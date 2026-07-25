"""Export historical crime data as CSV for QuickML Prophet training.

Usage:
    cd newcrime/backend
    python -m app.export_training_data

Output: training_data.csv with columns: date, crime_type, district, case_count
Aggregated from cases table by month x crime_type x district.
"""
import csv
from collections import Counter
from datetime import datetime

from .database import SessionLocal
from . import models as m


def _load_cases() -> list[tuple]:
    """(occurrence_date, crime_type, district) from whichever store is live."""
    from .config import settings
    if settings.use_catalyst:
        from .catalyst_store import init_catalyst_store, get_store
        init_catalyst_store()
        rows = get_store().query("SELECT * FROM cases")
        return [(r.get("occurrence_date"), r.get("crime_type"), r.get("district"))
                for r in rows]
    db = SessionLocal()
    try:
        return [(c.occurrence_date, c.crime_type, c.district)
                for c in db.query(m.Case).all()]
    finally:
        db.close()


def export(grain: str = "district"):
    """Aggregate monthly case counts for Prophet.

    grain picks the series key. "crime_district" is what the deployment plan
    asked for, but with a few hundred cases it yields ~1 point per series,
    which Prophet cannot fit — prefer "district" or "crime" until the archive
    is much larger.
    """
    keys = {
        "district": lambda ct, d: (d,),
        "crime": lambda ct, d: (ct,),
        "crime_district": lambda ct, d: (ct, d),
        "total": lambda ct, d: (),
    }
    if grain not in keys:
        raise SystemExit(f"grain must be one of {sorted(keys)}")
    key_of = keys[grain]

    counts: Counter = Counter()
    for occurred, crime_type, district in _load_cases():
        if not occurred or not crime_type or not district:
            continue
        if isinstance(occurred, datetime):
            dt = occurred
        else:
            # Catalyst returns "YYYY-MM-DD HH:MM:SS"; only the month matters
            try:
                dt = datetime.fromisoformat(str(occurred).replace(" ", "T")[:19])
            except ValueError:
                continue
        counts[(dt.strftime("%Y-%m-01"),) + key_of(crime_type, district)] += 1

    headers = {"district": ["date", "district", "case_count"],
               "crime": ["date", "crime_type", "case_count"],
               "crime_district": ["date", "crime_type", "district", "case_count"],
               "total": ["date", "case_count"]}[grain]
    rows = sorted(counts.items())
    output_path = f"training_data_{grain}.csv"
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for key, count in rows:
            writer.writerow(list(key) + [count])

    series: Counter = Counter(k[1:] for k in counts)
    per = sorted(Counter(k[1:] for k in counts).values()) if series else [0]
    print(f"Exported {len(rows)} rows to {output_path}  (grain={grain})")
    if rows:
        print(f"  Months     : {rows[0][0][0]} .. {rows[-1][0][0]}")
        print(f"  Series     : {len(series)}")
        pts = sorted(Counter(k[1:] for k in counts).values())
        print(f"  Points/series: min={pts[0]} max={pts[-1]}")
        if pts[-1] < 6:
            print("  WARNING: too few points per series for Prophet to fit; "
                  "use a coarser grain.")


if __name__ == "__main__":
    import sys
    export(sys.argv[1] if len(sys.argv) > 1 else "district")
