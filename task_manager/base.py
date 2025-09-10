import asyncio
import logging
from typing import Any, Callable, Dict, Optional

from task_manager.utils import factory_tag

from .types import ClientProtocol, TaskStorage

logger = logging.getLogger("task_manager")

class TaskManager:
    def __init__(self, storage: TaskStorage, *, persist_debounce_seconds: float = 0.5):
        self._tasks: Dict[str, asyncio.Task] = {}
        self._task_configs: Dict[str, Dict[str, Any]] = {}
        self._clients: Dict[str, object] = {}
        self._storage = storage
        self._persist_debounce_seconds = persist_debounce_seconds

        self._save_lock = asyncio.Lock()
        self._save_task: Optional[asyncio.Task] = None
        

    @property
    def clients(self) -> Dict[str, object]:
        """Read only access to all running client instances."""
        return dict(self._clients)
    
    @property
    def tasks(self) -> Dict[str, asyncio.Task]:
        """Read only access to all running tasks."""
        return dict(self._tasks)
    
    async def _persist_now(self) -> None:
        async with self._save_lock:
            
            await self._storage.save([
                {
                    "user_id": uid, 
                    "kwargs": self._task_configs.get(uid, {}),
                    "factory_tag": factory_tag(self._clients[uid].__class__)
                }
                for uid in self._tasks
            ])
            logger.debug("Persisted tasks to storage")
    def _schedule_persist(self) -> None:
        # Debounce writes to reduce DB churn
        if self._save_task and not self._save_task.done():
            return

        async def _delayed():
            try:
                await asyncio.sleep(self._persist_debounce_seconds)
                await self._persist_now()
            except asyncio.CancelledError:
                # on shutdown we may cancel this
                pass

        self._save_task = asyncio.create_task(_delayed())

    def is_running(self, user_id: str) -> bool:
        return user_id in self._tasks and not self._tasks[user_id].done()

    async def start(self, user_id: str, client_factory: Callable[..., object], **kwargs: Any):
        if self.is_running(user_id):
            logger.info(f"Task already running for user {user_id}")
            return

        client: ClientProtocol = client_factory(user_id=user_id, **kwargs)
        self._clients[user_id] = client
        self._task_configs[user_id] = kwargs

        async def _run():
            try:
                await client.connect()
            except asyncio.CancelledError:
                await client.disconnect()
                raise
            except Exception as e:
                logger.error(f"Error _run: {e}")
            finally:
                # if connect returns (finished), ensure cleanup
                await client.disconnect()

        self._tasks[user_id] = asyncio.create_task(_run())
        self._schedule_persist()
        logger.info(f"Task started for user {user_id}")

    async def stop(self, user_id: str):
        if not self.is_running(user_id):
            logger.info(f"Task not running for user {user_id}")
            return
        
        task = self._tasks.pop(user_id)
        client: ClientProtocol = self._clients.pop(user_id, None)

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        if client:
            try:
                await client.disconnect()
            except Exception:
                logger.exception("Error disconnecting client for %s", user_id)

        self._schedule_persist()
        logger.info(f"Task stopped for user {user_id}")


    async def restore_all(self, client_factory: Callable[..., object]):
        ensure = getattr(self._storage, "ensure_tables", None)
        if callable(ensure):
            await ensure()
        
        entries = await self._storage.load()
        current_tag = factory_tag(client_factory)
       

        
        for entry in entries:
            uid = entry["user_id"]
            kwargs = entry.get("kwargs", {})
            saved_tag = entry.get("factory_tag")
            if saved_tag and saved_tag != current_tag:
                logger.warning(
                    f"Factory mismatch for user {uid}: "
                    f"saved={saved_tag}, current={current_tag}. Skipping restore."
                )
                continue
            # do not await inside start loop if you want concurrency;
            # here we await to keep controlled
            await self.start(uid, client_factory, **kwargs)
    
    async def shutdown(self):
        logger.info("Shutting down TaskManager, cancelling all tasks...")
        if self._save_task and not self._save_task.done():
            self._save_task.cancel()
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        # Await all tasks, ignore cancellation errors
        for task in tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        # final persist to reflect empty/remaining tasks
        try:
            await self._persist_now()
        except Exception:
            logger.exception("Error persisting during shutdown")

        self._tasks.clear()
        self._clients.clear()
        logger.info("All tasks stopped cleanly.")
    
