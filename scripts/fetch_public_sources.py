#!/usr/bin/env python3
"""Refresh selected public-source bodies and inventory without deleting other rows."""
from __future__ import annotations

import csv
import argparse
import html
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/public_sources"
INVENTORY = ROOT / "data/source_inventory.csv"
RAW = ROOT / "data/raw"
# id, URL, coverage, license, extension, fields/content actually represented
SOURCES = [
    ("kerala_datahub_datasets", "https://datahub.kerala.gov.in/datasets", "Kerala Government data catalogue; no crossing-level counts established.", "Portal states reuse is free with accurate reproduction and prominent attribution to Kerala Data Portal, Government of Kerala.", "html", "Portal FAQ and dataset catalogue listings."),
    ("kerala_datahub_transport", "https://datahub.kerala.gov.in/sector/transport", "Transport-sector catalogue; no site-specific crossing evidence established.", "Kerala Data Portal terms as stated on catalogue.", "html", "Transport pages and linked chart/data summaries; source department where labeled."),
    ("kerala_datahub_datasets_page12", "https://datahub.kerala.gov.in/datasets?page=12", "Kerala Data Portal page containing district-wise PWD road-length and motor-vehicle chart data; both are district-level aggregates, not crossing measures.", "Kerala Data Portal terms: accurate reproduction and prominent attribution.", "html", "Embedded chart JSON and dataset labels; source names shown on portal."),
    ("india_ogd_kerala", "https://kerala.data.gov.in/", "India OGD state landing page; dataset resources may be owned by respective departments.", "Government Open Data License - India applies to published datasets/resources and metadata; verify individual resource.", "html", "Portal landing page, not individual datasets."),
    ("india_ogd_home", "https://www.data.gov.in/", "National OGD catalogue landing page; not evidence of a local crossing measurement.", "Government Open Data License - India for published datasets/resources and metadata; verify individual resource.", "html", "Portal landing page, not individual datasets."),
    ("iiitk_official", "https://iiitkottayam.ac.in/", "Official institute website for institutional identity/location context only.", "Not identified from fetched page; consult site terms before reuse.", "html", "Official institute landing page."),
    ("natpac_technical_reports", "https://natpac.kerala.gov.in/technical-reports/", "NATPAC list of submitted reports including Road Safety Policy, Road Safety Action Plan, Kerala road-safety factors/solutions, and crash-reduction strategy. Page lists reports but does not provide them.", "No page-specific reuse license identified; request report from NATPAC for substantive reuse.", "html", "Visible report titles; no report PDFs linked on page."),
    ("natpac_traffic_safety", "https://natpac.kerala.gov.in/traffic-engineering-safety-division/", "NATPAC describes road-safety auditing, road-user studies, crash database analysis, blackspot identification, vulnerable-road-user research and outreach. Stated work is statewide, not IIIT Kottayam crossing observations.", "No page-specific reuse license identified.", "html", "Division remit and stated activities; contextual only."),
    ("natpac_road_safety_materials", "https://natpac.kerala.gov.in/road-safety-materials-2/", "NATPAC road-safety materials catalogue linking educational PDFs.", "No page-specific reuse license identified; PDFs may be copyrighted.", "html", "Links to road-safety materials; no field measurements."),
    ("natpac_pedestrian_safety_booklets", "https://natpac.kerala.gov.in/wp-content/uploads/2023/08/Booklets-1.pdf", "Downloaded two-page list includes titles Pedestrian Safety Guide, Safe Cycling, Safe Road to School, and Safe Community Programme for Panchayats; it is a catalogue, not the full guide or local evidence.", "Copyright/license not stated in downloaded PDF; check with NATPAC before redistribution.", "pdf", "Booklet titles, including pedestrian-safety resources."),
    ("natpac_draft_road_safety_vision", "https://natpac.kerala.gov.in/wp-content/uploads/2023/08/Draft-Road-Safety-Vision.pdf", "NATPAC Draft Road Safety Vision—Kerala PDF, 68 physical pages containing a substantive 34-page report repeated twice. Historical statewide road-safety policy/context; stats span 1960–2013. Not site-level IIIT Kottayam evidence.", "Copyright/license not stated in downloaded PDF; cite and check with NATPAC before redistribution.", "pdf", "68 physical pages / repeated 34-page text. Printed p.12 pedestrian safety (sidewalks, zebra crossings, guardrails, beacons, grade-separated crossings); p.13 street lighting, visibility, traffic signals, road markings/signs. Historical aggregate statistics and policy recommendations; no Kottayam measurements."),
    ("peer_reviewed_india_midblock_ttc", "https://www.currentscience.ac.in/Volumes/123/09/1117.pdf", "Peer-reviewed Current Science research article (2022) reports videographic observations at four urban midblock sites in Surat, Vadodara, Ahmedabad, and Jaipur, India. Not IIIT Kottayam or its crossings.", "No explicit license identified in the article; cite bibliographically and check publisher terms before redistribution.", "pdf", "12-page article; method and reported aggregate study results only, not reusable Kottayam measurements."),
    ("peer_reviewed_iatssr_midblock_attempt", "https://www.sciencedirect.com/science/article/pii/S0386111220300522/pdf", "Attempted open-access publisher PDF for the 2020 India midblock-crosswalk mixed-traffic paper by Chaudhari et al.; publisher request returned HTTP 403 in this environment.", "Not verified from the downloaded publisher body; no body received.", "pdf", "No article fields extracted; failed download attempt only."),
]


def cached_record(key: str, url: str, coverage: str, license_note: str, extension: str, fields_description: str) -> dict:
    path = OUT / f"{key}.{extension}"
    row = dict(source_id=key, url=url, retrieved_utc="", status="cached", final_url=url, content_type="", coverage=coverage, fields=fields_description, intended_use="Context/discovery only; aggregate statistics are not crossing scores and no site observations should be fabricated.", license=license_note, body_file=f"data/raw/public_sources/{path.name}", sha256="", failure="")
    if INVENTORY.exists():
        with INVENTORY.open(newline="", encoding="utf-8") as stream:
            prior = next((item for item in csv.DictReader(stream) if item.get("source_id") == key), None)
        if prior:
            # Keep original retrieval/status provenance; cached mode only
            # recomputes local checksums and the declared coverage fields.
            row.update({column: prior[column] for column in ("retrieved_utc", "status", "final_url", "content_type", "body_file", "sha256", "failure") if column in prior})
    if path.exists():
        body = path.read_bytes()
        row["sha256"] = hashlib.sha256(body).hexdigest()
        if extension == "pdf" and (not body.startswith(b"%PDF-") or "application/pdf" not in row.get("content_type", "").lower()):
            row.update(status="download_not_pdf", failure="Cached PDF requires both %PDF- magic bytes and application/pdf content-type; verification failed.")
    elif not row.get("failure"):
        row.update(status="missing cached body", body_file="", failure=f"Expected cached file: {path.relative_to(ROOT)}")
    return row


def osm_rows() -> list[dict]:
    metadata_path = RAW / "osm_metadata.json"
    snapshot_path = RAW / "osm_context.json"
    nominatim_path = RAW / "osm_campus_nominatim.json"
    if not all(path.exists() for path in (metadata_path, snapshot_path, nominatim_path)):
        return []
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    nominatim = json.loads(nominatim_path.read_text(encoding="utf-8"))
    campus = metadata.get("campus_center", {})
    elements = snapshot.get("elements", [])
    type_counts: dict[str, int] = {}
    tag_counts: dict[str, int] = {}
    geometry_vertices = node_refs = 0
    for element in elements:
        kind = element.get("type", "unknown")
        type_counts[kind] = type_counts.get(kind, 0) + 1
        tags = element.get("tags", {})
        for key in tags:
            tag_counts[key] = tag_counts.get(key, 0) + 1
        geometry_vertices += len(element.get("geometry", []))
        node_refs += len(element.get("nodes", []))
    bbox = metadata.get("snapshot_bbox_south_west_north_east", metadata.get("bbox_south_west_north_east"))
    archived = metadata.get("archived_and_verified_at_utc", "")
    retrieved_at = metadata.get("retrieved_at_utc")
    retrieved = retrieved_at[:10] if retrieved_at else archived[:10]  # Clearly label archival date below when HTTP time is unknown.
    extract_note = metadata.get("snapshot_query_limitation") or metadata.get("bbox_basis") or "No additional extract-coverage note recorded."
    source_url = metadata.get("source_url", "https://overpass-api.de/api/interpreter")
    common = dict(retrieved_utc=retrieved, status="archived snapshot", content_type="application/json", intended_use="OSM geometry and nearby mapped-feature locations supply numeric geographic inputs to explicitly labeled synthetic score proxies in scripts/build_synthetic_dataset.py. They are not measured pedestrian demand, vehicle exposure, accessibility/control ratings, or field conditions; validate all candidate crossings in the field.", license=metadata.get("license", "OpenStreetMap contributors, ODbL 1.0"), failure="")
    overpass_body = snapshot_path.read_bytes()
    overpass_row = dict(source_id="osm_overpass_campus_context", url=source_url, final_url=source_url, coverage=f"Campus-centered extract; bbox south,west,north,east={bbox}; not district-wide. Snapshot query file={metadata.get('query_file')}; separately requested refresh query={metadata.get('refresh_requested_query_file')}. Extract note from metadata: {extract_note} Original HTTP request-completion time was not captured; retrieved_utc uses archive verification date {archived}. OSM base timestamp {snapshot.get('osm3s', {}).get('timestamp_osm_base', metadata.get('osm_timestamp_osm_base', 'unknown'))}.", fields=f"{len(elements)} OSM elements: {type_counts}; {geometry_vertices} inline geometry vertices; {node_refs} way node references; tagged keys include {', '.join(sorted(tag_counts))}. Raw per-element OSM element IDs, tags, geometry, and way node refs remain in osm_context.json.", body_file="data/raw/osm_context.json", sha256=hashlib.sha256(overpass_body).hexdigest(), **common)
    geo_url = campus.get("source_url", "https://nominatim.openstreetmap.org/search?q=Indian+Institute+of+Information+Technology+Kottayam&format=jsonv2&limit=5")
    nom_body = nominatim_path.read_bytes()
    nom_row = dict(source_id="osm_nominatim_iiit_kottayam", url=geo_url, final_url=geo_url, retrieved_utc=retrieved, coverage=f"Named campus place only, near the center of the campus-centered extract; Nominatim campus bbox south,north,west,east={campus.get('campus_bbox_south_north_west_east')}. HTTP completion time not captured; retrieved_utc uses archive verification date {archived}. Not district coverage.", fields=f"Campus name={campus.get('name')}; OSM {campus.get('osm_type')}/{campus.get('osm_id')}; latitude={campus.get('latitude')}; longitude={campus.get('longitude')}; campus bounding box={campus.get('campus_bbox_south_north_west_east')}; evidence includes raw Nominatim place_id/category/type/importance/display_name and bbox.", body_file="data/raw/osm_campus_nominatim.json", sha256=hashlib.sha256(nom_body).hexdigest(), **{key: value for key, value in common.items() if key != "retrieved_utc"})
    return [overpass_row, nom_row]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cached", action="store_true", help="Do not make network requests; rebuild inventory from saved source bodies and current OSM metadata/snapshot.")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    fetched = []
    for key, url, coverage, license_note, extension, fields_description in SOURCES:
        if args.cached:
            fetched.append(cached_record(key, url, coverage, license_note, extension, fields_description))
            continue
        row = dict(source_id=key, url=url, retrieved_utc=datetime.now(timezone.utc).date().isoformat(), status="", final_url="", content_type="", coverage=coverage, fields=fields_description, intended_use="Context/discovery only; aggregate statistics are not crossing scores and no site observations should be fabricated.", license=license_note, body_file="", sha256="", failure="")
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/130.0 Safari/537.36", "Referer": "https://natpac.kerala.gov.in/"})
            with urlopen(req, timeout=30) as response:
                body = response.read()
                row.update(status=str(response.status), final_url=response.geturl(), content_type=response.headers.get("Content-Type", ""))
            if extension == "pdf" and (not body.startswith(b"%PDF-") or "application/pdf" not in row["content_type"].lower()):
                actual_extension = "html" if body.lstrip().lower().startswith((b"<!doctype html", b"<html")) or "html" in row["content_type"].lower() else "bin"
                filename = f"{key}.{actual_extension}"
                (OUT / filename).write_bytes(body)
                row.update(status="download_not_pdf", body_file=f"data/raw/public_sources/{filename}", sha256=hashlib.sha256(body).hexdigest(), failure=f"Expected PDF; response content-type={row['content_type']!r}, magic={body[:8]!r}.")
                fetched.append(row)
                time.sleep(0.3)
                continue
            filename = f"{key}.{extension}"
            (OUT / filename).write_bytes(body)
            row.update(body_file=f"data/raw/public_sources/{filename}", sha256=hashlib.sha256(body).hexdigest())
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            row.update(status=getattr(exc, "code", "error"), failure=f"{type(exc).__name__}: {exc}")
        fetched.append(row)
        time.sleep(0.3)

    # The Kerala catalogue exposes these chart exports client-side in its page
    # JSON (rather than as linked CSV URLs). Preserve a simple CSV rendering of
    # those exact labels/values so the resource is inspectable offline.
    page = OUT / "kerala_datahub_datasets_page12.html"
    if page.exists():
        page_text = page.read_text(encoding="utf-8", errors="replace")
        for chart_id, slug, title, source in [
            ("863", "districtwise_road_length", "District-wise surface-wise and category-wise length of roads maintained by PWD", "PWD (Roads)"),
            ("864", "districtwise_motor_vehicle_growth", "Districtwise growth of motor vehicles in Kerala", "Motor Vehicles Department"),
        ]:
            match = re.search(r'<div id="dataset-chart-' + chart_id + r'".*?data-chart="(.*?)"', page_text, re.S)
            if not match:
                continue
            chart = json.loads(html.unescape(match.group(1)))
            chart_data = chart["chartData"]
            csv_path = OUT / f"{slug}.csv"
            with csv_path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.writer(stream)
                writer.writerow(["district"] + [series["label"] for series in chart_data["datasets"]])
                for index, district in enumerate(chart_data["labels"]):
                    writer.writerow([district] + [series["data"][index] for series in chart_data["datasets"]])
            source_page = next((row for row in fetched if row["source_id"] == "kerala_datahub_datasets_page12"), {})
            fetched.append(dict(source_id=slug, url=f"https://datahub.kerala.gov.in/datasets?page=12#dataset-chart-{chart_id}", retrieved_utc=source_page.get("retrieved_utc", ""), status="200 (embedded chart JSON)", final_url=f"https://datahub.kerala.gov.in/datasets?page=12#dataset-chart-{chart_id}", content_type="text/csv; charset=utf-8", coverage=f"{title}; 14 Kerala districts. District aggregate only, not site/crossing data.", fields=f"District; {', '.join(series['label'] for series in chart_data['datasets'])}. Portal source label: {source}.", intended_use="Contextual district comparison only; not a proxy or score input for crossing demand, exposure, or deficiencies.", license="Kerala Data Portal states accurate reproduction and prominent attribution; source department noted above.", body_file=f"data/raw/public_sources/{csv_path.name}", sha256=hashlib.sha256(csv_path.read_bytes()).hexdigest(), failure=""))

    # Hash current OSM artifacts on every inventory build, without modifying them.
    fetched.extend(osm_rows())

    # Preserve independent additions (e.g., OSM-worker rows) across refreshes.
    previous = []
    if INVENTORY.exists():
        with INVENTORY.open(newline="", encoding="utf-8") as stream:
            previous = list(csv.DictReader(stream))
    ids = {row["source_id"] for row in fetched}
    rows = fetched + [row for row in previous if row.get("source_id") not in ids]
    columns = list(fetched[0])
    with INVENTORY.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"inventory": str(INVENTORY), "sources": len(rows), "managed_rows": len(fetched), "mode": "cached" if args.cached else "fetch", "failures": sum(bool(row["failure"]) for row in fetched)}, indent=2))


if __name__ == "__main__":
    main()
