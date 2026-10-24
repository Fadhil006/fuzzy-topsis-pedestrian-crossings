"""Evidence-linkage and reproducibility checks, not empirical validation."""
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
from build_synthetic_dataset import CRITERIA, distance, make_rows, parse_context, write_dataset
from model import fuzzy_topsis, intervalize
from run_project import load_and_validate, triangles_from_frame


class DatasetGenerationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = json.loads((ROOT / "data/raw/osm_context.json").read_text())
        metadata = json.loads((ROOT / "data/raw/osm_metadata.json").read_text())
        center = metadata["campus_center"]
        cls.center = [center["latitude"], center["longitude"]]
        cls.bbox = metadata["bbox_south_west_north_east"]

    def test_raw_geometry_candidate_membership_and_bounds(self):
        rows = make_rows(self.raw, self.center, bbox=self.bbox)
        nodes, roads, _ = parse_context(self.raw)
        self.assertGreaterEqual(len(rows), 2)
        self.assertLessEqual(len(rows), 28)
        self.assertEqual(len(rows), len({r["alternative_id"] for r in rows}))
        self.assertEqual(len(rows), len({r["crossing_id"] for r in rows}))
        for i, row in enumerate(rows):
            node_id = row["osm_node_id"]
            point = (row["latitude"], row["longitude"])
            self.assertLess(distance(point, nodes[node_id]["point"]), .05)
            self.assertLessEqual(distance(point, self.center), 3000.1)
            for road_id in json.loads(row["osm_road_ids"]):
                self.assertIn(node_id, roads[road_id]["nodes"])
            for other in rows[:i]:
                self.assertGreaterEqual(distance(point, (other["latitude"], other["longitude"])), 79.9)
            self.assertEqual(row["data_status"], "public_source_informed_synthetic")
            self.assertEqual(row["engineering_feasibility"], "unknown_not_screened")
            for short, long_name in CRITERIA.items():
                self.assertIsInstance(row[long_name], int)
                self.assertTrue(1 <= row[f"{short}_low"] <= row[long_name] <= row[f"{short}_high"] <= 5)

    def test_identical_snapshot_seed_reproduces_committed_csv(self):
        rows = make_rows(self.raw, self.center, bbox=self.bbox)
        with tempfile.TemporaryDirectory() as tmp:
            path = write_dataset(rows, Path(tmp))
            expected = ROOT / "data/processed/pedestrian_crossings_fuzzy_topsis.csv"
            self.assertEqual(hashlib.sha256(path.read_bytes()).digest(),
                             hashlib.sha256(expected.read_bytes()).digest())
            other = write_dataset(make_rows(self.raw, self.center, seed=123, bbox=self.bbox), Path(tmp))
            self.assertNotEqual(hashlib.sha256(other.read_bytes()).digest(),
                                hashlib.sha256(expected.read_bytes()).digest())
        observed = pd.read_csv(ROOT / "data/processed/pedestrian_crossings_observed.csv")
        self.assertEqual(len(observed), 0)

    def test_full_dataset_loads_and_all_five_criterion_scores_reconstruct(self):
        _, data = load_and_validate(ROOT / "data/processed/pedestrian_crossings_fuzzy_topsis.csv", synthetic=True)
        self.assertFalse(data.isna().any().any())
        self.assertTrue(all(data[c].nunique() >= 2 for c in CRITERIA.values()))
        score, plus, minus = fuzzy_topsis(intervalize(triangles_from_frame(data, tuple(CRITERIA))), np.ones(5))
        self.assertTrue(np.isfinite(score).all())
        self.assertTrue(((score >= 0) & (score <= 1)).all())
        np.testing.assert_allclose(score, minus / (plus + minus))

    def test_missing_osm_tags_do_not_imply_accessibility_absence(self):
        rows = make_rows(self.raw, self.center, bbox=self.bbox)
        assumed = [r for r in rows if json.loads(r["confidence"])["access"] == "very_low_assumption"]
        self.assertTrue(assumed)
        for row in assumed:
            self.assertIn("tags unknown, not absent", json.loads(row["score_provenance"])["access"][0])
            self.assertEqual(max(1, row["access_mid"] - 1.5), row["access_low"])

    def test_existing_field_cli_with_synthetic_field_shaped_fixture(self):
        # Exercise old input mode only in a temporary directory. These fixture
        # values remain hypothetical and are never exported as real observations.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "field_mode_fixture"
            subprocess.run([sys.executable, str(ROOT / "src/run_project.py"),
                            "--input", str(ROOT / "data/hypothetical_demo.csv"),
                            "--output-dir", str(out), "--draws", "2"],
                           check=True, capture_output=True, text=True)
            manifest = json.loads((out / "field_run_manifest.json").read_text())
            self.assertEqual(manifest["evidence_status"], "user_supplied_unverified_field_data")
            self.assertTrue((out / "field_base_ranking.csv").exists())
            self.assertFalse((out / "fuzzy_topsis_results.csv").exists())

    def test_explicit_mapped_absence_and_legacy_zebra_tag_are_not_ignored(self):
        crossing = next(r for r in make_rows(self.raw, self.center, bbox=self.bbox)
                        if r["candidate_basis"] == "mapped_crossing_unverified")
        provenance = json.loads(crossing["score_provenance"])
        self.assertIn("mapped tactile_paving=no; unverified", provenance["access"])
        self.assertIn("mapped crossing markings; condition unknown", provenance["deficiency"])
        self.assertEqual(json.loads(crossing["confidence"])["access"], "low_mapped_proxy")


if __name__ == "__main__":
    unittest.main()
