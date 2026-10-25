import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from evaluate_revised_report import DEFAULT_INPUT, _crisp_topsis, build_revised_evaluation
from evaluate_report import build_evaluation
from run_project import load_and_validate


class RevisedEvaluationTests(unittest.TestCase):
    def test_crisp_topsis_perfect_profile(self):
        scores, details = _crisp_topsis(np.array([[1., 0.], [0., 1.], [0., 0.]]))
        np.testing.assert_allclose(scores, [0.5, 0.5, 0.])
        np.testing.assert_allclose(details["distance_positive"], [0.5, 0.5, np.sqrt(0.5)])
        np.testing.assert_allclose(details["positiveideal"], [0.5, 0.5])

    def test_crisp_topsis_rejects_non_discriminating_and_invalid_input(self):
        with self.assertRaisesRegex(ValueError, "no criterion distinguishes"):
            _crisp_topsis(np.ones((3, 2)))
        with self.assertRaisesRegex(ValueError, "finite 2-D"):
            _crisp_topsis(np.array([[1., np.nan], [2., 3.]]))

    def test_actual_input_reproducibility_and_primary_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "revised"
            result = build_revised_evaluation(DEFAULT_INPUT, out, draws=4)
            expected_primary = build_evaluation(DEFAULT_INPUT, Path(tmp) / "expected", draws=4)
            self.assertEqual(result["primary"], expected_primary)
            self.assertEqual(result, json.loads((out / "summary.json").read_text()))
            self.assertEqual(len(result["additional_baselines"]["crisp_topsis"]), 28)
            self.assertEqual(len(result["additional_baselines"]["deficiency_rule"]), 28)
            self.assertEqual(len(result["worked_crisp"]["rawcentral"]), 5)
            self.assertEqual(len(pd.read_csv(out / "crisp_topsis.csv")), 28)
            self.assertEqual(len(result["additional_baselines"]["comparisons"]), 2)
            np.testing.assert_allclose(
                [row["score"] for row in result["primary"]["all_candidates"]],
                [row["score"] for row in expected_primary["all_candidates"]])
            _, frame = load_and_validate(DEFAULT_INPUT, synthetic=True)
            central = frame[["access_mid", "deficiency_mid"]].to_numpy(float)
            expected = np.column_stack([
                (central[:, j] - central[:, j].min()) / np.ptp(central[:, j])
                if np.ptp(central[:, j]) else np.zeros(len(frame)) for j in range(2)
            ]).mean(axis=1)
            actual = {row["alternative_id"]: row["score"]
                      for row in result["additional_baselines"]["deficiency_rule"]}
            np.testing.assert_allclose([actual[aid] for aid in frame.alternative_id], expected)


if __name__ == "__main__":
    unittest.main()
