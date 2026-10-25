"""Content and numeric checks on the separately saved revised Word report."""
import hashlib
import json
import re
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
TITLE = "A Fuzzy TOPSIS Framework for Prioritising Pedestrian Crossing Safety and Accessibility Improvements"


def text(node):
    return "".join(node.itertext())


class RevisedReportDocumentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = json.loads((ROOT / "reports/revised_evaluation/summary.json").read_text())
        cls.primary = cls.result["primary"]
        with ZipFile(ROOT / "P20_Fuzzy_TOPSIS_Report_Revised.docx") as archive:
            cls.xml = ET.fromstring(archive.read("word/document.xml"))
            cls.core = ET.fromstring(archive.read("docProps/core.xml"))
            cls.part_texts = [text(ET.fromstring(archive.read(name)))
                              for name in archive.namelist()
                              if name.endswith(".xml") and (name.startswith("word/") or name.startswith("docProps/"))]
            cls.relationships = ET.fromstring(archive.read("word/_rels/document.xml.rels"))
        cls.paragraphs = [text(p) for p in cls.xml.findall(".//w:p", NS)]
        cls.content = "\n".join(cls.paragraphs)
        cls.tables = [[[text(cell) for cell in row.findall("w:tc", NS)]
                       for row in table.findall("w:tr", NS)] for table in cls.xml.findall(".//w:tbl", NS)]

    def table(self, first_header):
        return next(rows for rows in self.tables if rows[0] == first_header)

    def test_required_structure_original_title_and_no_template_or_forbidden_dashes(self):
        self.assertEqual(self.core.find("{http://purl.org/dc/elements/1.1/}title").text, TITLE)
        for heading in ["Abstract", "I Introduction", "II Related Work", "III Study Scope and Data",
                        "IV Methodology", "V Implementation and Evaluation", "VI Results",
                        "VII Discussion and Limitations", "VIII Conclusion", "Acknowledgement", "References"]:
            self.assertIn(heading, self.paragraphs)
        for part in self.part_texts:
            self.assertNotRegex(part, "[\u2013\u2014]")
            self.assertNotRegex(part, r"\[(?:Team|Student|Department|Institutional|Insert|Add or remove)[^]]*\]")
        self.assertNotIn("SAMPLE ONLY", self.content)
        self.assertEqual(len(self.xml.findall(".//m:oMath", NS)), 6)
        for number in range(1, 7):
            self.assertIn(f"({number})", self.content)
        for number in range(1, 11):
            self.assertRegex(self.content, rf"\[{number}\]")
        for caption in ("Table 1.", "Table 2.", "Table 3.", "Table 4.", "Table 5.", "Table 6.",
                        "Figure 1.", "Table A1.", "Table B1.", "Table C1.", "Table D1.", "Table F1."):
            self.assertIn(caption, self.content)

    def test_verified_team_members_and_repository_link(self):
        self.assertIn("Team 034", self.paragraphs)
        for author in ("Mohammed Ashar Husain (2024BCS0137)", "Muhamed Fadhil (2024BCS0093)", "Anjo P S (2024BCS0097)"):
            self.assertIn(author, self.paragraphs)
        author = self.core.find("{http://purl.org/dc/elements/1.1/}creator").text
        self.assertEqual(author, "Mohammed Ashar Husain; Muhamed Fadhil; Anjo P S")
        url = "https://github.com/Fadhil006/fuzzy-topsis-pedestrian-crossings"
        self.assertIn(url, self.content)
        self.assertTrue(any(rel.attrib.get("Target") == url and rel.attrib.get("TargetMode") == "External"
                            for rel in self.relationships))

    def test_main_and_complete_rank_tables_do_not_mislabel_central_mean_as_topsis(self):
        extra = self.result["additional_baselines"]
        crisp = {r["alternative_id"]: r for r in extra["crisp_topsis"]}
        deficiency = {r["alternative_id"]: r for r in extra["deficiency_rule"]}
        leading = self.table(["Rank", "OSM node ID", "Fuzzy score", "Four-criterion rank", "Mean rule rank", "Crisp TOPSIS rank"])
        expected = [[str(r["rank"]), r["alternative_id"].removeprefix("SYN-OSM-"), f"{r['score']:.4f}",
                     str(r["base_rank"]), str(r["crisp_rank"]), str(crisp[r["alternative_id"]]["rank"])]
                    for r in self.primary["top_candidates"][:5]]
        self.assertEqual(leading[1:], expected)
        complete = self.table(["Fuzzy rank", "Alternative ID", "Fuzzy score", "Fuzzy rank (4)",
                               "Mean rank (4)", "Crisp rank (5)", "Deficiency rank"])
        self.assertEqual(complete[1:], [[str(r["rank"]), r["alternative_id"], f"{r['score']:.6f}", str(r["base_rank"]),
                                        str(r["crisp_rank"]), str(crisp[r["alternative_id"]]["rank"]),
                                        str(deficiency[r["alternative_id"]]["rank"])]
                                       for r in self.primary["all_candidates"]])

    def test_comparison_and_uncertainty_table_values(self):
        comparisons = self.primary["comparisons"] + self.result["additional_baselines"]["comparisons"]
        table = self.table(["Comparison", "Top choice changed", "Top-three overlap", "Spearman ρ"])
        self.assertEqual([row[1:] for row in table[1:]],
                         [["Yes" if r["top1_changed"] else "No", f"{r['top_k_overlap']:.3f}", f"{r['spearman']:.3f}"]
                          for r in comparisons])
        scenarios = self.table(["Width factor α", "Interpretation", "Spearman ρ", "Leading pair"])
        for actual, expected in zip(scenarios[1:], self.primary["uncertainty"]):
            self.assertEqual(actual[0], f"{expected['width_factor']:.1f}")
            self.assertEqual(actual[2], f"{expected['spearman_vs_full']:.4f}")
        self.assertIn("514", self.content)
        self.assertIn("486", self.content)

    def test_both_worked_calculations_and_old_experiment_are_preserved(self):
        fuzzy = self.table(["Criterion", "Raw (l,c,u)", "Normalised", "Weight", "Weighted", "d+", "d-"])
        for actual, expected in zip(fuzzy[1:], self.primary["worked_example"]["criteria"]):
            self.assertEqual(actual, [expected["criterion"], str([round(v, 3) for v in expected["raw"]]),
                                      str([round(v, 3) for v in expected["normalized"]]), f"{expected['weight']:.2f}",
                                      str([round(v, 3) for v in expected["weighted"]]),
                                      f"{expected['distance_positive']:.6f}", f"{expected['distance_negative']:.6f}"])
        crisp = self.table(["Code", "Centre", "Min", "Max", "Normalised", "Weight", "Weighted", "Ideal +", "Ideal -"])
        expected = self.result["worked_crisp"]
        for i, actual in enumerate(crisp[1:]):
            self.assertEqual(actual[1:], [f"{expected['rawcentral'][i]:.1f}", f"{expected['minimums'][i]:.1f}",
                                         f"{expected['maximums'][i]:.1f}", f"{expected['normalized'][i]:.4f}",
                                         f"{expected['weights'][i]:.2f}", f"{expected['weighted'][i]:.4f}",
                                         f"{expected['positiveideal'][i]:.2f}", f"{expected['negativeideal'][i]:.2f}"])
        old = self.table(["ID", "Four-fuzzy score", "Four-fuzzy rank", "Four-mean rank", "Five-fuzzy score", "Five-fuzzy rank"])
        self.assertEqual(old[1:], [[r["alternative_id"], f"{r['base_score']:.6f}", str(r["base_rank"]), str(r["crisp_rank"]),
                                   f"{r['extension_score']:.6f}", str(r["extension_rank"])] for r in self.primary["old_demo"]])
        for value in ("0.35295551", "0.76370815", "0.68391959", "0.08333333", "0.40034707", "0.82770992"):
            self.assertIn(value, self.content)
        source = ROOT / "data/processed/pedestrian_crossings_fuzzy_topsis.csv"
        self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), self.primary["input_sha256"])


if __name__ == "__main__":
    unittest.main()
