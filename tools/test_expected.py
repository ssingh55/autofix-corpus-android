from pathlib import Path

import pytest

import score

ROOT = Path(__file__).resolve().parent.parent
ALL_IDS = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 15, 16, 17, *range(29, 47), 82, 83, 84,
           85, 86, 88, 89, 92, 93, 94, 95, 96, 98, 104, 113, 117, 118, 120, 121, 122,
           127, 128, 133}


def rows():
    return score.load_expected(ROOT / "expected.yaml")


def test_ids_unique_per_flavor():
    seen = [(r["id"], r["flavor"]) for r in rows()]
    assert len(seen) == len(set(seen))


def test_where_paths_exist():
    for r in rows():
        if r["where"].startswith("("):
            continue
        assert (ROOT / r["where"]).exists(), f"id {r['id']}: {r['where']} missing"


def test_shared_with_refers_to_planted_ids():
    planted = {r["id"] for r in rows()}
    for r in rows():
        assert set(r.get("shared_with", [])) <= planted, r["id"]


def test_all_55_ids_planted():
    assert {r["id"] for r in rows()} == ALL_IDS


def test_legacy_sources_use_no_crypto():
    for base in ("app/src/legacy", "app/src/main"):
        for f in (ROOT / base).rglob("*.kt"):
            text = f.read_text()
            assert "javax.crypto" not in text and "java.security" not in text, f
