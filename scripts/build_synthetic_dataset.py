"""Build explicitly synthetic ordinal inputs from a preserved OSM extract.

No network access is needed. This does not estimate measured counts or certify
crossings, conditions, engineering feasibility, or walking routes.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 20261024
CRITERIA = {
    "ped": "pedestrian_demand", "vehicle": "vehicle_exposure",
    "access": "accessibility_deficiency", "deficiency": "control_visibility_deficiency",
    "destination": "essential_destination_access",
}
ROAD_BASE = {"motorway": 5, "trunk": 5, "primary": 5, "secondary": 4,
             "tertiary": 3, "unclassified": 2, "residential": 2,
             "living_street": 1, "service": 1}


def distance(a, b):
    """Great-circle distance in metres; proximity is NOT walk-network access."""
    p, q = math.radians(a[0]), math.radians(b[0])
    dp, dl = q - p, math.radians(b[1] - a[1])
    z = math.sin(dp / 2) ** 2 + math.cos(p) * math.cos(q) * math.sin(dl / 2) ** 2
    return 6371008.8 * 2 * math.asin(min(1, math.sqrt(z)))


def feature_point(element):
    if "lat" in element and "lon" in element:
        return element["lat"], element["lon"]
    center = element.get("center")
    if center:
        return center["lat"], center["lon"]
    geom = element.get("geometry", [])
    if geom:
        return (sum(p["lat"] for p in geom) / len(geom),
                sum(p["lon"] for p in geom) / len(geom))
    return None


def destination_weight(tags):
    amenity = tags.get("amenity", "")
    if amenity in {"hospital", "clinic", "school", "kindergarten"}:
        return 3.0
    if amenity in {"college", "university", "pharmacy", "bus_station", "marketplace"}:
        return 2.5
    if (tags.get("highway") == "bus_stop" or tags.get("public_transport") in
            {"platform", "stop_position"}):
        return 2.0
    if amenity in {"bank", "post_office", "community_centre", "place_of_worship"}:
        return 1.5
    if tags.get("shop") or amenity in {"restaurant", "cafe"}:
        return 1.0
    return 0.0


def parse_context(raw):
    nodes, roads, destinations = {}, {}, []
    for element in raw["elements"]:
        point = feature_point(element)
        tags = element.get("tags", {})
        if element["type"] == "node" and point:
            nodes[element["id"]] = {"point": point, "tags": tags}
        highway = tags.get("highway", "").removesuffix("_link")
        if element["type"] == "way" and highway in ROAD_BASE:
            roads[element["id"]] = element
            for node_id, pos in zip(element.get("nodes", []), element.get("geometry", [])):
                nodes.setdefault(node_id, {"point": (pos["lat"], pos["lon"]), "tags": {}})
        weight = destination_weight(tags)
        if point and weight:
            destinations.append({"id": f'{element["type"]}/{element["id"]}',
                                 "point": point, "weight": weight, "tags": tags})
    # Avoid counting a tagged POI node AND a same-named area as two destinations.
    unique = []
    for dest in sorted(destinations, key=lambda d: d["id"]):
        name = dest["tags"].get("name")
        if name and any(p["tags"].get("name") == name and
                        distance(p["point"], dest["point"]) < 100 for p in unique):
            continue
        unique.append(dest)
    return nodes, roads, unique


def candidates(nodes, roads, destinations, center, radius=3000, target=28):
    neighbors, memberships = defaultdict(set), defaultdict(set)
    for road_id, road in roads.items():
        ids = road.get("nodes", [])
        for left, right in zip(ids, ids[1:]):
            neighbors[left].add(right)
            neighbors[right].add(left)
            memberships[left].add(road_id)
            memberships[right].add(road_id)
    selected = {}
    for node_id in memberships:
        node = nodes.get(node_id)
        if not node or distance(center, node["point"]) > radius:
            continue
        mapped_crossing = node["tags"].get("highway") == "crossing" or "crossing" in node["tags"]
        if mapped_crossing or len(neighbors[node_id]) >= 3:
            selected[node_id] = "mapped_crossing_unverified" if mapped_crossing else "mapped_road_junction_candidate"
    # Near-destination road nodes are candidate access locations, not inferred crossings.
    # Keep only the nearest road node <=100m from a mapped essential destination.
    for dest in destinations:
        nearby = [(distance(dest["point"], nodes[n]["point"]), n) for n in memberships
                  if n in nodes and distance(center, nodes[n]["point"]) <= radius]
        if nearby:
            dist, node_id = min(nearby)
            if dist <= 100:
                selected.setdefault(node_id, "mapped_destination_near_road_candidate")
    # Favor stronger location evidence, then proximity to campus; never make up nodes.
    order = {"mapped_crossing_unverified": 0, "mapped_road_junction_candidate": 1,
             "mapped_destination_near_road_candidate": 2}
    ordered = sorted(selected, key=lambda n: (order[selected[n]], distance(center, nodes[n]["point"]), n))
    chosen = []
    for n in ordered:
        if all(distance(nodes[n]["point"], nodes[other]["point"]) >= 80 for other in chosen):
            chosen.append(n)
        if len(chosen) == target:
            break
    return [(n, selected[n], sorted(memberships[n])) for n in chosen]


def ordinal(value):
    return min(5, max(1, int(math.floor(value + .5))))


def make_rows(raw, center, radius=3000, target=28, seed=SEED, bbox=None):
    nodes, roads, destinations = parse_context(raw)
    chosen = candidates(nodes, roads, destinations, center, radius, target)
    rows = []
    for node_id, kind, road_ids in chosen:
        node = nodes[node_id]
        tags = node["tags"]
        rng = random.Random(f"{seed}:{node_id}")
        road = max((roads[i] for i in road_ids),
                   key=lambda r: (ROAD_BASE[r["tags"]["highway"].removesuffix("_link")], -r["id"]))
        road_tags = road["tags"]
        highway = road_tags["highway"].removesuffix("_link")
        nearby = [(distance(node["point"], d["point"]), d) for d in destinations
                  if distance(node["point"], d["point"]) <= 500]
        intensity = sum(d["weight"] * (1 - dist / 600) for dist, d in nearby)
        bus_near = any((d["tags"].get("highway") == "bus_stop" or
                        d["tags"].get("public_transport") in {"platform", "stop_position"})
                       and dist <= 250 for dist, d in nearby)
        strongest = max((d["weight"] * (1 - dist / 600) for dist, d in nearby), default=0)
        context_complete = False
        if bbox:
            lat, lon = node["point"]
            south, west, north, east = bbox
            margin = min(distance((lat, lon), (south, lon)), distance((lat, lon), (north, lon)),
                         distance((lat, lon), (lat, west)), distance((lat, lon), (lat, east)))
            context_complete = south <= lat <= north and west <= lon <= east and margin >= 500
        exposure_value = float(ROAD_BASE[highway])
        lanes = road_tags.get("lanes", "unknown")
        speed = road_tags.get("maxspeed", "unknown")
        if str(lanes).isdigit() and int(lanes) >= 3:
            exposure_value += .5
        if str(speed).isdigit() and int(speed) >= 60:
            exposure_value += .5
        vehicle = ordinal(exposure_value + rng.uniform(-.35, .35))
        destination = ordinal(1 + 1.05 * strongest + .25 * math.log1p(intensity))
        ped = ordinal(1 + 1.05 * math.log1p(intensity) + .35 * bus_near +
                      .12 * (vehicle - 2) + rng.uniform(-.65, .65))
        # Missing tags retain a neutral synthetic prior; they never mean absent.
        shared = rng.uniform(-.45, .45)
        access_value = 3 + shared + rng.gauss(0, .85)
        control_value = 3 + shared + .2 * (vehicle - 3) + rng.gauss(0, .85)
        access_evidence, control_evidence = [], []
        if tags.get("wheelchair") in {"yes", "designated"}:
            access_value -= 1.2
            access_evidence.append("mapped wheelchair=yes/designated; unverified")
        elif tags.get("wheelchair") == "no":
            access_value += 1.2
            access_evidence.append("mapped wheelchair=no; unverified")
        if tags.get("kerb") in {"flush", "lowered"} or tags.get("sloped_curb") == "yes":
            access_value -= .8
            access_evidence.append("mapped lowered/flush kerb or sloped_curb=yes; unverified")
        elif tags.get("kerb") == "raised":
            access_value += .8
            access_evidence.append("mapped raised kerb; unverified")
        if tags.get("tactile_paving") == "yes":
            access_value -= .4
            access_evidence.append("mapped tactile paving; unverified")
        elif tags.get("tactile_paving") == "no":
            access_value += .4
            access_evidence.append("mapped tactile_paving=no; unverified")
        if tags.get("highway") == "traffic_signals" or tags.get("crossing") == "traffic_signals":
            control_value -= 1.1
            control_evidence.append("mapped traffic signals; condition unknown")
        elif (tags.get("crossing") in {"marked", "zebra"} or
              tags.get("crossing:markings") in {"yes", "zebra"} or tags.get("crossing_ref") == "zebra"):
            control_value -= .7
            control_evidence.append("mapped crossing markings; condition unknown")
        if tags.get("lit", road_tags.get("lit")) == "yes":
            control_value -= .4
            control_evidence.append("mapped lighting; condition unknown")
        scores = {"ped": ped, "vehicle": vehicle, "access": ordinal(access_value),
                  "deficiency": ordinal(control_value), "destination": destination}
        confidence = {"ped": "low_context_proxy", "vehicle": "low_context_proxy",
                      "access": "low_mapped_proxy" if access_evidence else "very_low_assumption",
                      "deficiency": "low_mapped_proxy" if control_evidence else "very_low_assumption",
                      "destination": "low_proximity_proxy" if nearby else "very_low_mapping_incomplete"}
        if not context_complete:
            confidence["ped"] = "very_low_context_truncated_or_unknown"
            confidence["destination"] = "very_low_context_truncated_or_unknown"
        name = road_tags.get("name", road_tags.get("ref", f"unnamed {highway} road"))
        refs = [f"https://www.openstreetmap.org/node/{node_id}"] + [
            f"https://www.openstreetmap.org/way/{r}" for r in road_ids]
        row = {
            "alternative_id": f"SYN-OSM-{node_id}", "crossing_id": f"CAND-OSM-{node_id}",
            "location_description": f"Hypothetical candidate on {name}, OSM node {node_id}",
            "location_name": f"{name} — hypothetical candidate {node_id}",
            "latitude": round(node["point"][0], 7), "longitude": round(node["point"][1], 7),
            "intervention_type": "synthetic generic accessible crossing improvement package; feasibility unknown",
            "survey_date": "not_field_survey", "evidence_photo_ids": "NO_FIELD_PHOTOS",
            "feasibility_status": "eligible", "data_status": "public_source_informed_synthetic",
            "location_status": "hypothetical_candidate_not_verified_crossing", "candidate_basis": kind,
            "engineering_feasibility": "unknown_not_screened", "distance_to_campus_m": round(distance(center, node["point"])),
            "osm_node_id": node_id, "osm_road_ids": json.dumps(road_ids),
            "road_class": highway, "mapped_lanes": lanes, "mapped_maxspeed": speed,
            "mapped_node_tags": json.dumps(tags, sort_keys=True, ensure_ascii=False),
            "mapped_road_tags": json.dumps(road_tags, sort_keys=True, ensure_ascii=False),
            "destinations_within_500m": len(nearby), "destination_intensity_proxy": round(intensity, 5),
            "full_500m_query_buffer": context_complete,
            "nearby_destination_refs": json.dumps([d["id"] for _, d in sorted(nearby, key=lambda x: (x[0], x[1]["id"]))]),
            "source_refs": json.dumps(refs), "confidence": json.dumps(confidence, sort_keys=True),
            "score_provenance": json.dumps({
                "ped": "synthetic: mapped amenity intensity + bus proximity + mild exposure association + seeded variation",
                "vehicle": "synthetic: road hierarchy plus mapped lanes/maxspeed where present; no measured traffic",
                "access": access_evidence or ["neutral prior plus seeded variation; tags unknown, not absent"],
                "deficiency": control_evidence or ["neutral prior plus exposure-context assumption and seeded variation"],
                "destination": "synthetic: straight-line mapped amenity proximity, not audited walk-network access",
            }, ensure_ascii=False, sort_keys=True),
            "assumptions": "All scores and intervals synthetic; missing tags unknown; great-circle proximity not walking access; eligible means simulation inclusion only; ordinal steps treated as equal spacing",
            "notes": "Not a verified crossing or observed safety finding; no field survey, counts, speeds, photographs or feasibility review",
            "synthetic_seed": seed,
        }
        for short, long_name in CRITERIA.items():
            score = scores[short]
            row[long_name] = score
            # These are modelling widths, not probabilities/confidence intervals.
            width = 1.5 if confidence[short].startswith("very_low") else 1.0
            row[f"{short}_low"] = max(1.0, score - width)
            row[f"{short}_mid"] = score
            row[f"{short}_high"] = min(5.0, score + width)
        rows.append(row)
    return sorted(rows, key=lambda row: row["alternative_id"])


def write_dataset(rows, outdir):
    if len(rows) < 2:
        raise ValueError("Public extract supports fewer than two candidates; do not invent locations")
    outdir.mkdir(parents=True, exist_ok=True)
    path = outdir / "pedestrian_crossings_fuzzy_topsis.csv"
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    observed = outdir / "pedestrian_crossings_observed.csv"
    # Empty observation template must never be populated with estimates.
    if not observed.exists():
        with observed.open("w", newline="", encoding="utf-8") as stream:
            csv.writer(stream).writerow(["observation_id", "crossing_id", "latitude", "longitude",
                                        "observation_date", "criterion", "observed_value", "unit", "source_url"])
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--osm-input", type=Path, default=ROOT / "data/raw/osm_context.json")
    parser.add_argument("--metadata", type=Path, default=ROOT / "data/raw/osm_metadata.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--target", type=int, default=28)
    parser.add_argument("--radius-m", type=float, default=3000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    if args.target < 2 or not math.isfinite(args.radius_m) or args.radius_m <= 0:
        parser.error("target must be >=2 and radius must be finite and positive")
    metadata = json.loads(args.metadata.read_text())
    center = metadata["campus_center"]
    if isinstance(center, dict):
        center = [center["latitude"], center["longitude"]]
    if len(center) != 2 or not all(math.isfinite(v) for v in center):
        raise ValueError("Invalid campus center metadata")
    raw = json.loads(args.osm_input.read_text())
    rows = make_rows(raw, center, args.radius_m, args.target, args.seed,
                     bbox=metadata["bbox_south_west_north_east"])
    path = write_dataset(rows, args.output_dir)
    manifest = {"evidence_status": "public_source_informed_synthetic", "candidate_count": len(rows),
                "target_count": args.target, "seed": args.seed, "radius_m": args.radius_m,
                "campus_center": center, "input_sha256": hashlib.sha256(args.osm_input.read_bytes()).hexdigest(),
                "input_metadata_sha256": hashlib.sha256(args.metadata.read_bytes()).hexdigest(),
                "extract_bbox_south_west_north_east": metadata["bbox_south_west_north_east"],
                "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "actual_field_observations": 0, "selection": "mapped road junctions/crossings or nodes <=100m from mapped destinations; >=80m spacing"}
    (args.output_dir / "synthetic_generation_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {len(rows)} hypothetical candidates to {path}; actual observations: 0")
    if len(rows) < args.target:
        print("Fewer defensible candidates than requested; retained available evidence instead of inventing locations.")


if __name__ == "__main__":
    main()
