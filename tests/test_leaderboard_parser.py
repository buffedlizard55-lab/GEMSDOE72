import unittest

from scripts.refresh_leaderboard import parse_leaderboard


FIXTURE = """
<html><table>
  <tr><th>Rank</th><th>Team members</th><th>Participant</th>
      <th>Best public DW-Tversky (in descending order)</th><th>Shared work</th></tr>
  <tr><td>#1</td><td></td><td><a>ExampleTeam</a><br>2h ago</td><td>0.4413</td><td></td></tr>
  <tr><td>#2</td><td></td><td>OtherTeam</td><td>0.3811</td><td></td></tr>
</table></html>
"""


class LeaderboardParserTests(unittest.TestCase):
    def test_extracts_first_public_dw_tversky_row(self):
        result = parse_leaderboard(FIXTURE, fetched_at="2026-10-20T12:00:00Z")
        self.assertEqual(result["rank"], 1)
        self.assertEqual(result["score"], 0.4413)
        self.assertEqual(result["participant"], "ExampleTeam")
        self.assertIn("not a submission receipt", result["evidence_class"])

    def test_unexpected_page_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_leaderboard("<html><body>login required</body></html>")


if __name__ == "__main__":
    unittest.main()
