"""Site readiness tests for the GEMSDOE72 GitHub Pages site.

Asserts the site IS ready: a validated TIF is offered for download, the
verdict box says so explicitly, the submission guide names the exact file,
and the run card reports measured (not null) holdout-DTI with a promote
verdict.
"""

from html.parser import HTMLParser
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.extend(value for key, value in attrs if key == "href")


class SiteReadinessTests(unittest.TestCase):
    def test_landing_page_offers_a_validated_tif(self):
        root_page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("docs/index.html", root_page)
        page = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
        self.assertIn("Download: yes", page)
        self.assertIn("Submit: yes", page)
        self.assertIn("gemsdoe72-h72-1-sgmc-offcatalogue-20261020T195456Z-6e6525e5-zeros.tif", page)
        self.assertIn("650b5ad2273f3634c15c0a97840ce36056906d3a2cedb110a77f8708c6783966", page)
        self.assertIn("0.1885", page)
        self.assertIn("[0.1658, 0.2113]", page)

    def test_internal_landing_links_resolve(self):
        parser = Links()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        for href in parser.hrefs:
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            self.assertTrue((ROOT / href).is_file(), f"broken internal link: {href}")

    def test_submission_guide_names_the_validated_file(self):
        guide = (ROOT / "docs/executive-summary.html").read_text(encoding="utf-8")
        self.assertIn("gemsdoe72-h72-1-sgmc-offcatalogue-20261020T195456Z-6e6525e5-zeros.tif", guide)
        self.assertIn("650b5ad2273f3634c15c0a97840ce36056906d3a2cedb110a77f8708c6783966", guide)
        self.assertIn("[0, 1]", guide)
        self.assertIn("EPSG:32611", guide)
        note = "GEMSDOE72 H72-1 | off-catalogue SGMC faults, dot-thinned 280 m; 27,823 px, 0 on catalogue; holdout-DTI 0.1885 CI [0.166,0.211] | UNSCORED"
        self.assertIn(note, guide)
        self.assertLessEqual(len(note), 140)

    def test_run_card_reports_measured_holdout_and_promote_verdict(self):
        card = json.loads((ROOT / "run_card.json").read_text(encoding="utf-8"))
        self.assertIsInstance(card["holdout_dti"], float)
        self.assertIsNotNone(card["holdout_95ci"])
        self.assertEqual(len(card["holdout_95ci"]), 2)
        self.assertEqual(card["verdict"], "promote")
        self.assertEqual(len(card["submission_note"]), 137)

    def test_submission_file_exists_and_matches_the_run_card(self):
        card = json.loads((ROOT / "run_card.json").read_text(encoding="utf-8"))
        tif = ROOT / "docs" / "downloads" / card["submission_name"]
        self.assertTrue(tif.is_file(), f"missing {tif}")


def card_name():
    return json.loads((ROOT / "run_card.json").read_text(encoding="utf-8"))["submission_name"]


if __name__ == "__main__":
    unittest.main()
