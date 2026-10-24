#!/usr/bin/env python3
"""Fetch/cache public OSM context for IIIT Kottayam (standard library only).

Run from the repository root. Existing raw response is preserved unless --refresh
is supplied. Query and provenance are stored alongside the response.
"""
import argparse
import datetime as dt
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
QUERY = RAW / "osm_query.overpassql"
OUTPUT = RAW / "osm_context.json"
METADATA = RAW / "osm_metadata.json"
FAILURES = RAW / "osm_fetch_failures.json"
ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def campus_metadata():
    evidence_path = RAW / "osm_campus_nominatim.json"
    places = json.loads(evidence_path.read_text(encoding="utf-8"))
    place = next(
        item for item in places
        if item.get("osm_type") == "way" and item.get("osm_id") == 1077351803
    )
    south, north, west, east = map(float, place["boundingbox"])
    return {
        "latitude": float(place["lat"]),
        "longitude": float(place["lon"]),
        "osm_type": place["osm_type"],
        "osm_id": place["osm_id"],
        "name": place["name"],
        "source_url": "https://nominatim.openstreetmap.org/search?q=Indian+Institute+of+Information+Technology+Kottayam&format=jsonv2&limit=5",
        "evidence_file": evidence_path.name,
        "campus_bbox_south_north_west_east": [south, north, west, east],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="fetch again rather than using cached raw response")
    args = parser.parse_args()
    RAW.mkdir(parents=True, exist_ok=True)
    if OUTPUT.exists() and not args.refresh:
        print(f"Using cached response: {OUTPUT}")
        return 0
    query = QUERY.read_text(encoding="utf-8")
    failures = []
    attempted_urls = []
    for endpoint in ENDPOINTS:
        attempted_urls.append(endpoint)
        started = utcnow()
        request = urllib.request.Request(
            endpoint,
            data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
            headers={"User-Agent": "fuzzy-topsis-research/1.0 (public OSM context; contact via project repository)",
                     "Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            with urllib.request.urlopen(request, timeout=150) as response:
                body = response.read()
                payload = json.loads(body)
                if not isinstance(payload.get("elements"), list) or not payload["elements"] or payload.get("remark"):
                    raise ValueError("Overpass response is empty or incomplete")
                completed = utcnow()
                metadata = {
                    "retrieved_at_utc": completed,
                    "source_url": endpoint,
                    "attempted_source_urls": attempted_urls,
                    "failures_before_success": failures,
                    "query_file": QUERY.name,
                    "response_file": OUTPUT.name,
                    "bbox_south_west_north_east": [9.7229, 76.6170, 9.7880, 76.6820],
                    "bbox_basis": "approximately 3.6 km campus-centered rectangular extraction buffer; candidate radius remains a separate 3 km generator filter",
                    "campus_evidence_file": "osm_campus_nominatim.json",
                    "campus_center": campus_metadata(),
                    "license": "OpenStreetMap contributors, ODbL 1.0",
                    "osm_timestamp_osm_base": payload.get("osm3s", {}).get("timestamp_osm_base"),
                    "element_count": len(payload["elements"]),
                }
                # Resolve dependent evidence before replacing a valid snapshot.
                temp_output = OUTPUT.with_suffix(OUTPUT.suffix + ".tmp")
                temp_output.write_bytes(body)
                temp_output.replace(OUTPUT)
                snapshot_query = RAW / "osm_snapshot_query.overpassql"
                snapshot_query.write_text(query, encoding="utf-8")
                metadata["query_file"] = snapshot_query.name
                METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
                if failures:
                    FAILURES.write_text(json.dumps({"failures": failures}, indent=2) + "\n", encoding="utf-8")
                print(f"Saved {len(payload['elements'])} elements to {OUTPUT}")
                return 0
        except (OSError, urllib.error.URLError, urllib.error.HTTPError, ValueError, json.JSONDecodeError) as exc:
            failures.append({"url": endpoint, "attempted_at_utc": started, "error": str(exc)})
            print(f"Overpass failure {endpoint}: {exc}", file=sys.stderr)
    FAILURES.write_text(json.dumps({
        "recorded_at_utc": utcnow(),
        "attempted_source_urls": attempted_urls,
        "failures": failures,
    }, indent=2) + "\n", encoding="utf-8")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
