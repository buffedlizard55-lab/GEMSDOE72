from html.parser import HTMLParser
from pathlib import Path
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
    def test_landing_page_is_explicitly_not_ready(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("NO SUBMISSION FILE — DO NOT DOWNLOAD OR SUBMIT", page)
        self.assertIn("No download link is offered", page)

    def test_internal_landing_links_resolve(self):
        parser = Links()
        parser.feed((ROOT / "index.html").read_text(encoding="utf-8"))
        for href in parser.hrefs:
            if href.startswith(("http://", "https://", "#", "mailto:")):
                continue
            self.assertTrue((ROOT / href).is_file(), f"broken internal link: {href}")

    def test_submission_guide_does_not_claim_a_file_exists(self):
        guide = (ROOT / "docs/executive-summary.html").read_text(encoding="utf-8")
        self.assertIn("there is no validated TIF to download", guide)
        self.assertIn("Do not submit a file from here", guide)
        self.assertIn("[0,1]", guide)
        self.assertIn("EPSG:32611", guide)

    def test_candidate_run_card_keeps_unmeasured_results_null(self):
        report = (ROOT / "docs/hypotheses.md").read_text(encoding="utf-8")
        self.assertIn('"holdout_dti_ci": null', report)
        self.assertIn('"raster_sha256": null', report)
        self.assertIn('"verdict": "negative"', report)


if __name__ == "__main__":
    unittest.main()
