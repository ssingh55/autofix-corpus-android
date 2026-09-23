"""Score an autofix run against expected.yaml.

Inputs are Appknox `api/v2/files/<id>/analyses` payloads for the baseline scan
(before) and the rescan of the autofix PR head (after).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

FIX_OUTCOMES = {"fix:code", "fix:manifest", "fix:resource", "fix:add-code"}
OUTCOMES = FIX_OUTCOMES | {"declined:build", "record-only", "canary"}
FLAVORS = {"full", "legacy"}


class IncompleteScan(Exception):
    """The after-scan reports fewer analyses than the baseline: not finished."""


def load_expected(path) -> list[dict]:
    """Load and validate expected.yaml rows."""
    data = yaml.safe_load(Path(path).read_text())
    rows = data["vulnerabilities"]
    for row in rows:
        if row["outcome"] not in OUTCOMES:
            raise ValueError(f"id {row['id']}: unknown outcome {row['outcome']!r}")
        if row["flavor"] not in FLAVORS:
            raise ValueError(f"id {row['id']}: unknown flavor {row['flavor']!r}")
    return rows


def risky(analyses: dict) -> dict[int, int]:
    """Map vulnerability id to computed risk, for analyses above Passed."""
    return {a["vulnerability"]: a.get("computed_risk", 0)
            for a in analyses.get("results", [])
            if a.get("computed_risk", 0) > 0}


def _flavor_rows(rows: list[dict], flavor: str) -> list[dict]:
    return [r for r in rows if r["flavor"] == flavor]


def detect(rows: list[dict], flavor: str, before: dict[int, int]) -> list[int]:
    """Planted ids of this flavor the baseline scan did not report (canaries excluded)."""
    return sorted(r["id"] for r in _flavor_rows(rows, flavor)
                  if r["outcome"] != "canary" and r["id"] not in before)


def _result(row: dict, before: dict[int, int], after: dict[int, int]) -> str:
    vid, outcome = row["id"], row["outcome"]
    if outcome in ("record-only", "canary"):
        return "recorded-present" if vid in after else "recorded-cleared"
    if vid not in before:
        return "detection-gap"
    if outcome == "declined:build":
        return "declined-as-expected" if vid in after else "cleared-unexpectedly"
    if vid not in after:
        return "fixed-as-expected"
    if any(s in after for s in row.get("shared_with", [])):
        return "blocked-by-shared"
    return "missed-known-gap" if row.get("known_gap") else "missed"


def score(rows, flavor, before, after, before_count, after_count) -> dict:
    """Assign every planted id of this flavor a result, and list regressions."""
    if after_count < before_count:
        raise IncompleteScan(
            f"after-scan has {after_count} analyses, baseline {before_count}: not finished")
    scored = [{"id": r["id"], "outcome": r["outcome"], "result": _result(r, before, after)}
              for r in _flavor_rows(rows, flavor)]
    return {"flavor": flavor, "rows": scored,
            "regressions": sorted(set(after) - set(before))}


def render_markdown(report: dict) -> str:
    """Scorecard for the GitHub job summary."""
    lines = [f"### Autofix corpus scorecard ({report['flavor']})", "",
             "| id | expected | result |", "|---|---|---|"]
    lines += [f"| {r['id']} | {r['outcome']} | {r['result']} |" for r in report["rows"]]
    lines += ["", f"Regressions (new ids after the fix): {report['regressions'] or 'none'}"]
    return "\n".join(lines) + "\n"


def _load_json(path: str) -> dict:
    return json.loads(Path(path).read_text())


def main(argv: list[str]) -> int:
    """CLI entry point: `detect` (gate on baseline coverage) or `score` (write reports)."""
    parser = argparse.ArgumentParser(prog="score.py")
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("detect", "score"):
        p = sub.add_parser(name)
        p.add_argument("--expected", required=True)
        p.add_argument("--flavor", required=True, choices=sorted(FLAVORS))
        p.add_argument("--before", required=True)
        if name == "score":
            p.add_argument("--after", required=True)
            p.add_argument("--summary", required=True)
            p.add_argument("--json", required=True)
    args = parser.parse_args(argv)

    rows = load_expected(args.expected)
    before_payload = _load_json(args.before)
    before = risky(before_payload)
    if args.cmd == "detect":
        gaps = detect(rows, args.flavor, before)
        sys.stdout.write(f"detection gaps ({args.flavor}): {gaps or 'none'}\n")
        return 1 if gaps else 0

    after_payload = _load_json(args.after)
    report = score(rows, args.flavor, before, risky(after_payload),
                   before_payload.get("count", 0), after_payload.get("count", 0))
    Path(args.summary).write_text(render_markdown(report))
    Path(args.json).write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
