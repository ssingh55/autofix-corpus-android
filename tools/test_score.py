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
