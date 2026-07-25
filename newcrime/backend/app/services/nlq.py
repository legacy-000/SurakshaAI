"""Natural-language query engine.

Two modes:
  - Rule-based (mock LLM): keyword matching + ORM queries. Zero API keys.
  - GLM-powered (Catalyst): GLM 4.7 generates ZCQL, executes against Datastore,
    GLM narrates the answer. Requires Catalyst project + GLM enabled.

Both return the same shape:
  {intent, answer, sql, evidence, data, grounding, reasoning}
"""
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models as m
from ..config import settings
from ..llm import get_llm

# ── lexicons (English + Kannada transliteration/script) ───────────────
CRIME_LEXICON = {
    "theft": "Theft", "burglary": "Burglary", "robbery": "Robbery",
    "vehicle theft": "Vehicle Theft", "chain snatching": "Chain Snatching",
    "snatching": "Chain Snatching", "assault": "Assault", "murder": "Murder",
    "kidnapping": "Kidnapping", "domestic": "Domestic Violence",
    "cyber": "Cyber Fraud", "cyber fraud": "Cyber Fraud", "bank fraud": "Bank Fraud",
    "upi": "UPI Scam", "extortion": "Extortion", "drug": "Drug Trafficking",
    "trafficking": "Human Trafficking", "riot": "Rioting",
    "ಕಳ್ಳತನ": "Theft", "ಕೊಲೆ": "Murder", "ದರೋಡೆ": "Robbery", "ಸೈಬರ್": "Cyber Fraud",
}
DISTRICTS = [
    "Bengaluru City", "Bengaluru Rural", "Mysuru", "Mangaluru", "Hubballi-Dharwad",
    "Belagavi", "Kalaburagi", "Ballari", "Vijayapura", "Davanagere", "Shivamogga",
    "Tumakuru", "Udupi", "Hassan", "Mandya",
]
STATUS_WORDS = {
    "open": "Open", "closed": "Closed", "cold": "Cold",
    "chargesheeted": "Chargesheeted", "under investigation": "Under Investigation",
}

ALLOWED_TABLES = {
    "users", "officers", "accused", "victims", "cases", "case_accused",
    "case_victim", "associations", "investigations", "timeline_events",
    "financial_accounts", "transactions", "crime_patterns", "predictions",
    "behavior_profiles", "alerts", "conversations", "messages", "case_notes",
    "evidence_documents", "witnesses", "audit_logs", "stage_approvals",
    "access_requests",
}

SCHEMA_CONTEXT = """You have access to a crime intelligence database with these tables:

TABLE cases: ROWID (id), fir_number, title, description, crime_type, crime_head, modus_operandi, status, severity, district, station, location_name, latitude, longitude, is_financial, loss_amount, occurrence_date, reported_date, CREATEDTIME
TABLE accused: ROWID (id), full_name, aliases, gender, age, address, district, phone_number, occupation, education, socio_economic, urban_rural, migrant, previous_convictions, status
TABLE victims: ROWID (id), full_name, gender, age, contact_number, address, district, occupation, statement_summary
TABLE case_accused: ROWID, case_id, accused_id, role_in_crime
TABLE case_victim: ROWID, case_id, victim_id
TABLE associations: ROWID, source_id, target_id, association_type, gang_name, strength
TABLE investigations: ROWID, case_id, officer_id, stage, priority, started_at, summary, assigned_by
TABLE timeline_events: ROWID, case_id, event_title, description, event_type, event_timestamp
TABLE financial_accounts: ROWID, accused_id, account_type, account_number, bank_name, balance, flagged
TABLE transactions: ROWID, source_account_id, target_account_id, amount, currency, channel, case_id, flagged, transaction_timestamp
TABLE behavior_profiles: ROWID, accused_id, risk_score, risk_band, propensity_tags, behavioral_traits, last_assessed, recidivism_probability
TABLE predictions: ROWID, crime_type, target_area, probability, risk_level, predicted_date, factors
TABLE alerts: ROWID, title, description, severity, category, resolved, case_id, CREATEDTIME
TABLE witnesses: ROWID, case_id, name, contact, statement, reliability, document_path, document_name
TABLE officers: ROWID, badge_number, name, rank, posting_station, district, contact_number

ZCQL RULES:
- Only SELECT queries allowed
- No GROUP BY with aggregate functions — fetch rows and I will aggregate in Python
- No JOINs — I will query each table separately
- Supported: WHERE, ORDER BY, LIMIT, IN, LIKE, AND, OR, COUNT(ROWID)
- Date format: YYYY-MM-DD
- String comparison is case-sensitive — use exact values from the lists below

CRIME_TYPES: Theft, Burglary, Robbery, Vehicle Theft, Chain Snatching, Assault, Murder, Kidnapping, Domestic Violence, Cyber Fraud, Bank Fraud, UPI Scam, Extortion, Drug Trafficking, Human Trafficking, Rioting

DISTRICTS: Bengaluru City, Bengaluru Rural, Mysuru, Mangaluru, Hubballi-Dharwad, Belagavi, Kalaburagi, Ballari, Vijayapura, Davanagere, Shivamogga, Tumakuru, Udupi, Hassan, Mandya

Respond ONLY with valid JSON: {"intent": "...", "zcql": "SELECT ...", "reasoning": "...", "needs_aggregation": true/false, "aggregation_column": "column_name_or_null"}
If the question is a greeting or help request, use intent "help" with empty zcql.
If the question doesn't map to the database, use intent "unknown" with empty zcql."""


def _detect_lang(text: str) -> str:
    return "kn" if re.search(r"[ಀ-೿]", text) else "en"


def validate_zcql(zcql: str) -> bool:
    if not zcql or not zcql.strip():
        return False
    normalized = zcql.strip().upper()
    if not normalized.startswith("SELECT"):
        return False
    if ";" in zcql:
        return False
    if len(zcql) > 500:
        return False
    dangerous = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE"]
    for word in dangerous:
        if re.search(rf'\b{word}\b', normalized):
            return False
    tables_in_query = re.findall(r'(?:FROM|JOIN)\s+(\w+)', zcql, re.IGNORECASE)
    for t in tables_in_query:
        if t.lower() not in ALLOWED_TABLES:
            return False
    return True


_GROUP_BY_RE = re.compile(r"\bGROUP\s+BY\s+([\w.]+)", re.IGNORECASE)
_COUNT_RE = re.compile(r"\bCOUNT\s*\(", re.IGNORECASE)


_SELECT_RE = re.compile(r"^\s*SELECT\s+(.*?)\s+FROM\s+(\w+)", re.IGNORECASE | re.DOTALL)


def _degroup(zcql: str):
    """Rewrite queries ZCQL answers with an empty result set.

    ZCQL supports a bare COUNT(...) but not GROUP BY, an aggregate mixed with
    plain columns, or ORDER BY over an aggregate. It returns zero rows instead
    of erroring, which narrates as "no data" — a confidently wrong answer.
    Widen those to a plain row fetch and aggregate in Python.

    Returns (zcql, group_column | None).
    """
    match = _SELECT_RE.match(zcql)
    if not match:
        return zcql, None
    select_list, table = match.group(1), match.group(2)

    group_by = _GROUP_BY_RE.search(zcql)
    group_col = group_by.group(1).split(".")[-1] if group_by else None
    # split on commas that aren't inside COUNT( ... )
    plain_cols = [c.strip() for c in re.split(r",(?![^()]*\))", select_list)
                  if c.strip() and not _COUNT_RE.search(c)]
    has_agg = bool(_COUNT_RE.search(select_list))
    orders_by_agg = bool(re.search(r"ORDER\s+BY\s+[^,]*COUNT\s*\(", zcql, re.IGNORECASE))

    # a lone COUNT(...) with no grouping is fine as-is
    if not group_by and not orders_by_agg and not (has_agg and plain_cols):
        return zcql, None

    if group_col is None and plain_cols and plain_cols[0] != "*":
        group_col = plain_cols[0].split(".")[-1].split()[0]

    return _widen(zcql)[0], group_col


def _widen(zcql: str):
    """Strip a query down to `SELECT * FROM table WHERE ...`.

    Returns (zcql, group_column | None); unchanged if it can't be parsed.
    """
    match = _SELECT_RE.match(zcql)
    if not match:
        return zcql, None
    select_list, table = match.group(1), match.group(2)
    plain = [c.strip() for c in re.split(r",(?![^()]*\))", select_list)
             if c.strip() and not _COUNT_RE.search(c)]
    col = plain[0].split(".")[-1].split()[0] if plain and plain[0] != "*" else None
    clause = re.search(r"\bWHERE\b(.*?)(?:\bGROUP\s+BY\b|\bORDER\s+BY\b|\bLIMIT\b|$)",
                       zcql, re.IGNORECASE | re.DOTALL)
    where = (" WHERE" + clause.group(1).rstrip()) if clause else ""
    return f"SELECT * FROM {table}{where}".strip(), col


def _count_from(rows):
    """Pull the scalar out of a COUNT(...) result row, if that's what it is."""
    if len(rows) != 1:
        return None
    for key, value in rows[0].items():
        if key.upper().startswith("COUNT"):
            try:
                return int(value)
            except (TypeError, ValueError):
                return None
    return None


def _fallback(db, question: str, lang: str, ctx, llm) -> dict:
    """Pick whichever engine can actually reach the data."""
    if settings.use_catalyst:
        return _catalyst_fallback(question, lang, ctx, llm)
    return _rule_based_answer(db, question, lang)


def _catalyst_fallback(question: str, lang: str, ctx, llm) -> dict:
    """Answer the common case questions from the Datastore, without GLM.

    The rule-based engine is SQLAlchemy-only, so under Catalyst a GLM outage
    would otherwise take chat down entirely. This covers the cases-table
    intents that make up most real questions and says so plainly for anything
    else, rather than guessing.
    """
    from ..catalyst_store import get_store

    t = question.lower().strip()
    if any(w in t for w in ("hello", "hi ", "help", "what can you", "namaste", "ನಮಸ್ಕಾರ")):
        return _reply("help", question, lang,
                      "I can answer questions about FIRs, case counts, crime types, "
                      "trends and district hotspots.", "-- no query", [], llm=llm)

    crime, district, status, year = _extract(question)
    where = []
    if crime:
        where.append(f"crime_type = '{crime}'")
    if district and (ctx is None or ctx.can_access_district(district)):
        where.append(f"district = '{district}'")
    if status:
        where.append(f"status = '{status}'")
    zcql = "SELECT * FROM cases" + (" WHERE " + " AND ".join(where) if where else "")

    try:
        rows = get_store().query(zcql)
    except Exception:
        return _reply("unknown", question, lang,
                      "The crime database is unreachable right now. Please retry shortly.",
                      "-- unavailable", [], llm=llm)
    if ctx is not None:
        rows = ctx.scope_rows(rows)

    scope_note = ""
    if ctx is not None and ctx.scope != "state":
        scope_note = f" in {', '.join(ctx.districts_in_scope()) or 'your jurisdiction'}"
    filters = ", ".join(x for x in (crime, district, status) if x) or "all cases"
    evidence = [{"table": "cases", "detail": f"{len(rows)} records matched {filters}",
                 "provenance": "DATABASE_FACT"}]

    if any(w in t for w in ("top crime", "most common", "crime types", "breakdown", "which crimes")):
        ranked = Counter(r.get("crime_type") or "Unknown" for r in rows).most_common(5)
        answer = ("Most frequent crime types" + scope_note + ": "
                  + "; ".join(f"{k} ({v})" for k, v in ranked) + ".")
        data = {"chart": "bar", "series": [{"label": k, "value": v} for k, v in ranked]}
        return _reply("crime_breakdown", question, lang, answer, zcql, evidence, data, llm)

    if any(w in t for w in ("hotspot", "which district", "which area", "top district", "where")):
        ranked = Counter(r.get("district") or "Unknown" for r in rows).most_common(5)
        answer = ("Districts with the most cases" + scope_note + ": "
                  + "; ".join(f"{k} ({v})" for k, v in ranked) + ".")
        data = {"chart": "bar", "series": [{"label": k, "value": v} for k, v in ranked]}
        return _reply("hotspots", question, lang, answer, zcql, evidence, data, llm)

    if any(w in t for w in ("trend", "over time", "monthly", "by month")):
        months = Counter((r.get("occurrence_date") or "")[:7] for r in rows if r.get("occurrence_date"))
        series = sorted(months.items())
        answer = (f"{len(rows)} cases{scope_note} across {len(series)} months"
                  + (f", peaking in {max(series, key=lambda kv: kv[1])[0]}." if series else "."))
        data = {"chart": "line", "series": [{"label": k, "value": v} for k, v in series]}
        return _reply("trend", question, lang, answer, zcql, evidence, data, llm)

    if any(w in t for w in ("show", "list", "recent")):
        top = sorted(rows, key=lambda r: r.get("occurrence_date") or "", reverse=True)[:5]
        lines = "; ".join(f"{r.get('fir_number')} — {r.get('title')} ({r.get('district')})"
                          for r in top)
        answer = f"{len(rows)} matching cases{scope_note}. Most recent: {lines}" if top \
            else f"No cases match {filters}{scope_note}."
        return _reply("list_cases", question, lang, answer, zcql, evidence,
                      {"count": len(rows), "rows": top}, llm)

    # counts, and anything else that still narrowed to cases
    if crime or district or status or any(w in t for w in ("how many", "count", "number of", "total")):
        one = len(rows) == 1
        answer = (f"There {'is' if one else 'are'} {len(rows)} "
                  f"{'case' if one else 'cases'} matching {filters}{scope_note}.")
        return _reply("count_cases", question, lang, answer, zcql, evidence,
                      {"count": len(rows)}, llm)

    return _reply("unknown", question, lang,
                  "The AI assistant is temporarily unavailable. I can still answer "
                  "questions about case counts, crime types, trends and district "
                  "hotspots — try rephrasing along those lines.",
                  "-- no query", [], llm=llm)


def answer_question(db, question: str, language: str | None = None, ctx=None) -> dict:
    lang = language or _detect_lang(question)
    llm = get_llm()

    if llm.provider == "catalyst" and hasattr(llm, "generate_query"):
        return _glm_answer(db, question, lang, llm, ctx)
    return _fallback(db, question, lang, ctx, llm)


# ── GLM-powered path ──────────────────────────────────────────────────

def _glm_answer(db, question: str, lang: str, llm, ctx=None) -> dict:
    from ..catalyst_store import get_store

    parsed = llm.generate_query(question, SCHEMA_CONTEXT)

    # GLM unreachable is not the same as GLM saying "I don't know" — degrade to
    # the rule-based engine instead of telling every user the question failed.
    if getattr(llm, "last_error", None):
        return _fallback(db, question, lang, ctx, llm)

    intent = parsed.get("intent", "unknown")
    zcql = parsed.get("zcql", "")
    reasoning_text = parsed.get("reasoning", "")

    if intent in ("help", "unknown") or not zcql:
        if intent == "help":
            answer = ("I can answer questions about FIRs, accused, victims, crime trends, "
                      "hotspots, offender risk, criminal networks, money trails and forecasts.")
        else:
            answer = ("I couldn't map that to the crime database. Try asking about case counts, "
                      "crime trends, hotspots, offenders, networks, money trails or forecasts.")
        return _reply(intent, question, lang, answer, "-- no query", [], llm=llm)

    if not validate_zcql(zcql):
        return _fallback(db, question, lang, ctx, llm)

    # GLM reaches for GROUP BY despite the prompt; ZCQL answers those with an
    # empty result set, so rewrite before executing.
    zcql, group_col = _degroup(zcql)

    # GLM writes no territory filter, so NLQ would otherwise bypass every
    # jurisdiction check in the routers. A COUNT can't be filtered after the
    # fact — widen it to rows so the scoped count is honest.
    scoped = ctx is not None and ctx.scope != "state"
    if scoped and _COUNT_RE.search(zcql):
        zcql = re.sub(r"^\s*SELECT\s+.*?\s+FROM\s+", "SELECT * FROM ", zcql,
                      flags=re.IGNORECASE | re.DOTALL)

    try:
        store = get_store()
        rows = store.query(zcql)
    except Exception:
        return _fallback(db, question, lang, ctx, llm)

    # Catch-all for aggregate shapes _degroup hasn't learned yet: GLM is
    # non-deterministic, and ZCQL answers anything it dislikes with an empty
    # set. Retry widened before concluding "no data", which would otherwise be
    # narrated as fact.
    if not rows and (_COUNT_RE.search(zcql) or _GROUP_BY_RE.search(zcql)):
        widened, inferred = _widen(zcql)
        if widened != zcql:
            retry = store.query(widened)
            if retry:
                rows, zcql = retry, widened
                group_col = group_col or inferred

    if scoped and rows and "district" in rows[0]:
        rows = ctx.scope_rows(rows)
    elif scoped and rows:
        # no district column to filter on — refuse rather than over-share
        return _reply("restricted", question, lang,
                      "That query spans data outside your jurisdiction. Ask about "
                      "cases, accused or victims in your own area.",
                      zcql, [], llm=llm)

    agg_col = group_col or (parsed.get("aggregation_column")
                            if parsed.get("needs_aggregation") else None)
    # a COUNT(...) query returns one row holding the total, not one row per hit
    if scoped:
        total = len(rows) if _COUNT_RE.search(parsed.get("zcql", "")) else None
    else:
        total = _count_from(rows) if _COUNT_RE.search(zcql) else None

    if total is not None:
        findings = f"Count: {total}."
        data = {"count": total}
    elif agg_col and not str(agg_col).upper().startswith("COUNT"):
        counts = dict(Counter(row.get(agg_col) or "Unknown" for row in rows))
        ranked = sorted(counts.items(), key=lambda kv: -kv[1])
        findings = (f"{len(rows)} matching records. Grouped by {agg_col}: "
                    f"{json.dumps(dict(ranked))}")
        data = {"chart": "bar",
                "series": [{"label": k, "value": v} for k, v in ranked]}
    else:
        findings = f"Query returned {len(rows)} rows."
        if rows:
            findings += f" Sample: {json.dumps(rows[:5], default=str)}"
        data = {"count": len(rows), "rows": rows[:20]}

    evidence = [{"table": t, "detail": f"Queried {t}", "provenance": "DATABASE_FACT"}
                for t in re.findall(r'(?:FROM)\s+(\w+)', zcql, re.IGNORECASE)]

    narrated = llm.narrate(question, findings, lang)

    return _reply(intent, question, lang, narrated, zcql, evidence, data=data, llm=llm)


# ── Rule-based path (original, zero-API-key) ──────────────────────────

def _extract(text: str):
    t = text.lower()
    crime = None
    for key, val in CRIME_LEXICON.items():
        if key in t or key in text:
            crime = val
            break
    district = next((d for d in DISTRICTS if d.lower() in t), None)
    if not district:
        district = next((d for d in DISTRICTS if d.split()[0].lower() in t), None)
    status = next((v for k, v in STATUS_WORDS.items() if k in t), None)
    ymatch = re.search(r"\b(20\d{2})\b", t)
    year = int(ymatch.group(1)) if ymatch else None
    return crime, district, status, year


def _rule_based_answer(db: Session, question: str, lang: str) -> dict:
    t = question.lower().strip()
    crime, district, status, year = _extract(question)

    def base_filter(q):
        if crime:
            q = q.filter(m.Case.crime_type == crime)
        if district:
            q = q.filter(m.Case.district == district)
        if status:
            q = q.filter(m.Case.status == status)
        if year:
            q = q.filter(func.strftime("%Y", m.Case.occurrence_date) == str(year))
        return q

    filters_desc = ", ".join(
        [x for x in [crime, district, status, str(year) if year else None] if x]) or "all records"

    if any(w in t for w in ["hello", "hi ", "help", "what can you", "namaste", "ನಮಸ್ಕಾರ"]):
        return _reply(
            intent="help", question=question, lang=lang,
            answer=("I can answer questions about FIRs, accused, victims, crime trends, "
                    "hotspots, offender risk, criminal networks, money trails and forecasts. "
                    "Try: 'How many cyber fraud cases in Bengaluru City?', "
                    "'Show crime trend', 'Top repeat offenders', 'Show hotspots'."),
            sql="-- no query (informational)", evidence=[])

    if any(w in t for w in ["top crime", "most common crime", "which crimes", "crime types", "breakdown"]):
        rows = (db.query(m.Case.crime_type, func.count(m.Case.id))
                .group_by(m.Case.crime_type).order_by(func.count(m.Case.id).desc()).limit(8).all())
        data = [{"label": r[0], "value": r[1]} for r in rows]
        top = ", ".join(f"{r[0]} ({r[1]})" for r in rows[:5])
        return _reply("top_crime_types", question, lang,
                      f"The most frequent crime types are: {top}.",
                      "SELECT crime_type, COUNT(*) FROM cases GROUP BY crime_type ORDER BY 2 DESC;",
                      [{"table": "cases", "detail": f"{r[0]}: {r[1]} cases"} for r in rows],
                      data={"chart": "bar", "series": data})

    if any(w in t for w in ["trend", "over time", "monthly", "by month", "timeline of crime"]):
        rows = (db.query(func.strftime("%Y-%m", m.Case.occurrence_date), func.count(m.Case.id))
                .group_by(func.strftime("%Y-%m", m.Case.occurrence_date))
                .order_by(func.strftime("%Y-%m", m.Case.occurrence_date)).all())
        data = [{"label": r[0], "value": r[1]} for r in rows if r[0]]
        return _reply("crime_trend", question, lang,
                      f"Crime volume spans {len(data)} months; the trend series is plotted below "
                      f"(peak: {max(data, key=lambda x: x['value'])['label'] if data else 'n/a'}).",
                      "SELECT strftime('%Y-%m', occurrence_date) m, COUNT(*) FROM cases GROUP BY m ORDER BY m;",
                      [{"table": "cases", "detail": f"{d['label']}: {d['value']}"} for d in data[-6:]],
                      data={"chart": "line", "series": data})

    if any(w in t for w in ["hotspot", "hot spot", "which district", "which area", "top district", "where"]):
        q = db.query(m.Case.district, func.count(m.Case.id))
        if crime:
            q = q.filter(m.Case.crime_type == crime)
        rows = q.group_by(m.Case.district).order_by(func.count(m.Case.id).desc()).limit(6).all()
        data = [{"label": r[0], "value": r[1]} for r in rows]
        top = ", ".join(f"{r[0]} ({r[1]})" for r in rows[:3])
        return _reply("hotspots", question, lang,
                      f"Top crime hotspots{f' for {crime}' if crime else ''}: {top}.",
                      f"SELECT district, COUNT(*) FROM cases {'WHERE crime_type=:c ' if crime else ''}"
                      "GROUP BY district ORDER BY 2 DESC LIMIT 6;",
                      [{"table": "cases", "detail": f"{r[0]}: {r[1]} cases"} for r in rows],
                      data={"chart": "bar", "series": data})

    if any(w in t for w in ["repeat offender", "habitual", "high risk", "high-risk", "risk score",
                            "top offender", "dangerous", "wanted"]):
        rows = (db.query(m.Accused, m.BehaviorProfile)
                .join(m.BehaviorProfile, m.BehaviorProfile.accused_id == m.Accused.id)
                .order_by(m.BehaviorProfile.risk_score.desc()).limit(8).all())
        ev = [{"table": "accused", "detail":
               f"{a.full_name} — risk {p.risk_score:.0f} ({p.risk_band}), "
               f"{a.previous_convictions} priors, tags: {p.propensity_tags}"}
              for a, p in rows]
        top = "; ".join(f"{a.full_name} (risk {p.risk_score:.0f}, {p.risk_band})" for a, p in rows[:5])
        return _reply("repeat_offenders", question, lang,
                      f"Highest-risk offenders: {top}.",
                      "SELECT a.full_name, b.risk_score FROM accused a JOIN behavior_profiles b "
                      "ON b.accused_id=a.id ORDER BY b.risk_score DESC LIMIT 8;",
                      ev, data={"chart": "table", "rows": [
                          {"name": a.full_name, "risk": round(p.risk_score), "band": p.risk_band,
                           "priors": a.previous_convictions, "district": a.district} for a, p in rows]})

    fir = re.search(r"fir[\/\s]*([\w\/\-]+)", t)
    if "fir" in t and fir:
        token = fir.group(1)
        case = db.query(m.Case).filter(m.Case.fir_number.ilike(f"%{token}%")).first()
        if case:
            return _reply("case_lookup", question, lang, _describe_case(db, case),
                          f"SELECT * FROM cases WHERE fir_number LIKE '%{token}%';",
                          [{"table": "cases", "detail": f"{case.fir_number}: {case.title}"}],
                          data={"case": _case_dict(db, case)})

    if any(w in t for w in ["who is", "profile of", "accused named", "person named", "details of"]):
        name = re.sub(r".*(who is|profile of|accused named|person named|details of)\s*", "", t).strip(" ?")
        if name:
            a = db.query(m.Accused).filter(m.Accused.full_name.ilike(f"%{name}%")).first()
            if a:
                return _reply("accused_lookup", question, lang, _describe_accused(db, a),
                              f"SELECT * FROM accused WHERE full_name LIKE '%{name}%';",
                              [{"table": "accused", "detail": f"{a.full_name}, {a.district}"}],
                              data={"accused_id": a.id})

    if any(w in t for w in ["money", "transaction", "financial", "money trail", "fund", "laundering", "account"]):
        total = db.query(func.count(m.Transaction.id)).scalar() or 0
        flagged = db.query(func.count(m.Transaction.id)).filter(m.Transaction.flagged.is_(True)).scalar() or 0
        loss = db.query(func.sum(m.Case.loss_amount)).filter(m.Case.is_financial.is_(True)).scalar() or 0
        return _reply("financial", question, lang,
                      f"There are {total} tracked transactions, {flagged} flagged as suspicious, "
                      f"across financial cases totalling ₹{loss:,.0f} in reported loss. "
                      "Open the Financial module for the full money-trail graph.",
                      "SELECT COUNT(*), SUM(flagged) FROM transactions;",
                      [{"table": "transactions", "detail": f"{flagged} flagged of {total}"}],
                      data={"total": total, "flagged": flagged, "loss": loss})

    if any(w in t for w in ["network", "gang", "association", "connected", "syndicate", "linked"]):
        gangs = (db.query(m.Association.gang_name, func.count(m.Association.id))
                 .filter(m.Association.gang_name.isnot(None))
                 .group_by(m.Association.gang_name).order_by(func.count(m.Association.id).desc()).all())
        top = ", ".join(f"{g[0]} ({g[1]} links)" for g in gangs[:5])
        edges = db.query(func.count(m.Association.id)).scalar()
        return _reply("network", question, lang,
                      f"The network holds {edges} associations. Most active groups: {top}. "
                      "Open the Network module to explore the interactive graph.",
                      "SELECT gang_name, COUNT(*) FROM associations GROUP BY gang_name ORDER BY 2 DESC;",
                      [{"table": "associations", "detail": f"{g[0]}: {g[1]} links"} for g in gangs],
                      data={"gangs": [{"label": g[0], "value": g[1]} for g in gangs]})

    if any(w in t for w in ["forecast", "predict", "will happen", "next week", "early warning", "future", "likely"]):
        preds = db.query(m.Prediction).order_by(m.Prediction.probability.desc()).limit(6).all()
        ev = [{"table": "predictions", "detail":
               f"{p.crime_type} in {p.target_area} — {p.probability*100:.0f}% ({p.risk_level})"}
              for p in preds]
        top = "; ".join(f"{p.crime_type} in {p.target_area} ({p.probability*100:.0f}%)" for p in preds[:4])
        return _reply("forecast", question, lang,
                      f"Top predicted risks for the coming window: {top}.",
                      "SELECT * FROM predictions ORDER BY probability DESC LIMIT 6;",
                      ev, data={"predictions": [
                          {"area": p.target_area, "crime": p.crime_type,
                           "prob": p.probability, "level": p.risk_level} for p in preds]})

    if any(w in t for w in ["age", "gender", "demographic", "socio", "education", "occupation", "urban", "rural"]):
        gender = (db.query(m.Accused.gender, func.count(m.Accused.id))
                  .group_by(m.Accused.gender).all())
        ses = (db.query(m.Accused.socio_economic, func.count(m.Accused.id))
               .group_by(m.Accused.socio_economic).all())
        gtxt = ", ".join(f"{g[0]}: {g[1]}" for g in gender)
        stxt = ", ".join(f"{s[0]}: {s[1]}" for s in ses)
        return _reply("socio", question, lang,
                      f"Accused gender split — {gtxt}. Socio-economic distribution — {stxt}. "
                      "See the Sociological Insights module for age bands and risk factors.",
                      "SELECT gender, COUNT(*) FROM accused GROUP BY gender;",
                      [{"table": "accused", "detail": f"gender {gtxt}"},
                       {"table": "accused", "detail": f"SES {stxt}"}],
                      data={"gender": [{"label": g[0], "value": g[1]} for g in gender],
                            "ses": [{"label": s[0], "value": s[1]} for s in ses]})

    if any(w in t for w in ["how many", "count", "number of", "total"]) or crime or district:
        n = base_filter(db.query(func.count(m.Case.id))).scalar() or 0
        return _reply("count_cases", question, lang,
                      f"There are {n} case(s) matching {filters_desc}.",
                      f"SELECT COUNT(*) FROM cases WHERE {_sql_where(crime, district, status, year) or '1=1'};",
                      [{"table": "cases", "detail": f"{n} cases for {filters_desc}"}],
                      data={"count": n, "filters": filters_desc})

    if any(w in t for w in ["show", "list", "cases", "fir"]):
        cases = base_filter(db.query(m.Case)).order_by(m.Case.occurrence_date.desc()).limit(10).all()
        ev = [{"table": "cases", "detail": f"{c.fir_number} — {c.title} [{c.status}]"} for c in cases]
        return _reply("list_cases", question, lang,
                      f"Showing {len(cases)} recent case(s) for {filters_desc}.",
                      f"SELECT * FROM cases WHERE {_sql_where(crime, district, status, year) or '1=1'} "
                      "ORDER BY occurrence_date DESC LIMIT 10;",
                      ev, data={"cases": [_case_dict(db, c) for c in cases]})

    return _reply("unknown", question, lang,
                  "I couldn't map that to the crime database. Try asking about case counts, "
                  "crime trends, hotspots, offenders, networks, money trails or forecasts.",
                  "-- no matching query", [])


# ── helpers ───────────────────────────────────────────────────────────

def _sql_where(crime, district, status, year):
    parts = []
    if crime: parts.append(f"crime_type='{crime}'")
    if district: parts.append(f"district='{district}'")
    if status: parts.append(f"status='{status}'")
    if year: parts.append(f"strftime('%Y',occurrence_date)='{year}'")
    return " AND ".join(parts)


def _case_dict(db, c: m.Case):
    accused = [ca.accused.full_name for ca in c.accused_links]
    return {"id": c.id, "fir_number": c.fir_number, "title": c.title, "crime_type": c.crime_type,
            "status": c.status, "severity": c.severity, "district": c.district,
            "occurrence_date": c.occurrence_date.isoformat() if c.occurrence_date else None,
            "loss_amount": c.loss_amount, "accused": accused}


def _describe_case(db, c: m.Case):
    accused = [ca.accused.full_name for ca in c.accused_links]
    inv = c.investigation
    off = inv.officer.name if inv and inv.officer else "unassigned"
    return (f"{c.fir_number}: {c.title}. Crime type: {c.crime_type} ({c.severity} severity), "
            f"status {c.status}, district {c.district}. "
            f"Occurred {c.occurrence_date.date() if c.occurrence_date else 'n/a'}. "
            f"Accused: {', '.join(accused) if accused else 'none recorded'}. "
            f"Investigating officer: {off}.")


def _describe_accused(db, a: m.Accused):
    p = a.profile
    n_cases = len(a.case_links)
    risk = f"risk {p.risk_score:.0f} ({p.risk_band})" if p else "no risk profile"
    return (f"{a.full_name}, {a.age}/{a.gender}, from {a.district}. Status: {a.status}. "
            f"{a.previous_convictions} prior conviction(s), linked to {n_cases} case(s). "
            f"Occupation: {a.occupation}, education: {a.education}, socio-economic: {a.socio_economic}. "
            f"Profile: {risk}"
            + (f", traits: {p.behavioral_traits}." if p else "."))


PROVENANCE = {
    "count_cases": ("DATABASE_FACT", "High"),
    "list_cases": ("DATABASE_FACT", "High"),
    "top_crime_types": ("DATABASE_FACT", "High"),
    "hotspots": ("DATABASE_FACT", "High"),
    "case_lookup": ("DATABASE_FACT", "High"),
    "accused_lookup": ("DATABASE_FACT", "High"),
    "network": ("DATABASE_FACT", "High"),
    "financial": ("DATABASE_FACT", "High"),
    "socio": ("DATABASE_FACT", "High"),
    "crime_trend": ("COMPUTED_FINDING", "High"),
    "repeat_offenders": ("COMPUTED_FINDING", "Medium"),
    "forecast": ("MODEL_PREDICTION", "Medium"),
    "help": ("NONE", "N/A"),
    "unknown": ("NONE", "N/A"),
}


def _reason_steps(intent, sql, evidence, provenance):
    tables = sorted({e.get("table") for e in evidence if e.get("table")})
    if not tables and sql:
        tables = sorted(set(re.findall(r"(?:FROM|JOIN)\s+(\w+)", sql)))
    return [
        {"step": "Understand", "detail": f"Classified intent as '{intent}'", "icon": "brain"},
        {"step": "Retrieve", "detail": "Queried " + (", ".join(tables) if tables else "database"), "icon": "database"},
        {"step": "Ground", "detail": f"{len(evidence)} evidence record(s) found", "icon": "search"},
        {"step": "Classify", "detail": f"Provenance: {provenance}", "icon": "shield"},
        {"step": "Answer", "detail": "Composed grounded response", "icon": "message"},
    ]


def _reply(intent, question, lang, answer, sql, evidence, data=None, llm=None):
    if llm is None:
        llm = get_llm()
    narrated = answer if llm.provider == "catalyst" else llm.narrate(question, answer, lang)
    provenance, confidence = PROVENANCE.get(intent, ("DATABASE_FACT", "Medium"))
    for e in evidence:
        e.setdefault("provenance", provenance)
    grounded = bool(evidence) and provenance != "NONE"
    grounding = {
        "status": "GROUNDED" if grounded else "UNGROUNDED",
        "provenance": provenance,
        "confidence": confidence,
        "source_count": len(evidence),
        "note": ("Answer is backed by database evidence; no fabricated facts."
                 if grounded else
                 "Informational response — not a data claim."),
    }
    return {"intent": intent, "answer": narrated, "sql": sql,
            "evidence": evidence, "data": data or {}, "language": lang,
            "provider": llm.provider, "grounding": grounding,
            "reasoning": _reason_steps(intent, sql, evidence, provenance)}
