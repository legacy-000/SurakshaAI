import pandas as pd
import random
from datetime import datetime, timedelta


class ForecastDataBuilder:
    def build_daily_counts(self, district_id: int, crime_sub_head_id: int,
                           training_window_days: int = 365) -> pd.DataFrame:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=training_window_days)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        base = random.randint(1, 5)
        data = []
        for d in dates:
            count = max(0, int(base + random.gauss(0, 2) + 3 * (1 + (d.month % 12) / 12)))
            data.append({"ds": d, "y": count})

        return pd.DataFrame(data)
