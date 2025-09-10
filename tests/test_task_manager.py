import asyncio
import logging

import pytest

from task_manager.base import TaskManager
from task_manager.storage import SQLiteStorage
from task_manager.types import ClientProtocol
from task_manager.utils import factory_tag  # assuming you put factory_tag in utils.py

# Use an in-memory SQLite database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

# Silence logs during test runs
logging.basicConfig(level=logging.CRITICAL)


class FakeClient(ClientProtocol):
    def __init__(self, user_id: str, **kwargs):
        self.user_id = user_id
        self.kwargs = kwargs
        self.connected = False
        self.disconnected = False

    async def connect(self):
        await asyncio.sleep(0.01)  # simulate async work
        self.connected = True

    async def disconnect(self):
        await asyncio.sleep(0.01)
        self.disconnected = True


@pytest.mark.asyncio
async def test_start_and_stop_task():
    storage = SQLiteStorage(TEST_DB_URL)
    manager = TaskManager(storage)

    # Ensure DB schema
    if hasattr(storage, "ensure_tables"):
        await storage.ensure_tables()

    # Start task
    await manager.start("u1", FakeClient, foo="bar")

    # Wait until client is connected (or timeout)
    async def wait_connected(client, timeout=1.0):
        import time
        start = time.time()
        while not client.connected:
            await asyncio.sleep(0.01)
            if time.time() - start > timeout:
                break

    await wait_connected(manager.clients["u1"])
    assert manager.clients["u1"].connected
    assert manager.is_running("u1")
    assert "u1" in manager.clients
    assert manager.clients["u1"].connected

    # Stop task
    await manager.stop("u1")
    assert not manager.is_running("u1")
    assert "u1" not in manager.clients


@pytest.mark.asyncio
async def test_persist_and_restore():
    storage = SQLiteStorage(TEST_DB_URL)
    manager1 = TaskManager(storage)

    if hasattr(storage, "ensure_tables"):
        await storage.ensure_tables()

    # Start and persist
    await manager1.start("u2", FakeClient, alpha=123)

    
    await manager1.shutdown()

    # New TaskManager should restore from DB
    manager2 = TaskManager(storage)
    await manager2.restore_all(FakeClient)

    assert manager2.is_running("u2")
    client = manager2.clients["u2"]
    assert isinstance(client, FakeClient)
    assert client.kwargs["alpha"] == 123


@pytest.mark.asyncio
async def test_factory_tag_changes_on_class_name_change():
    tag1 = factory_tag(FakeClient)

    # Define a new class with different name
    class FakeClientV2(FakeClient):
        pass

    tag2 = factory_tag(FakeClientV2)
    assert tag1 != tag2  # changing class name changes tag
