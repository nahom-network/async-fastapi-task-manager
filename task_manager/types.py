from typing import Any, Dict, List, Protocol, runtime_checkable


# A lightweight description for storage
@runtime_checkable
class TaskStorage(Protocol):
    async def save(self, tasks: List[Dict[str, Any]]) -> None:
        ...

    async def load(self) -> List[Dict[str, Any]]:
        ...

# What your client objects must implement
class ClientProtocol(Protocol):
    def __init__(self, user_id: str, **kwargs: Any) -> None: ...
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...