import re


class PIIMasker:
    def mask_accused_name(self, name: str) -> str:
        if not name:
            return name
        parts = name.split()
        if len(parts) == 1:
            return parts[0][0] + "***"
        return parts[0] + " " + parts[-1][0] + "***"

    def mask_pii_in_results(self, rows: list[list], columns: list[str],
                            mask_columns: list[str]) -> list[list]:
        mask_indices = [columns.index(c) for c in mask_columns if c in columns]
        if not mask_indices:
            return rows
        masked = []
        for row in rows:
            new_row = list(row)
            for idx in mask_indices:
                if idx < len(new_row) and isinstance(new_row[idx], str):
                    new_row[idx] = self.mask_accused_name(new_row[idx])
            masked.append(new_row)
        return masked
