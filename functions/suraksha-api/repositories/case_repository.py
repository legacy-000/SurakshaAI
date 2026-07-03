from sqlalchemy.orm import Session
from models.case import Case
from .base import BaseRepository

class CaseRepository(BaseRepository[Case]):
    """
    Repository for handling database actions related to Case entities.
    """
    def __init__(self, db: Session):
        super().__init__(Case, db)

    def get_by_fir_number(self, fir_number: str) -> Case | None:
        return self.db.query(self.model).filter(self.model.fir_number == fir_number).first()
