"""Entity resolution across the Accused table (Part E.3 + B + E.5).

Two algorithm strategies exposed behind one contract so a future ML resolver
can be added without touching callers (OCP). All bulk work runs in the cron
function via :func:`EntityResolver.compute_all_and_store`.

LSP: every strategy returns a list of dicts with the same canonical keys:
``{canonical_name, aliases, case_ids, score}``.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Iterable, Optional

from common.db.datastore_client import DatastoreClient
from common.repositories.interfaces import AccusedRepository, PrecomputedStore
from common.repositories.zcql_impl import ZCQLAccusedRepository, CatalystRowPrecomputedStore

logger = logging.getLogger(__name__)


class EntityResolutionStrategy(ABC):
    name: str = "EntityResolutionStrategy"

    @abstractmethod
    def resolve(self, rows: Iterable[dict], threshold: float = 0.85) -> list[dict]:
        """Group suspect aliases. Returns canonical groups with ``aliases``."""


class FuzzyEntityResolutionStrategy(EntityResolutionStrategy):
    """Pure-Python fallback — uses rapidfuzz when present, else simple normalization."""

    name = "Fuzzy v1"

    def resolve(self, rows: Iterable[dict], threshold: float = 0.85) -> list[dict]:
        try:
            from rapidfuzz import fuzz  # type: ignore
            sim = lambda a, b: fuzz.token_set_ratio(a, b) / 100.0
        except ImportError:
            sim = _fallback_sim

        # Greedy union-find clustering keyed by first alias of each group.
        groups: list[dict] = []
        rep_of: dict[str, int] = {}
        for row in rows:
            name = _norm(str(row.get("AccusedName", "")))
            if not name:
                continue
            cm = row.get("CaseMasterID")
            matched = -1
            for i, g in enumerate(groups):
                rep = g["canonical_name"]
                if sim(name, rep) >= threshold:
                    matched = i
                    break
            if matched == -1:
                groups.append({
                    "canonical_name": name,
                    "aliases": {name},
                    "case_ids": {cm} if cm is not None else set(),
                    "count": 1,
                    "score": 1.0,
                })
            else:
                g = groups[matched]
                g["aliases"].add(name)
                if cm is not None:
                    g["case_ids"].add(cm)
                g["count"] = len(g["aliases"])
                g["score"] = round(_avg_sim(g["aliases"], sim), 3)
        return _serialize_groups(groups)


def _norm(s: str) -> str:
    return " ".join(s.strip().lower().split())


def _fallback_sim(a: str, b: str) -> float:
    """Cheap Levenshtein-ish similarity so the strategy works without rapidfuzz."""
    if not a or not b:
        return 0.0
    a_set = set(a.split())
    b_set = set(b.split())
    if not a_set or not b_set:
        return 0.0
    inter = len(a_set & b_set)
    union = len(a_set | b_set)
    return inter / union


def _avg_sim(aliases: Iterable[str], sim) -> float:
    aliases = list(aliases)
    if len(aliases) < 2:
        return 1.0
    total = 0.0
    pairs = 0
    for i in range(len(aliases)):
        for j in range(i + 1, len(aliases)):
            total += sim(aliases[i], aliases[j])
            pairs += 1
    return total / pairs if pairs else 1.0


def _serialize_groups(groups: list[dict]) -> list[dict]:
    out = []
    for g in groups:
        out.append({
            "canonical_name": g["canonical_name"],
            "aliases": sorted(g["aliases"]),
            "case_ids": sorted(c for c in g["case_ids"] if c is not None),
            "count": g["count"],
            "score": g["score"],
        })
    return out


def build_entity_resolver() -> "EntityResolver":
    return EntityResolver(FuzzyEntityResolutionStrategy())


class EntityResolver:
    def __init__(self, strategy: EntityResolutionStrategy):
        self.strategy = strategy

    @property
    def strategy_name(self) -> str:
        return self.strategy.name

    def resolve_batch(self, rows: list[dict], threshold: float = 0.85) -> list[dict]:
        return self.strategy.resolve(rows, threshold)

    def compute_all_and_store(self, catalyst_app) -> dict:
        db = DatastoreClient(catalyst_app)
        repo = ZCQLAccusedRepository(db)
        store = CatalystRowPrecomputedStore(db)

        rows = repo.fetch_all(limit=10000)
        if not rows:
            return {"status": "skipped", "reason": "empty table"}
        groups = self.strategy.resolve(rows)
        payload = {
            "computed_at": datetime.utcnow().isoformat() + "Z",
            "strategy": self.strategy.name,
            "groups": groups,
            "total_groups": len(groups),
        }
        store.save_entity_resolution(payload)
        return {"status": "ok", "groups": len(groups)}

    def load_all_precomputed(self) -> Optional[dict]:
        # Inline so a serve-side caller doesn't need to inject the store.
        return self._load_fn() if hasattr(self, "_load_fn") else None
