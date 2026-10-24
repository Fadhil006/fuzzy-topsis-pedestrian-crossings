"""Explicit synthetic-input validation and CLI export checks."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from run_project import load_and_validate


def synthetic_frame():
    frame = pd.read_csv(ROOT / "data/hypothetical_demo.csv")
    frame["survey_date"] = "not_field_survey"
    for col, value in {
        "latitude": 10.0, "longitude": 76.5,
        "data_status": "public_source_informed_synthetic",
        "location_status": "hypothetical_candidate_not_verified_crossing",
        "score_provenance": "assumed from public sources", "assumptions": "synthetic values",
        "confidence": "low", "source_refs": "public references",
    }.items():
        frame[col] = value
    for score, criterion in {
        "pedestrian_demand": "ped", "vehicle_exposure": "vehicle",
        "accessibility_deficiency": "access", "control_visibility_deficiency": "deficiency",
        "essential_destination_access": "destination",
    }.items():
        frame[score] = frame[f"{criterion}_mid"].round().astype(int).clip(1, 5)
        frame[f"{criterion}_mid"] = frame[score]
        frame[f"{criterion}_low"] = frame[f"{criterion}_mid"]
        frame[f"{criterion}_high"] = frame[f"{criterion}_mid"]
    return frame


class SyntheticPipelineChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "synthetic.csv"
        synthetic_frame().to_csv(self.path, index=False)

    def test_validation_rejects_bad_ranges_scores_coordinates_and_provenance(self):
        for change, message in [
            (lambda d: d.__setitem__("pedestrian_demand", 2.5), "integer"),
            (lambda d: d.__setitem__("access_low", 0), "1–5"),
            (lambda d: d.__setitem__("latitude", 91), "latitude"),
            (lambda d: d.__setitem__("score_provenance", ""), "provenance"),
            (lambda d: d.loc.__setitem__((0, "pedestrian_demand"), int(d.loc[0, "pedestrian_demand"]) % 5 + 1), "match ped_mid"),
        ]:
            data = synthetic_frame()
            change(data)
            data.to_csv(self.path, index=False)
            with self.assertRaisesRegex(ValueError, message):
                load_and_validate(self.path, synthetic=True)

    def test_cli_exports_five_criterion_labeled_ranking(self):
        output = Path(self.temp.name) / "run"
        subprocess.run([sys.executable, str(ROOT / "src/run_project.py"), "--synthetic-input",
                        str(self.path), "--output-dir", str(output), "--draws", "2"],
                       cwd=ROOT, check=True, capture_output=True, text=True)
        result = pd.read_csv(output / "fuzzy_topsis_results.csv")
        self.assertIn("closeness_coefficient", result)
        self.assertEqual(set(result.evidence_status), {"synthetic"})
        self.assertTrue((output / "synthetic_base_ranking.csv").exists())
        extension = pd.read_csv(output / "synthetic_extension_ranking.csv").set_index("alternative_id")
        np.testing.assert_allclose(result.set_index("alternative_id").loc[extension.index, "closeness_coefficient"], extension.score)
        manifest = json.loads((output / "synthetic_run_manifest.json").read_text())
        self.assertEqual(manifest["evidence_status"], "public_source_informed_synthetic")
        self.assertEqual(manifest["primary_model"], "five_criterion_extension")
        chart = (output / "synthetic_weight_sensitivity.svg").read_text()
        self.assertNotIn("Field observations", chart)

    def test_duplicates_missing_score_and_field_mode_are_rejected(self):
        mutations = [
            (lambda d: d.__setitem__("crossing_id", d.crossing_id.iloc[0]), "crossing_id"),
            (lambda d: d.__setitem__("alternative_id", d.alternative_id.iloc[0]), "alternative_id"),
            (lambda d: d.__setitem__("pedestrian_demand", float("nan")), "integer"),
        ]
        for mutation, message in mutations:
            data = synthetic_frame()
            mutation(data)
            data.to_csv(self.path, index=False)
            with self.assertRaisesRegex(ValueError, message):
                load_and_validate(self.path, synthetic=True)
        field = synthetic_frame()
        field["survey_date"] = "2026-01-01"
        field.to_csv(self.path, index=False)
        with self.assertRaisesRegex(ValueError, "--synthetic-input"):
            load_and_validate(self.path)
        field["data_status"] = "field_observation"
        field["access_high"] = 4
        field.to_csv(self.path, index=False)
        with self.assertRaisesRegex(ValueError, "0–3 scale"):
            load_and_validate(self.path)


if __name__ == "__main__":
    unittest.main()
