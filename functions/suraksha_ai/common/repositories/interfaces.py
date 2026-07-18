"""Storage abstractions (Part E.5 Dependency Inversion, Part F Information Expert).

Business logic (analyzers, scorer, entity resolver) depends ONLY on these
interfaces. Concrete ZCQL-backed and InMemory-backed implementations live one
module down — swap them in production vs. tests, never modify business logic
when the Catalyst SDK changes.
"""
from abc import ABC, abstractmethod
from typing import Iterable, Optional


class CaseRepository(ABC):
    """Reads case rows + the catalog tables they reference."""

    @abstractmethod
    def fetch_dates_in_window(
        self,
        station_ids: Iterable[int],
        crime_sub_head_ids: Optional[Iterable[int]],
        date_from: Optional[str],
        date_to: Optional[str],
        limit: int = 5000,
    ) -> list[dict]:
        """Return ``[{CrimeRegisteredDate: 'YYYY-MM-DD', ROWID: '123'}, ...]``."""

    @abstractmethod
    def fetch_geo_points(
        self,
        station_ids: Iterable[int],
        crime_sub_head_ids: Optional[Iterable[int]],
        date_from: Optional[str],
        date_to: Optional[str],
        limit: int = 10000,
    ) -> list[dict]:
        """Return ``[{latitude, longitude, CaseMasterID, CaseCategoryID}, ...]``."""

    @abstractmethod
    def station_ids_for_districts(self, district_ids: Iterable[int]) -> list[int]:
        """Map DistrictID list to UnitID list (``PoliceStationID``)."""

    @abstractmethod
    def station_ids_for_district(self, district_id: int) -> list[int]:
        """Single-district variant for hotspot detection."""


class AccusedRepository(ABC):
    """Reads offender / accused rows for entity resolution + profiling."""

    @abstractmethod
    def fetch_all(self, limit: int = 10000) -> list[dict]:
        """Return every accused row. Used by the cron-side entity resolver."""

    @abstractmethod
    def fetch_by_name(self, accused_name: str, limit: int = 1000) -> list[dict]:
        """Return rows for one canonical name (exact match on AccusedName)."""

    @abstractmethod
    def fetch_cases(self, case_master_ids: Iterable[int], limit: int = 1000) -> list[dict]:
        """Fan-out lookup for CaseMaster rows by IDs (ZCQL has no JOIN)."""

    @abstractmethod
    def fetch_crime_sub_heads(self, sub_head_ids: Iterable[int], limit: int = 1000) -> list[dict]:
        """Resolve CrimeSubHead → CrimeHeadName for a batch of IDs."""

    @abstractmethod
    def fetch_case_statuses(self, status_ids: Iterable[int], limit: int = 1000) -> list[dict]:
        """Resolve CaseStatusMaster lookup by IDs."""


class PrecomputedStore(ABC):
    """Read/write precomputed artifacts (Part B compute/serve split).

    The cron function writes here; the 30 s serve function reads from here.
    """

    @abstractmethod
    def save_trends(self, payload: dict) -> bool: ...

    @abstractmethod
    def load_trends(self) -> Optional[dict]: ...

    @abstractmethod
    def save_hotspots(self, payload: dict) -> bool: ...

    @abstractmethod
    def load_hotspots(self) -> Optional[dict]: ...

    @abstractmethod
    def save_forecast(self, district_id: int, crime_sub_head_id: int, payload: dict) -> bool: ...

    @abstractmethod
    def load_forecast(self, district_id: int, crime_sub_head_id: int) -> Optional[dict]: ...

    @abstractmethod
    def save_entity_resolution(self, payload: dict) -> bool: ...

    @abstractmethod
    def load_entity_resolution(self) -> Optional[dict]: ...

    @abstractmethod
    def save_ips_scores(self, payload: dict) -> bool: ...

    @abstractmethod
    def load_ips_scores(self) -> Optional[dict]: ...
