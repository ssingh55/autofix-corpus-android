import json
import textwrap

import pytest

import score

ROWS = [
    {"id": 17, "flavor": "full", "outcome": "fix:code", "where": "v17/LogLeak.kt"},
    {"id": 38, "flavor": "full", "outcome": "fix:manifest", "where": "AndroidManifest.xml",
     "shared_with": [85, 86]},
    {"id": 85, "flavor": "full", "outcome": "fix:code", "where": "v85/PrefActivity.kt"},
    {"id": 86, "flavor": "full", "outcome": "fix:code", "where": "v86/FileWebActivity.kt"},
    {"id": 92, "flavor": "full", "outcome": "fix:add-code", "where": "(absence)", "known_gap": True},
    {"id": 104, "flavor": "full", "outcome": "declined:build", "where": "app/build.gradle.kts"},
    {"id": 37, "flavor": "full", "outcome": "record-only", "where": "redis/clients/jedis/Jedis.kt"},
    {"id": 4, "flavor": "full", "outcome": "canary", "where": "AndroidManifest.xml"},
    {"id": 11, "flavor": "legacy", "outcome": "declined:build", "where": "v11/JsBridge.kt"},
]


def analyses(risks: dict[int, int]) -> dict:
    return {"count": 60, "results": [
        {"vulnerability": vid, "computed_risk": risk} for vid, risk in risks.items()]}


def result_for(report, vid):
    return next(r["result"] for r in report["rows"] if r["id"] == vid)


def test_risky_keeps_only_positive_risk():
    assert score.risky(analyses({17: 2, 96: 0})) == {17: 2}


def test_detect_gate_lists_missing_non_canary_ids_for_flavor():
    before = score.risky(analyses({17: 2, 38: 2, 85: 2, 86: 2, 92: 1, 104: 2, 37: 3}))
    assert score.detect(ROWS, "full", before) == []
    del before[17]
    assert score.detect(ROWS, "full", before) == [17]


def test_detect_gate_ignores_canary_and_other_flavor():
    before = score.risky(analyses({17: 2, 38: 2, 85: 2, 86: 2, 92: 1, 104: 2, 37: 3}))
    assert 4 not in score.detect(ROWS, "full", before)
    assert 11 not in score.detect(ROWS, "full", before)


def test_fixed_missed_declined_and_record_only():
    before = {17: 2, 38: 2, 85: 2, 86: 2, 92: 1, 104: 2, 37: 3, 4: 1}
    after = {38: 2, 85: 2, 86: 2, 92: 1, 104: 2, 37: 3}
    report = score.score(ROWS, "full", before, after, 60, 60)
    assert result_for(report, 17) == "fixed-as-expected"
    assert result_for(report, 92) == "missed-known-gap"
    assert result_for(report, 104) == "declined-as-expected"
    assert result_for(report, 37) == "recorded-present"
    assert result_for(report, 4) == "recorded-cleared"


def test_shared_trigger_blocks_miss():
    before = {17: 2, 38: 2, 85: 2, 86: 2}
    after = {38: 2, 85: 2}  # 86 fixed, 85 not: 38 cannot clear while 85 is exported
    report = score.score(ROWS, "full", before, after, 60, 60)
    assert result_for(report, 38) == "blocked-by-shared"
    assert result_for(report, 85) == "missed"
    assert result_for(report, 86) == "fixed-as-expected"


def test_declined_but_cleared_is_flagged():
    report = score.score(ROWS, "full", {104: 2}, {}, 60, 60)
    assert result_for(report, 104) == "cleared-unexpectedly"


def test_undetected_row_is_detection_gap_not_fixed():
    report = score.score(ROWS, "full", {}, {}, 60, 60)
    assert result_for(report, 17) == "detection-gap"


def test_regression_reported():
    report = score.score(ROWS, "full", {17: 2}, {120: 3}, 60, 60)
    assert report["regressions"] == [120]


def test_incomplete_after_scan_refuses():
    with pytest.raises(score.IncompleteScan):
        score.score(ROWS, "full", {17: 2}, {}, 60, 41)


def test_load_expected_rejects_unknown_outcome(tmp_path):
    p = tmp_path / "e.yaml"
    p.write_text(textwrap.dedent("""
        vulnerabilities:
          - {id: 17, flavor: full, outcome: "fix:magic", where: x}
    """))
    with pytest.raises(ValueError, match="outcome"):
        score.load_expected(p)


def test_cli_detect_exit_code(tmp_path):
    e = tmp_path / "e.yaml"
    e.write_text('vulnerabilities:\n  - {id: 17, flavor: full, outcome: "fix:code", where: x}\n')
    b = tmp_path / "b.json"
    b.write_text(json.dumps(analyses({})))
    assert score.main(["detect", "--expected", str(e), "--flavor", "full", "--before", str(b)]) == 1
    b.write_text(json.dumps(analyses({17: 2})))
    assert score.main(["detect", "--expected", str(e), "--flavor", "full", "--before", str(b)]) == 0


def test_render_markdown_has_row_per_id():
    report = score.score(ROWS, "full", {17: 2}, {}, 60, 60)
    md = score.render_markdown(report)
    assert "| 17 |" in md and "fixed-as-expected" in md


# --- final-review fixes: precondition removal, record-only sharers, canary vs record-only gate,
# --- not-attempted, the score CLI and its clean IncompleteScan exit.

TLS_ROWS = [
    {"id": 5, "flavor": "full", "outcome": "fix:code", "where": "v5/TrustAllManager.kt",
     "requires_permission": "android.permission.INTERNET"},
    {"id": 10, "flavor": "full", "outcome": "fix:manifest", "where": "AndroidManifest.xml",
     "shared_with": [34]},
    {"id": 34, "flavor": "full", "outcome": "record-only", "where": "AndroidManifest.xml"},
    {"id": 38, "flavor": "full", "outcome": "fix:manifest", "where": "AndroidManifest.xml",
     "shared_with": [34, 85]},
    {"id": 85, "flavor": "full", "outcome": "fix:code", "where": "v85/PrefActivity.kt"},
    {"id": 86, "flavor": "full", "outcome": "canary", "where": "v86/FileWebActivity.kt"},
]


def test_cleared_after_permission_removed_is_not_credited_as_fixed():
    report = score.score(TLS_ROWS, "full", {5: 3, 10: 1}, {}, 60, 60,
                         removed_permissions=["android.permission.INTERNET"])
    assert result_for(report, 5) == "cleared-by-precondition-removal"
    assert result_for(report, 10) == "fixed-as-expected"


def test_cleared_with_permission_kept_is_fixed():
    report = score.score(TLS_ROWS, "full", {5: 3}, {}, 60, 60)
    assert result_for(report, 5) == "fixed-as-expected"


def test_record_only_sharer_is_not_a_blocker():
    before = {10: 1, 34: 1, 38: 2, 85: 2}
    report = score.score(TLS_ROWS, "full", before, {10: 1, 34: 1, 38: 2}, 60, 60)
    assert result_for(report, 10) == "blocked-by-record-only"
    assert result_for(report, 38) == "blocked-by-record-only"


def test_fixable_sharer_still_blocks_even_with_record_only_present():
    before = {34: 1, 38: 2, 85: 2}
    report = score.score(TLS_ROWS, "full", before, {34: 1, 38: 2, 85: 2}, 60, 60)
    assert result_for(report, 38) == "blocked-by-shared"


def test_no_sharer_present_is_missed():
    report = score.score(TLS_ROWS, "full", {10: 1, 34: 1}, {10: 1}, 60, 60)
    assert result_for(report, 10) == "missed"


def test_not_attempted_beats_missed_and_blocked():
    report = score.score(TLS_ROWS, "full", {10: 1, 34: 1}, {10: 1, 34: 1}, 60, 60,
                         not_attempted=[10])
    assert result_for(report, 10) == "not-attempted"


def test_undetected_record_only_is_gated_but_canary_is_not():
    gaps = score.detect(TLS_ROWS, "full", {5: 3, 10: 1, 38: 2, 85: 2})
    assert 34 in gaps  # record-only: fires-but-unfixable, so it must be detected
    assert 86 not in gaps  # canary: cannot be triggered, the only exempt outcome


def _score_files(tmp_path, before, after):
    e = tmp_path / "e.yaml"
    e.write_text(
        'vulnerabilities:\n'
        '  - {id: 5, flavor: full, outcome: "fix:code", where: x, '
        'requires_permission: android.permission.INTERNET}\n'
        '  - {id: 17, flavor: full, outcome: "fix:code", where: x}\n')
    b, a = tmp_path / "b.json", tmp_path / "a.json"
    b.write_text(json.dumps(before))
    a.write_text(json.dumps(after))
    return ["score", "--expected", str(e), "--flavor", "full", "--before", str(b),
            "--after", str(a), "--summary", str(tmp_path / "s.md"),
            "--json", str(tmp_path / "s.json")]


def test_cli_score_writes_summary_and_json(tmp_path):
    argv = _score_files(tmp_path, analyses({5: 3, 17: 2}), analyses({17: 2}))
    argv += ["--removed-permission", "android.permission.INTERNET",
             "--meta", "appknox-go=4f69cc6", "--meta", "files=1/2",
             "--partial", "full: budget exhausted"]
    assert score.main(argv) == 0
    report = json.loads((tmp_path / "s.json").read_text())
    assert {r["id"]: r["result"] for r in report["rows"]} == {
        5: "cleared-by-precondition-removal", 17: "missed"}
    md = (tmp_path / "s.md").read_text()
    assert md.startswith("### Autofix corpus scorecard (full) PARTIAL: full: budget exhausted")
    assert "- appknox-go: 4f69cc6" in md and "- files: 1/2" in md
    assert "| 17 | fix:code | missed |" in md


def test_cli_score_not_attempted(tmp_path):
    argv = _score_files(tmp_path, analyses({5: 3, 17: 2}), analyses({17: 2}))
    assert score.main(argv + ["--not-attempted", "17"]) == 0
    report = json.loads((tmp_path / "s.json").read_text())
    assert {r["id"]: r["result"] for r in report["rows"]}[17] == "not-attempted"


def test_cli_incomplete_scan_exits_cleanly(tmp_path, capsys):
    before = analyses({5: 3, 17: 2})
    after = {"count": 10, "results": []}
    argv = _score_files(tmp_path, before, after)
    with pytest.raises(SystemExit) as exc:
        score.cli(argv)
    assert "not finished" in str(exc.value.code)
    assert not (tmp_path / "s.md").exists()


def test_cli_rejects_malformed_meta(tmp_path):
    argv = _score_files(tmp_path, analyses({5: 3}), analyses({}))
    with pytest.raises(SystemExit):
        score.main(argv + ["--meta", "no-equals-sign"])


MANIFEST = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    {perm}
    <uses-permission android:name="android.permission.VIBRATE" />
</manifest>
"""
INTERNET = '<uses-permission android:name="android.permission.INTERNET" />'


def test_removed_permissions_from_manifests(tmp_path):
    kept, gone, commented = (tmp_path / n for n in ("kept.xml", "gone.xml", "commented.xml"))
    kept.write_text(MANIFEST.format(perm=INTERNET))
    gone.write_text(MANIFEST.format(perm=""))
    commented.write_text(MANIFEST.format(perm=f"<!-- {INTERNET} -->"))
    assert score.removed_permissions(TLS_ROWS, [kept]) == set()
    assert score.removed_permissions(TLS_ROWS, [gone]) == {"android.permission.INTERNET"}
    assert score.removed_permissions(TLS_ROWS, [commented]) == {"android.permission.INTERNET"}
    # Declared in any of the merged manifests (e.g. moved to main) still counts as kept.
    assert score.removed_permissions(TLS_ROWS, [gone, kept]) == set()


def test_cli_score_manifest_marks_precondition_removal(tmp_path):
    argv = _score_files(tmp_path, analyses({5: 3, 17: 2}), analyses({17: 2}))
    m = tmp_path / "m.xml"
    m.write_text(MANIFEST.format(perm=""))
    assert score.main(argv + ["--manifest", str(m)]) == 0
    rows = json.loads((tmp_path / "s.json").read_text())["rows"]
    assert {r["id"]: r["result"] for r in rows}[5] == "cleared-by-precondition-removal"
    m.write_text(MANIFEST.format(perm=INTERNET))
    assert score.main(argv + ["--manifest", str(m)]) == 0
    rows = json.loads((tmp_path / "s.json").read_text())["rows"]
    assert {r["id"]: r["result"] for r in rows}[5] == "fixed-as-expected"
