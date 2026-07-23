"""Financial-crime & transaction-link analysis."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models as m

router = APIRouter(prefix="/api/financial", tags=["financial"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
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
def money_graph(db: Session = Depends(get_db), only_flagged: bool = False, limit: int = 200):
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
def suspicious_accounts(db: Session = Depends(get_db)):
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
