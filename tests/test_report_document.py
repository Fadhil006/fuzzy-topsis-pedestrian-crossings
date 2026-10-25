"""Check that the distributed report actually describes its current inputs."""
import hashlib
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
TITLE = "A Fuzzy TOPSIS Framework for Prioritising Pedestrian Crossing Safety and Accessibility Improvements"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}


class ReportDocumentChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = json.loads((ROOT / "reports/evaluation/summary.json").read_text())
        with ZipFile(ROOT / "P20_Fuzzy_TOPSIS_Report.docx") as archive:
            cls.xml = ET.fromstring(archive.read("word/document.xml"))
            core = ET.fromstring(archive.read("docProps/core.xml"))
        cls.title = core.find("{http://purl.org/dc/elements/1.1/}title").text
        cls.text = "\n".join("".join(p.itertext()) for p in cls.xml.findall(".//w:p", NS))

    def test_original_title_and_main_and_teaching_datasets_are_present(self):
        self.assertEqual(self.title, TITLE)
        self.assertIn(TITLE, self.text)
        for row in self.summary["all_candidates"]:
            self.assertIn(row["alternative_id"], self.text)
        for row in self.summary["old_demo"]:
            self.assertIn(row["alternative_id"], self.text)
        self.assertIn("hypothetical", self.text.lower())
        self.assertIn("synthetic", self.text.lower())

    def test_summary_and_quoted_results_match_current_input(self):
        source = ROOT / "data/processed/pedestrian_crossings_fuzzy_topsis.csv"
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), self.summary["input_sha256"])
        self.assertEqual(len(self.summary["all_candidates"]), 28)
        self.assertEqual(len(self.summary["old_demo"]), 4)
        for row in self.summary["top_candidates"][:8]:
            self.assertIn(f"{row['score']:.4f}", self.text)
        for i in range(1, 10):
            self.assertIn(f"[{i}]", self.text)


if __name__ == "__main__":
    unittest.main()
