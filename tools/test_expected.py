import re
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


AKIA_RE = re.compile(r"AKIA[A-Z0-9]*")


def _akia_tokens():
    """(file:line, token) for every AKIA token under app/. Values are never printed."""
    for f in sorted((ROOT / "app").rglob("*")):
        if not f.is_file() or f.suffix not in {".kt", ".xml", ".java"}:
            continue
        for n, line in enumerate(f.read_text().splitlines(), 1):
            for m in AKIA_RE.finditer(line):
                yield f"{f.relative_to(ROOT)}:{n}", m.group(0)


def test_planted_akia_keys_are_16_char_word_free_suffixes():
    tokens = list(_akia_tokens())
    assert len(tokens) == 2, [where for where, _ in tokens]
    for where, tok in tokens:
        suffix = tok[4:]
        # Messages name file:line and length only, never the value.
        assert len(suffix) == 16, f"{where}: suffix length {len(suffix)}, want 16"
        assert re.fullmatch(r"[A-Z0-9]{16}", suffix), f"{where}: suffix not [A-Z0-9]{{16}}"
        assert not re.search(r"[A-Z]{4,}", suffix), (
            f"{where}: suffix has an alphabetic run of 4+ (Sherlock's word filter drops it)")


def test_tls_rows_require_internet_and_internet_is_used():
    by_id = {r["id"]: r for r in rows()}
    for vid in (5, 6, 7, 8, 9):
        assert by_id[vid].get("requires_permission") == "android.permission.INTERNET", vid
    corpus = (ROOT / "app/src/full/java/com/appknox/corpus/Corpus.kt").read_text()
    assert "reportNetworkConnectivity" in corpus


def test_untriggerable_rows_are_canaries():
    by_id = {(r["id"], r["flavor"]): r for r in rows()}
    assert by_id[(82, "legacy")]["outcome"] == "canary"
    assert by_id[(86, "full")]["outcome"] == "canary"
