from sqlalchemy import JSON, Column, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class TaskState(Base):
    __tablename__ = "task_state"

    user_id = Column(String, primary_key=True, index=True)
    kwargs_json = Column(JSON, nullable=False, default={})
    factory_tag = Column(String, nullable=True, index=True)