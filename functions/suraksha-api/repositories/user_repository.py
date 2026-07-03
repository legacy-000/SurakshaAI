from sqlalchemy.orm import Session
from models.user import User
from .base import BaseRepository

class UserRepository(BaseRepository[User]):
    """
    Repository for handling database actions related to User accounts.
    """
    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> User | None:
        # Placeholder for querying by username
        return self.db.query(self.model).filter(self.model.username == username).first()

    def get_by_email(self, email: str) -> User | None:
        # Placeholder for querying by email
        return self.db.query(self.model).filter(self.model.email == email).first()
