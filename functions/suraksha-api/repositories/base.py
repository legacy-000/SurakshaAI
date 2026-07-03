from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy.orm import Session
from models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    """
    Standard base repository providing generic database interactions.
    Exposes simple CRUD helpers mapping to SQLAlchemy.
    """
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get(self, id: Any) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, obj_in: Any) -> ModelType:
        # Placeholder for object creation logic
        pass

    def update(self, db_obj: ModelType, obj_in: Any) -> ModelType:
        # Placeholder for object updates
        pass

    def remove(self, id: Any) -> Optional[ModelType]:
        # Placeholder for object deletion
        pass
