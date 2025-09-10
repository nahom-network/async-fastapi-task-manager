from typing import Any, Dict, List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .models import Base, TaskState
from .types import TaskStorage


class SQLStorageBase(TaskStorage):
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, future=True, echo=False)
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def ensure_tables(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def save(self, tasks: List[Dict[str, Any]]) -> None:
        """
        Save tasks in the format:
        [{"user_id": str, "kwargs": dict}, ...]
        """
        async with self.async_session() as session:
            # Clear previous data
            await session.execute(delete(TaskState))
            # Insert all tasks
            session.add_all([
            TaskState(user_id=t["user_id"], kwargs_json=t.get("kwargs") or {}, factory_tag=t.get("factory_tag"))
            for t in tasks
            ])
            await session.commit()

    async def load(self, *, factory_tag: Optional[str] = None) -> List[Dict[str, Any]]:
        async with self.async_session() as session:
            stmt = select(TaskState)
            if factory_tag is not None:
                stmt = stmt.where(TaskState.factory_tag == factory_tag)
            result = await session.execute(stmt)
            rows = result.scalars().all()
            return [
                {"user_id": r.user_id, "kwargs": r.kwargs_json or {}, "factory_tag": r.factory_tag}
                for r in rows
            ]

class SQLiteStorage(SQLStorageBase):
    pass

class PostgresStorage(SQLStorageBase):
    pass
