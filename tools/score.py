"""Score an autofix run against expected.yaml.

Inputs are Appknox `api/v2/files/<id>/analyses` payloads for the baseline scan
(before) and the rescan of the autofix PR head (after).
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

FIX_OUTCOMES = {"fix:code", "fix:manifest", "fix:resource", "fix:add-code"}
OUTCOMES = FIX_OUTCOMES | {"declined:build", "record-only", "canary"}
FLAVORS = {"full", "legacy"}
ANDROID_NAME = "{http://schemas.android.com/apk/res/android}name"


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


def declared_permissions(manifests) -> set[str]:
    """Permissions requested by <uses-permission> elements (comments do not count)."""
    declared = set()
    for path in manifests:
        root = ET.parse(path).getroot()
        for tag in ("uses-permission", "uses-permission-sdk-23"):
            declared |= {e.get(ANDROID_NAME) for e in root.iter(tag) if e.get(ANDROID_NAME)}
    return declared


def removed_permissions(rows: list[dict], manifests) -> set[str]:
    """requires_permission values that none of the given (fix-branch) manifests declare."""
    required = {r["requires_permission"] for r in rows if r.get("requires_permission")}
    return required - declared_permissions(manifests)


def _flavor_rows(rows: list[dict], flavor: str) -> list[dict]:
    return [r for r in rows if r["flavor"] == flavor]


def detect(rows: list[dict], flavor: str, before: dict[int, int]) -> list[int]:
    """Planted ids of this flavor the baseline scan did not report (canaries excluded)."""
    return sorted(r["id"] for r in _flavor_rows(rows, flavor)
                  if r["outcome"] != "canary" and r["id"] not in before)


def _still_present(row: dict, after: dict[int, int], record_only: frozenset[int],
                   not_attempted: frozenset[int]) -> str:
    """Why an attempted-to-fix id survived the after-scan."""
    if row["id"] in not_attempted:
        return "not-attempted"
    sharers = [s for s in row.get("shared_with", []) if s in after]
    if any(s not in record_only for s in sharers):
        return "blocked-by-shared"
    if sharers:
        # Only record-only ids (never expected to be fixed) keep this one alive.
        return "blocked-by-record-only"
    return "missed-known-gap" if row.get("known_gap") else "missed"


def _result(row: dict, before: dict[int, int], after: dict[int, int],
            ctx: dict | None = None) -> str:
    """Result for one row. ctx: record_only / removed_permissions / not_attempted sets."""
    ctx = ctx or {}
    vid, outcome = row["id"], row["outcome"]
    if outcome in ("record-only", "canary"):
        return "recorded-present" if vid in after else "recorded-cleared"
    if vid not in before:
        return "detection-gap"
    if outcome == "declined:build":
        return "declined-as-expected" if vid in after else "cleared-unexpectedly"
    if vid not in after:
        if row.get("requires_permission") in ctx.get("removed_permissions", frozenset()):
            return "cleared-by-precondition-removal"
        return "fixed-as-expected"
    return _still_present(row, after, ctx.get("record_only", frozenset()),
                          ctx.get("not_attempted", frozenset()))


def score(rows, flavor, before, after, before_count, after_count,
          removed_permissions=(), not_attempted=()) -> dict:
    """Assign every planted id of this flavor a result, and list regressions.

    removed_permissions: permissions the fix branch no longer declares (rows whose
    requires_permission is among them cannot score fixed-as-expected).
    not_attempted: ids the fixer reported it never attempted.
    """
    if after_count < before_count:
        raise IncompleteScan(
            f"after-scan has {after_count} analyses, baseline {before_count}: not finished")
    ctx = {"record_only": frozenset(r["id"] for r in rows if r["outcome"] == "record-only"),
           "removed_permissions": frozenset(removed_permissions),
           "not_attempted": frozenset(not_attempted)}
    scored = [{"id": r["id"], "outcome": r["outcome"], "result": _result(r, before, after, ctx)}
              for r in _flavor_rows(rows, flavor)]
    return {"flavor": flavor, "rows": scored,
            "regressions": sorted(set(after) - set(before))}


def render_markdown(report: dict) -> str:
    """Scorecard for the GitHub job summary, with the run metadata and PARTIAL stamp on top."""
    title = f"### Autofix corpus scorecard ({report['flavor']})"
    if report.get("partial"):
        title += f" PARTIAL: {report['partial']}"
    lines = [title, ""]
    lines += [f"- {k}: {v}" for k, v in report.get("meta", {}).items()]
    if report.get("meta"):
        lines.append("")
    lines += ["| id | expected | result |", "|---|---|---|"]
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
            p.add_argument("--removed-permission", action="append", default=[],
                           help="permission the fix branch no longer declares (repeatable)")
            p.add_argument("--manifest", action="append", default=[],
                           help="fix-branch manifest; a requires_permission none of them "
                                "declares counts as removed (repeatable)")
            p.add_argument("--not-attempted", action="append", default=[], type=int,
                           help="id the fixer never attempted (repeatable)")
            p.add_argument("--partial", default="",
                           help="stamp the scorecard PARTIAL with this reason")
            p.add_argument("--meta", action="append", default=[],
                           help="KEY=VALUE line for the scorecard header (repeatable)")
    args = parser.parse_args(argv)

    if args.cmd == "score" and any("=" not in m for m in args.meta):
        parser.error("--meta takes KEY=VALUE")
    rows = load_expected(args.expected)
    before_payload = _load_json(args.before)
    before = risky(before_payload)
    if args.cmd == "detect":
        gaps = detect(rows, args.flavor, before)
        sys.stdout.write(f"detection gaps ({args.flavor}): {gaps or 'none'}\n")
        return 1 if gaps else 0

    after_payload = _load_json(args.after)
    report = score(rows, args.flavor, before, risky(after_payload),
                   before_payload.get("count", 0), after_payload.get("count", 0),
                   removed_permissions=set(args.removed_permission)
                   | (removed_permissions(rows, args.manifest) if args.manifest else set()),
                   not_attempted=args.not_attempted)
    report["meta"] = dict(m.split("=", 1) for m in args.meta)
    if args.partial:
        report["partial"] = args.partial
    Path(args.summary).write_text(render_markdown(report))
    Path(args.json).write_text(json.dumps(report, indent=2))
    return 0


def cli(argv: list[str]) -> int:
    """main() with an unfinished after-scan reported as one clean line, not a traceback."""
    try:
        return main(argv)
    except IncompleteScan as exc:
        sys.exit(f"score.py: {exc}")


if __name__ == "__main__":
    sys.exit(cli(sys.argv[1:]))
