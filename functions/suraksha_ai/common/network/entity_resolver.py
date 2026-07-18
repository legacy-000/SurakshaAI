import difflib
import hashlib
import logging
import re

logger = logging.getLogger(__name__)


# In-memory fallback when Data Store is unavailable.
_KNOWN_ACCUSED = [
    "Ravi Kumar", "Suresh P", "Rajesh K", "Manoj R", "Venkatesh G",
    "Prakash M", "Kumar S", "Anil K", "Sunil D", "Gopal R",
    "Mohan L", "Vijay K", "Arun P", "Karthik S", "Dinesh M",
]

_TITLES = {"mr", "ms", "sri", "shri", "smt", "mrs"}
_SUFFIXES = ("kumar", "appa", "anna", "amma")
_WS = re.compile(r"\s+")


def normalize_name(name: str) -> str:
    """Lowercase, strip titles, strip common suffixes, collapse whitespace."""
    if not name:
        return ""
    tokens = [t for t in _WS.sub(" ", name.strip().lower()).split() if t]
    tokens = [t for t in tokens if t not in _TITLES]
    if tokens and tokens[-1] in _SUFFIXES:
        tokens = tokens[:-1]
    return " ".join(tokens)


def _token_set(name: str) -> set:
    return set(normalize_name(name).split())


def _row_val(row: dict, key: str, cast=None):
    """Pull a column value from either a dict-row (column->value) or alternate shapes."""
    if row is None:
        return None
    if key in row:
        v = row[key]
    else:
        v = row.get("Accused", {}).get(key) if isinstance(row.get("Accused"), dict) else None
    if v is None or v == "":
        return None
    if cast is int:
        try:
            return int(v)
        except (TypeError, ValueError):
            return None
    return v


def _fetch_rows(db, sql: str) -> list:
    """Run ZCQL via the injected db; tolerate either DatastoreClient shape or raw zcql handler."""
    if db is None:
        return []
    # DatastoreClient shape
    if hasattr(db, "execute_non_query"):
        res = db.execute_non_query(sql)
        if not res or res.get("status") != "success":
            return []
        rows = res.get("rows", [])
        cols = res.get("columns", [])
        out = []
        for r in rows:
            if isinstance(r, list):
                out.append({c: v for c, v in zip(cols, r)})
            elif isinstance(r, dict):
                inner = list(r.values())[0] if r else {}
                out.append(inner if isinstance(inner, dict) else r)
        return out
    # Raw zcql handler or mock exposing execute_query
    if hasattr(db, "execute_query"):
        try:
            raw = db.execute_query(sql)
        except Exception as e:
            logger.info("execute_query failed: %s", e)
            return []
        if not raw:
            return []
        out = []
        for r in raw:
            if isinstance(r, dict):
                inner = list(r.values())[0]
                if isinstance(inner, dict):
                    out.append(inner)
        return out
    return []


_SQL_ACCUSED_ALL = (
    "SELECT ROWID, AccusedName, PersonID, CaseMasterID, AgeYear, GenderID "
    "FROM Accused LIMIT 200"
)


def _sql_accused_by_cases(case_ids: list) -> str:
    ids = ", ".join(str(int(c)) for c in case_ids)
    return (
        "SELECT ROWID, AccusedName, PersonID, CaseMasterID, AgeYear, GenderID "
        f"FROM Accused WHERE CaseMasterID IN ({ids}) LIMIT 200"
    )


def _age_close(a, b, tol: int = 5) -> bool:
    if a is None or b is None:
        return False
    return abs(int(a) - int(b)) <= tol


def _score(query_name: str, cand_name: str, q_age, q_gender,
           cand_age, cand_gender) -> float:
    qn = normalize_name(query_name)
    cn = normalize_name(cand_name)
    if not qn or not cn:
        return 0.0
    if qn == cn:
        base = 1.0
    else:
        qts, cts = _token_set(query_name), _token_set(cand_name)
        if qts and cts:
            overlap = len(qts & cts) / len(qts | cts)
        else:
            overlap = 0.0
        if overlap >= 0.8:
            base = 0.9
        else:
            ratio = difflib.SequenceMatcher(None, qn, cn).ratio()
            if ratio >= 0.88:
                base = 0.7
            else:
                return 0.0
    if q_gender is not None and cand_gender is not None and q_gender == cand_gender:
        if q_age is not None and cand_age is not None and _age_close(q_age, cand_age):
            base = min(1.0, base + 0.05)
    return base


class EntityResolver:
    def __init__(self):
        self._cache = None

    def _load_accused(self, db) -> list:
        if self._cache is not None:
            return self._cache
        rows = _fetch_rows(db, _SQL_ACCUSED_ALL)
        # normalize to a uniform dict shape
        out = []
        for r in rows:
            out.append({
                "rowid": _row_val(r, "ROWID", int),
                "accused_name": _row_val(r, "AccusedName"),
                "person_id": _row_val(r, "PersonID"),
                "case_master_id": _row_val(r, "CaseMasterID", int),
                "age": _row_val(r, "AgeYear", int),
                "gender": _row_val(r, "GenderID", int),
            })
        self._cache = out
        return out

    def _co_accused(self, db, case_ids: list, exclude_norm: str) -> list:
        if not case_ids:
            return []
        sql = _sql_accused_by_cases(case_ids)
        rows = _fetch_rows(db, sql)
        bucket: dict = {}
        for r in rows:
            name = _row_val(r, "AccusedName")
            if not name:
                continue
            norm = normalize_name(name)
            if norm == exclude_norm:
                continue
            cmid = _row_val(r, "CaseMasterID", int)
            if cmid is None:
                continue
            bucket.setdefault(norm, {"name": name, "case_ids": set()})
            bucket[norm]["case_ids"].add(cmid)
        return [
            {"name": v["name"], "together_in_case_ids": sorted(v["case_ids"])}
            for v in bucket.values()
        ]

    def resolve(self, name: str, db=None) -> list[dict]:
        if db is None:
            matches = difflib.get_close_matches(name, _KNOWN_ACCUSED, n=10, cutoff=0.6)
            results = []
            for i, m in enumerate(matches):
                confidence = round(1.0 - (i * 0.08), 2)
                results.append({
                    "name": m,
                    "confidence": max(confidence, 0.5),
                    "person_id": _KNOWN_ACCUSED.index(m) + 1000,
                    "case_count": max(1, 8 - i),
                    "matched_case_ids": [],
                    "aliases": [],
                    "co_accused": [],
                })
            return results

        try:
            accused = self._load_accused(db)
        except Exception as e:
            logger.warning("DB fetch failed, using fallback: %s", e)
            return self.resolve(name, db=None)

        if not accused:
            return self.resolve(name, db=None)

        q_age = None
        q_gender = None
        # Phase 1: score each Accused row
        scored = []
        for a in accused:
            if not a["accused_name"]:
                continue
            s = _score(name, a["accused_name"], q_age, q_gender,
                       a["age"], a["gender"])
            if s > 0.0:
                scored.append((s, a))

        if not scored:
            return []

        # Phase 2: cluster by normalized name
        clusters: dict = {}
        for s, a in scored:
            norm = normalize_name(a["accused_name"])
            if not norm:
                continue
            clusters.setdefault(norm, {"rows": [], "max_score": 0.0, "aliases": set()})
            clusters[norm]["rows"].append(a)
            clusters[norm]["max_score"] = max(clusters[norm]["max_score"], s)
            raw = a["accused_name"]
            if raw and raw != norm:
                clusters[norm]["aliases"].add(raw)

        results = []
        for norm, c in clusters.items():
            case_ids = sorted({a["case_master_id"] for a in c["rows"]
                              if a["case_master_id"] is not None})
            person_id = hashlib.md5(norm.encode()).hexdigest()[:12]
            co_acc = []
            try:
                co_acc = self._co_accused(db, case_ids, norm)
            except Exception as e:
                logger.warning("Co-accused fetch failed: %s", e)
            results.append({
                "name": c["rows"][0]["accused_name"],
                "person_id": person_id,
                "case_count": len(case_ids),
                "confidence": round(c["max_score"], 2),
                "matched_case_ids": case_ids,
                "aliases": sorted(c["aliases"]),
                "co_accused": co_acc,
            })

        results.sort(key=lambda r: r["confidence"], reverse=True)
        return results
