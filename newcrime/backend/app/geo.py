"""Geographic intelligence module for Karnataka State Police hierarchy.

Maps all 15 districts to their range, subdivisions, neighbors, and geo-coordinates.
Provides helpers for territory-based access control and cross-border analysis.
"""

from __future__ import annotations

KARNATAKA_DISTRICTS = {
    "Bengaluru City": {
        "range": "Bengaluru",
        "subdivisions": ["Bengaluru East", "Bengaluru West", "Bengaluru South", "Bengaluru North"],
        "neighbors": ["Bengaluru Rural", "Tumakuru", "Mandya"],
        "geo": (12.97, 77.59),
    },
    "Bengaluru Rural": {
        "range": "Bengaluru",
        "subdivisions": ["Devanahalli", "Hosakote", "Nelamangala", "Doddaballapura"],
        "neighbors": ["Bengaluru City", "Tumakuru", "Kalaburagi"],
        "geo": (13.23, 77.57),
    },
    "Mysuru": {
        "range": "Mysuru",
        "subdivisions": ["Mysuru North", "Mysuru South", "Nanjangud", "Hunsur"],
        "neighbors": ["Mandya", "Hassan", "Mangaluru"],
        "geo": (12.30, 76.64),
    },
    "Mangaluru": {
        "range": "Mangaluru",
        "subdivisions": ["Mangaluru North", "Mangaluru South", "Bantwal", "Puttur"],
        "neighbors": ["Udupi", "Hassan", "Mysuru"],
        "geo": (12.91, 74.86),
    },
    "Hubballi-Dharwad": {
        "range": "Belgaum",
        "subdivisions": ["Hubballi", "Dharwad", "Navalgund", "Kundgol"],
        "neighbors": ["Belagavi", "Davanagere", "Ballari", "Vijayapura"],
        "geo": (15.36, 75.12),
    },
    "Belagavi": {
        "range": "Belgaum",
        "subdivisions": ["Belagavi North", "Belagavi South", "Chikkodi", "Gokak"],
        "neighbors": ["Hubballi-Dharwad", "Vijayapura"],
        "geo": (15.85, 74.50),
    },
    "Kalaburagi": {
        "range": "North Eastern",
        "subdivisions": ["Kalaburagi North", "Kalaburagi South", "Aland", "Afzalpur"],
        "neighbors": ["Vijayapura", "Ballari", "Bengaluru Rural"],
        "geo": (17.33, 76.83),
    },
    "Ballari": {
        "range": "North Eastern",
        "subdivisions": ["Ballari City", "Ballari Rural", "Hospet", "Sandur"],
        "neighbors": ["Davanagere", "Kalaburagi", "Vijayapura", "Hubballi-Dharwad"],
        "geo": (15.14, 76.92),
    },
    "Vijayapura": {
        "range": "North Eastern",
        "subdivisions": ["Vijayapura North", "Vijayapura South", "Indi", "Muddebihal"],
        "neighbors": ["Belagavi", "Hubballi-Dharwad", "Ballari", "Kalaburagi"],
        "geo": (16.83, 75.71),
    },
    "Davanagere": {
        "range": "Central",
        "subdivisions": ["Davanagere City", "Davanagere Rural", "Harihar", "Jagalur"],
        "neighbors": ["Shivamogga", "Ballari", "Hubballi-Dharwad", "Tumakuru"],
        "geo": (14.47, 75.92),
    },
    "Shivamogga": {
        "range": "Central",
        "subdivisions": ["Shivamogga City", "Shivamogga Rural", "Bhadravati", "Sagar"],
        "neighbors": ["Davanagere", "Udupi", "Hassan"],
        "geo": (13.93, 75.57),
    },
    "Tumakuru": {
        "range": "Bengaluru",
        "subdivisions": ["Tumakuru City", "Tumakuru Rural", "Tiptur", "Madhugiri"],
        "neighbors": ["Bengaluru City", "Bengaluru Rural", "Hassan", "Davanagere"],
        "geo": (13.34, 77.10),
    },
    "Udupi": {
        "range": "Mangaluru",
        "subdivisions": ["Udupi Town", "Kundapura", "Karkala", "Brahmavar"],
        "neighbors": ["Mangaluru", "Shivamogga"],
        "geo": (13.34, 74.75),
    },
    "Hassan": {
        "range": "Mysuru",
        "subdivisions": ["Hassan Town", "Hassan Rural", "Arsikere", "Belur"],
        "neighbors": ["Tumakuru", "Mysuru", "Mangaluru", "Shivamogga"],
        "geo": (13.00, 76.10),
    },
    "Mandya": {
        "range": "Mysuru",
        "subdivisions": ["Mandya Town", "Mandya Rural", "Maddur", "Srirangapatna"],
        "neighbors": ["Bengaluru City", "Mysuru", "Hassan"],
        "geo": (12.52, 76.90),
    },
}


def get_neighbors(district: str) -> list[str]:
    """Return neighboring districts."""
    info = KARNATAKA_DISTRICTS.get(district)
    return info["neighbors"] if info else []


def get_range_districts(range_name: str) -> list[str]:
    """Return all districts in a range."""
    return [d for d, info in KARNATAKA_DISTRICTS.items() if info["range"] == range_name]


def get_subdivisions(district: str) -> list[str]:
    """Return subdivisions of a district."""
    info = KARNATAKA_DISTRICTS.get(district)
    return info["subdivisions"] if info else []


def get_district_for_subdivision(subdivision: str) -> str | None:
    """Find which district a subdivision belongs to."""
    for d, info in KARNATAKA_DISTRICTS.items():
        if subdivision in info["subdivisions"]:
            return d
    return None


def get_neighboring_subdivisions(subdivision: str) -> list[str]:
    """Return subdivisions in neighboring districts (for cross-border analysis)."""
    parent = get_district_for_subdivision(subdivision)
    if not parent:
        return []
    neighbors = get_neighbors(parent)
    result = []
    for n in neighbors:
        result.extend(get_subdivisions(n)[:2])  # first 2 from each neighbor
    return result


RANGES = sorted(set(info["range"] for info in KARNATAKA_DISTRICTS.values()))
