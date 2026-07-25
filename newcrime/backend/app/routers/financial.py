"""Financial-crime & transaction-link analysis."""
from collections import Counter

from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from .. import models as m
from ..deps import get_ctx

router = APIRouter(prefix="/api/financial", tags=["financial"])


def _scope(ctx, store):
    """Case ids and suspicious-account ids inside the caller's territory.

    Neither transactions nor financial_accounts carry a district, so
    jurisdiction is derived through the two links that exist:
      transaction -> case -> district
      account     -> accused -> district

    Transactions are scoped by their CASE, not by account district: a money
    trail out of your own case legitimately crosses into other districts and
    is evidence you need. The standalone suspicious-account browse is scoped
    by accused district instead, since it isn't anchored to a case.

    Returns (case_ids, account_ids), or (None, None) for state-wide scope.
    """
    if ctx.scope == "state":
        return None, None
    allowed = set(ctx.districts_in_scope())
    case_ids = {c.get("ROWID") for c in store.query("SELECT * FROM cases")
                if c.get("district") in allowed}
    accused_ids = {a.get("ROWID") for a in store.query("SELECT * FROM accused")
                   if a.get("district") in allowed}
    # accounts with no accused link cannot be placed in a jurisdiction —
    # excluded rather than shown, consistent with fail-closed elsewhere
    account_ids = {a.get("ROWID") for a in store.query("SELECT * FROM financial_accounts")
                   if a.get("accused_id") in accused_ids}
    return case_ids, account_ids


@router.get("/summary")
def summary(request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        case_ids, account_ids = _scope(ctx, store)
        txns = store.query("SELECT * FROM transactions")
        if case_ids is not None:
            txns = [t for t in txns if t.get("case_id") in case_ids]
        total_txn = len(txns)
        flagged = sum(1 for t in txns if t.get("flagged"))
        volume = sum(float(t.get("amount", 0)) for t in txns)
        by_channel = Counter(t.get("channel") for t in txns)
        accs = store.query("SELECT * FROM financial_accounts WHERE is_suspicious = true")
        if account_ids is not None:
            accs = [a for a in accs if a.get("ROWID") in account_ids]
        suspicious_acc = len(accs)
        cases = ctx.scope_rows(store.query("SELECT * FROM cases WHERE is_financial = true"))
        loss = sum(float(c.get("loss_amount", 0)) for c in cases)
        return {"total_transactions": total_txn, "flagged": flagged, "volume": volume,
                "suspicious_accounts": suspicious_acc, "financial_loss": loss,
                "by_channel": [{"label": k, "value": v} for k, v in by_channel.items()]}

    total_txn = db.query(func.count(m.Transaction.id)).scalar() or 0
    flagged = db.query(func.count(m.Transaction.id)).filter(m.Transaction.flagged.is_(True)).scalar() or 0
    volume = db.query(func.sum(m.Transaction.amount)).scalar() or 0
    suspicious_acc = db.query(func.count(m.FinancialAccount.id)).filter(
        m.FinancialAccount.is_suspicious.is_(True)).scalar() or 0
    loss = db.query(func.sum(m.Case.loss_amount)).filter(m.Case.is_financial.is_(True)).scalar() or 0
    by_channel = (db.query(m.Transaction.channel, func.count(m.Transaction.id))
                  .group_by(m.Transaction.channel).all())
    return {"total_transactions": total_txn, "flagged": flagged, "volume": volume,
            "suspicious_accounts": suspicious_acc, "financial_loss": loss,
            "by_channel": [{"label": r[0], "value": r[1]} for r in by_channel]}


@router.get("/graph")
def money_graph(request: Request, db: Session = Depends(get_db),
                only_flagged: bool = False, limit: int = 200):
    ctx = get_ctx(request)
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        if only_flagged:
            txns = store.query("SELECT * FROM transactions WHERE flagged = true ORDER BY CREATEDTIME DESC")
        else:
            txns = store.query("SELECT * FROM transactions ORDER BY CREATEDTIME DESC")
        case_ids, _ = _scope(ctx, store)
        if case_ids is not None:
            # scope before the limit, or the page fills with other districts
            txns = [t for t in txns if t.get("case_id") in case_ids]
        txns = txns[:limit]
        acc_ids = {t.get("source_account_id") for t in txns} | {t.get("target_account_id") for t in txns}
        acc_ids.discard(None)
        all_accs = store.query("SELECT * FROM financial_accounts")
        acc_map = {a.get("ROWID"): a for a in all_accs}
        nodes = [{"id": a.get("ROWID"), "label": a.get("holder_name"), "bank": a.get("bank"),
                  "type": a.get("account_type"), "suspicious": a.get("is_suspicious"),
                  "account_number": a.get("account_number")}
                 for a in all_accs if a.get("ROWID") in acc_ids]
        edges = [{"source": t.get("source_account_id"), "target": t.get("target_account_id"),
                  "amount": t.get("amount"), "channel": t.get("channel"),
                  "flagged": t.get("flagged"), "case_id": t.get("case_id"),
                  "timestamp": t.get("transaction_timestamp") or t.get("CREATEDTIME")}
                 for t in txns]
        return {"nodes": nodes, "edges": edges}

    q = db.query(m.Transaction)
    if only_flagged:
        q = q.filter(m.Transaction.flagged.is_(True))
    txns = q.order_by(m.Transaction.txn_timestamp.desc()).limit(limit).all()
    acc_ids = {t.from_account_id for t in txns} | {t.to_account_id for t in txns}
    accounts = db.query(m.FinancialAccount).filter(m.FinancialAccount.id.in_(acc_ids)).all()
    nodes = [{"id": a.id, "label": a.holder_name, "bank": a.bank,
              "type": a.account_type, "suspicious": a.is_suspicious,
              "account_number": a.account_number} for a in accounts]
    edges = [{"source": t.from_account_id, "target": t.to_account_id,
              "amount": t.amount, "channel": t.channel, "flagged": t.flagged,
              "case_id": t.case_id,
              "timestamp": t.txn_timestamp.isoformat() if t.txn_timestamp else None}
             for t in txns]
    return {"nodes": nodes, "edges": edges}


@router.get("/suspicious-accounts")
def suspicious_accounts(request: Request, db: Session = Depends(get_db)):
    ctx = get_ctx(request)
    if settings.use_catalyst:
        from ..catalyst_store import get_store
        store = get_store()
        accs = store.query("SELECT * FROM financial_accounts WHERE is_suspicious = true")
        txns = store.query("SELECT * FROM transactions")
        case_ids, account_ids = _scope(ctx, store)
        if account_ids is not None:
            accs = [a for a in accs if a.get("ROWID") in account_ids]
            # inflow/outflow must not aggregate other districts' transactions
            txns = [t for t in txns if t.get("case_id") in case_ids]
        out = []
        for a in accs:
            aid = a.get("ROWID")
            inflow = sum(float(t.get("amount", 0)) for t in txns if t.get("target_account_id") == aid)
            outflow = sum(float(t.get("amount", 0)) for t in txns if t.get("source_account_id") == aid)
            txn_count = sum(1 for t in txns
                           if t.get("source_account_id") == aid or t.get("target_account_id") == aid)
            out.append({"id": aid, "holder": a.get("holder_name"), "bank": a.get("bank"),
                        "type": a.get("account_type"), "account_number": a.get("account_number"),
                        "inflow": inflow, "outflow": outflow, "transactions": txn_count})
        return sorted(out, key=lambda x: -(x["inflow"] + x["outflow"]))

    rows = db.query(m.FinancialAccount).filter(m.FinancialAccount.is_suspicious.is_(True)).all()
    out = []
    for a in rows:
        inflow = db.query(func.sum(m.Transaction.amount)).filter(
            m.Transaction.to_account_id == a.id).scalar() or 0
        outflow = db.query(func.sum(m.Transaction.amount)).filter(
            m.Transaction.from_account_id == a.id).scalar() or 0
        txn_count = db.query(func.count(m.Transaction.id)).filter(
            or_(m.Transaction.from_account_id == a.id,
                m.Transaction.to_account_id == a.id)).scalar() or 0
        out.append({"id": a.id, "holder": a.holder_name, "bank": a.bank,
                    "type": a.account_type, "account_number": a.account_number,
                    "inflow": inflow, "outflow": outflow, "transactions": txn_count})
    return sorted(out, key=lambda x: -(x["inflow"] + x["outflow"]))
