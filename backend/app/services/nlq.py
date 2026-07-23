"""Natural-language query engine (rule-based, works with zero API keys).

Parses an English or Kannada question into an intent + entities, runs the
matching ORM query, and returns:
  - answer   : natural-language reply
  - sql       : an illustrative SQL trace (explainability)
  - evidence  : list of evidence rows / reasoning (explainable AI)
  - data      : optional structured payload the UI can render (chart/table)
  - intent    : the detected intent

When a real LLM provider is configured it is used to rephrase `answer`;
otherwise the deterministic text below is returned verbatim.
"""
from __future__ import annotations

import re
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from .. import models as m
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
    # Kannada
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


def _extract(text: str):
    t = text.lower()
    crime = None
    for key, val in CRIME_LEXICON.items():
        if key in t or key in text:  # Kannada keys are case-sensitive
            crime = val
            break
    district = next((d for d in DISTRICTS if d.lower() in t), None)
    if not district:  # loose match on first word of district
        district = next((d for d in DISTRICTS if d.split()[0].lower() in t), None)
    status = next((v for k, v in STATUS_WORDS.items() if k in t), None)
    ymatch = re.search(r"\b(20\d{2})\b", t)
    year = int(ymatch.group(1)) if ymatch else None
    return crime, district, status, year


def _detect_lang(text: str) -> str:
    return "kn" if re.search(r"[ಀ-೿]", text) else "en"


def answer_question(db: Session, question: str, language: str | None = None) -> dict:
    lang = language or _detect_lang(question)
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

    # ── Intent routing ────────────────────────────────────────────────
    # greeting / help
    if any(w in t for w in ["hello", "hi ", "help", "what can you", "namaste", "ನಮಸ್ಕಾರ"]):
        return _reply(
            intent="help", question=question, lang=lang,
            answer=("I can answer questions about FIRs, accused, victims, crime trends, "
                    "hotspots, offender risk, criminal networks, money trails and forecasts. "
                    "Try: 'How many cyber fraud cases in Bengaluru City?', "
                    "'Show crime trend', 'Top repeat offenders', 'Show hotspots'."),
            sql="-- no query (informational)", evidence=[])

    # top crime types
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

    # crime trend over time
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

    # hotspots
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

    # repeat / high-risk offenders
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

    # FIR lookup
    fir = re.search(r"fir[\/\s]*([\w\/\-]+)", t)
    if "fir" in t and fir:
        token = fir.group(1)
        case = db.query(m.Case).filter(m.Case.fir_number.ilike(f"%{token}%")).first()
        if case:
            return _reply("case_lookup", question, lang, _describe_case(db, case),
                          f"SELECT * FROM cases WHERE fir_number LIKE '%{token}%';",
                          [{"table": "cases", "detail": f"{case.fir_number}: {case.title}"}],
                          data={"case": _case_dict(db, case)})

    # accused lookup by name
    if any(w in t for w in ["who is", "profile of", "accused named", "person named", "details of"]):
        name = re.sub(r".*(who is|profile of|accused named|person named|details of)\s*", "", t).strip(" ?")
        if name:
            a = db.query(m.Accused).filter(m.Accused.full_name.ilike(f"%{name}%")).first()
            if a:
                return _reply("accused_lookup", question, lang, _describe_accused(db, a),
                              f"SELECT * FROM accused WHERE full_name LIKE '%{name}%';",
                              [{"table": "accused", "detail": f"{a.full_name}, {a.district}"}],
                              data={"accused_id": a.id})

    # money trail / financial
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

    # network / gang
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

    # forecast / prediction
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

    # socio-demographic
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

    # count cases (default catch for "how many")
    if any(w in t for w in ["how many", "count", "number of", "total"]) or crime or district:
        n = base_filter(db.query(func.count(m.Case.id))).scalar() or 0
        return _reply("count_cases", question, lang,
                      f"There are {n} case(s) matching {filters_desc}.",
                      f"SELECT COUNT(*) FROM cases WHERE {_sql_where(crime, district, status, year) or '1=1'};",
                      [{"table": "cases", "detail": f"{n} cases for {filters_desc}"}],
                      data={"count": n, "filters": filters_desc})

    # list cases fallback
    if any(w in t for w in ["show", "list", "cases", "fir"]):
        cases = base_filter(db.query(m.Case)).order_by(m.Case.occurrence_date.desc()).limit(10).all()
        ev = [{"table": "cases", "detail": f"{c.fir_number} — {c.title} [{c.status}]"} for c in cases]
        return _reply("list_cases", question, lang,
                      f"Showing {len(cases)} recent case(s) for {filters_desc}.",
                      f"SELECT * FROM cases WHERE {_sql_where(crime, district, status, year) or '1=1'} "
                      "ORDER BY occurrence_date DESC LIMIT 10;",
                      ev, data={"cases": [_case_dict(db, c) for c in cases]})

    # unknown
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


# Claim-Ledger provenance classification per intent (Explainable-AI layer).
#   DATABASE_FACT    — read directly from authoritative tables
#   COMPUTED_FINDING — deterministically derived (aggregation / scoring)
#   MODEL_PREDICTION — inferred by a forecasting model (carries confidence)
#   MODEL_HYPOTHESIS — speculative lead, unproven
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
    """Build a visual reasoning trace (Explainable-AI: 'visualize reasoning paths')."""
    # source tables from evidence + SQL
    tables = sorted({e.get("table") for e in evidence if e.get("table")})
    if not tables and sql:
        tables = sorted(set(re.findall(r"(?:FROM|JOIN)\s+(\w+)", sql)))
    steps = [
        {"step": "Understand", "detail": f"Classified intent as '{intent}'", "icon": "brain"},
        {"step": "Retrieve", "detail": "Queried " + (", ".join(tables) if tables else "database"), "icon": "database"},
        {"step": "Ground", "detail": f"{len(evidence)} evidence record(s) found", "icon": "search"},
        {"step": "Classify", "detail": f"Provenance: {provenance}", "icon": "shield"},
        {"step": "Answer", "detail": "Composed grounded response", "icon": "message"},
    ]
    return steps


def _reply(intent, question, lang, answer, sql, evidence, data=None):
    llm = get_llm()
    narrated = llm.narrate(question, answer, lang)
    provenance, confidence = PROVENANCE.get(intent, ("DATABASE_FACT", "Medium"))
    # tag every evidence row with its provenance class (Claim Ledger)
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
