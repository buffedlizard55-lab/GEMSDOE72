#!/usr/bin/env python3
"""Fetch and parse the public DrivenData leaderboard into a small JSON snapshot.

The snapshot is a public leaderboard listing, not a submission receipt. Parsing
fails closed: an unexpected page shape exits non-zero and leaves the output alone.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.request import Request, urlopen

URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self._table_depth = 0
        self._row: list[str] | None = None
        self._cell: list[str] | None = None
        self._table: list[list[str]] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "table":
            self._table_depth += 1
            if self._table_depth == 1:
                self._table = []
        elif self._table_depth == 1 and tag == "tr":
            self._row = []
        elif self._table_depth == 1 and tag in ("td", "th") and self._row is not None:
            self._cell = []
        elif self._cell is not None and tag == "br":
            self._cell.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self._table_depth == 1 and tag in ("td", "th") and self._cell is not None:
            text = "\n".join(line.strip() for line in "".join(self._cell).replace("\xa0", " ").splitlines() if line.strip())
            assert self._row is not None
            self._row.append(text)
            self._cell = None
        elif self._table_depth == 1 and tag == "tr" and self._row is not None:
            if self._table is not None:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table_depth:
            self._table_depth -= 1
            if self._table_depth == 0 and self._table is not None:
                self.tables.append(self._table)
                self._table = None

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell.append(data)


def parse_leaderboard(html: str, fetched_at: str | None = None) -> dict:
    parser = TableParser()
    parser.feed(html)
    for table in parser.tables:
        for row_index, row in enumerate(table):
            headers = [cell.casefold() for cell in row]
            score_column = next((i for i, text in enumerate(headers) if "dw-tversky" in text), None)
            if score_column is None:
                continue
            for candidate in table[row_index + 1:]:
                if len(candidate) <= score_column:
                    continue
                match = re.search(r"(?<!\d)(0\.\d+)(?!\d)", candidate[score_column])
                if not match:
                    continue
                rank_match = re.search(r"#\s*(\d+)", candidate[0]) if candidate else None
                name = candidate[2].split("\n", 1)[0].strip() if len(candidate) > 2 else ""
                return {
                    "updated_at": fetched_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
                    "source_url": URL,
                    "evidence_class": "ORGANIZER-CONFIRMED public leaderboard listing; not a submission receipt",
                    "rank": int(rank_match.group(1)) if rank_match else None,
                    "participant": name,
                    "score": float(match.group(1)),
                }
    raise ValueError("Could not identify the public DW-Tversky leaderboard table/leading score; no output written")


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, required=True, help="Destination JSON path")
    args = cli.parse_args()
    request = Request(URL, headers={"User-Agent": "GEMSDOE72-leaderboard-monitor/1.0"})
    try:
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(f"Leaderboard returned HTTP {response.status}")
            html = response.read().decode("utf-8", errors="replace")
        payload = parse_leaderboard(html)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(payload, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"WARNING: leaderboard refresh failed; retain the last known snapshot: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
