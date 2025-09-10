from .base import TaskManager
from .storage import SQLiteStorage
from .types import ClientProtocol, TaskStorage

__all__ = ["TaskManager", "SQLiteStorage", "TaskStorage", "ClientProtocol"]

def new(storage_url: str | None = None, storage: TaskStorage | None = None) -> TaskManager:
    """
    Factory to create a ready-to-use TaskManager.
    Users can either pass a storage object, or a database URL (SQLite by default).
    """
    if storage is None:
        if storage_url is None:
            storage_url = "sqlite+aiosqlite:///./task_manager.db"
        storage = SQLiteStorage(storage_url)
    return TaskManager(storage)
