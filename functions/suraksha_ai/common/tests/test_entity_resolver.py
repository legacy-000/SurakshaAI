from network.entity_resolver import EntityResolver, normalize_name
import sys
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE)
os.environ.setdefault("PYTHONPATH", BASE)


class FakeZCQL:
    """Mock db exposing execute_query, returning canned rows for the two ZCQL shapes."""

    def __init__(self, all_rows, case_rows):
        self.all_rows = all_rows
        self.case_rows = case_rows
        self.calls = []

    def execute_query(self, sql):
        self.calls.append(sql)
        if "CaseMasterID IN" in sql:
            return self.case_rows
        return self.all_rows


def _row(name, person, case, age, gender):
    return {"Accused": {
        "ROWID": 1, "AccusedName": name, "PersonID": person,
        "CaseMasterID": case, "AgeYear": age, "GenderID": gender,
    }}


class TestNormalize:
    def test_strips_titles(self):
        assert normalize_name("Mr Ravi Kumar") == "ravi"
        assert normalize_name("Smt Lakshmi") == "lakshmi"

    def test_strips_suffixes(self):
        assert normalize_name("Raj anna") == "raj"
        assert normalize_name("Suresh kumar") == "suresh"

    def test_case_and_whitespace(self):
        assert normalize_name("  RAVI   kumar ") == "ravi"


class TestFallbackPath:
    def test_exact_match_known_name(self):
        r = EntityResolver().resolve("Ravi Kumar")
        assert any(c["name"] == "Ravi Kumar" for c in r)
        assert all("confidence" in c for c in r)

    def test_unknown_returns_empty(self):
        # unknown name at high-ish cutoff = no match in fallback path
        r = EntityResolver().resolve("Zzzqq Xyyzzz Qqqzz")
        assert r == []

    def test_structure(self):
        r = EntityResolver().resolve("Ravi Kumar")
        for c in r:
            assert {"name", "person_id", "case_count", "confidence",
                    "matched_case_ids", "aliases", "co_accused"} <= c.keys()


class TestDBPath:
    def test_exact_match_db(self):
        all_rows = [
            _row("Ravi Kumar", None, 11, 30, 1),
            _row("Ravi kumar", None, 12, 31, 1),
            _row("Suresh", None, 13, 40, 1),
        ]
        case_rows = all_rows  # co-accused query returns same set
        db = FakeZCQL(all_rows, case_rows)
        r = EntityResolver().resolve("Ravi Kumar", db=db)
        assert any(c["case_count"] >= 1 for c in r)
        top = r[0]
        assert top["confidence"] >= 0.9
        assert "matched_case_ids" in top
        assert isinstance(top["co_accused"], list)

    def test_unknown_name_db_returns_empty(self):
        db = FakeZCQL([_row("Ravi Kumar", None, 11, 30, 1)], [])
        r = EntityResolver().resolve("Zzzz Noman Yyy", db=db)
        assert r == []

    def test_partial_match_db(self):
        all_rows = [_row("Suresh Kumar", None, 14, 35, 1)]
        db = FakeZCQL(all_rows, all_rows)
        r = EntityResolver().resolve("Suresh kumar", db=db)
        assert len(r) >= 1
        assert r[0]["confidence"] >= 0.7

    def test_no_zcql_join_or_like(self):
        all_rows = [_row("Ravi Kumar", None, 11, 30, 1)]
        db = FakeZCQL(all_rows, all_rows)
        EntityResolver().resolve("Ravi Kumar", db=db)
        for sql in db.calls:
            assert " JOIN " not in sql.upper()
            assert " LIKE " not in sql.upper()
            assert "COUNT(*)" not in sql.upper()
        # empty IN must never be emitted
        assert not any("IN ()" in sql for sql in db.calls)
