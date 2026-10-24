"""Offline tests of source preservation on failed or incomplete downloads."""
import importlib.util
import csv
import hashlib
import html
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fetch_osm", ROOT / "scripts/fetch_osm_context.py")
fetch_osm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetch_osm)


class SourcePreservationChecks(unittest.TestCase):
    def test_preserved_inventory_checksums_and_pdf_content(self):
        with (ROOT / "data/source_inventory.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), len({row["source_id"] for row in rows}))
        for row in rows:
            self.assertTrue(row["url"] and row["coverage"] and row["fields"] and row["retrieved_utc"])
            if not row["body_file"]:
                self.assertTrue(row["failure"])
                continue
            body = (ROOT / row["body_file"]).read_bytes()
            self.assertEqual(hashlib.sha256(body).hexdigest(), row["sha256"], row["source_id"])
            if row["body_file"].endswith(".pdf"):
                self.assertTrue(body.startswith(b"%PDF-"))
                self.assertIn("application/pdf", row["content_type"])

    def test_extracted_district_csvs_match_actual_embedded_chart_values(self):
        raw = ROOT / "data/raw/public_sources"
        page = (raw / "kerala_datahub_datasets_page12.html").read_text()
        for chart_id, filename in [("863", "districtwise_road_length.csv"),
                                   ("864", "districtwise_motor_vehicle_growth.csv")]:
            match = re.search(r'<div id="dataset-chart-' + chart_id + r'".*?data-chart="(.*?)"', page, re.S)
            self.assertIsNotNone(match)
            data = json.loads(html.unescape(match.group(1)))["chartData"]
            with (raw / filename).open(newline="", encoding="utf-8") as stream:
                rows = list(csv.reader(stream))
            expected = [["district"] + [series["label"] for series in data["datasets"]]]
            for i, district in enumerate(data["labels"]):
                expected.append([district] + [str(series["data"][i]) for series in data["datasets"]])
            self.assertEqual(rows, expected)

    def test_failed_refresh_preserves_success_and_records_actual_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp)
            output, metadata = raw / "osm_context.json", raw / "osm_metadata.json"
            query, failures = raw / "osm_query.overpassql", raw / "osm_fetch_failures.json"
            output.write_text('{"elements":[{"type":"node","id":123}]}')
            metadata.write_text('{"successful_snapshot":"retained"}')
            query.write_text('[out:json];node(123);out;')
            old = output.read_bytes(), metadata.read_bytes()
            with patch.multiple(fetch_osm, RAW=raw, OUTPUT=output, METADATA=metadata,
                                QUERY=query, FAILURES=failures, ENDPOINTS=["https://example.invalid/api"]), \
                 patch.object(sys, "argv", ["fetch_osm_context.py", "--refresh"]), \
                 patch.object(fetch_osm.urllib.request, "urlopen", side_effect=URLError("offline test")):
                self.assertEqual(fetch_osm.main(), 1)
            self.assertEqual((output.read_bytes(), metadata.read_bytes()), old)
            recorded = json.loads(failures.read_text())
            self.assertEqual(recorded["attempted_source_urls"], ["https://example.invalid/api"])
            self.assertIn("offline test", recorded["failures"][0]["error"])

    def test_incomplete_http_success_cannot_replace_snapshot(self):
        from unittest.mock import MagicMock
        with tempfile.TemporaryDirectory() as tmp:
            raw = Path(tmp)
            output, metadata = raw / "osm_context.json", raw / "osm_metadata.json"
            query, failures = raw / "osm_query.overpassql", raw / "osm_fetch_failures.json"
            output.write_text("cached valid snapshot")
            metadata.write_text("cached success metadata")
            query.write_text("query")
            response = MagicMock()
            response.__enter__.return_value.read.return_value = b'{"elements":[],"remark":"runtime timeout"}'
            with patch.multiple(fetch_osm, RAW=raw, OUTPUT=output, METADATA=metadata,
                                QUERY=query, FAILURES=failures, ENDPOINTS=["https://example.invalid/api"]), \
                 patch.object(sys, "argv", ["fetch_osm_context.py", "--refresh"]), \
                 patch.object(fetch_osm.urllib.request, "urlopen", return_value=response):
                self.assertEqual(fetch_osm.main(), 1)
            self.assertEqual(output.read_text(), "cached valid snapshot")
            self.assertEqual(metadata.read_text(), "cached success metadata")


if __name__ == "__main__":
    unittest.main()
