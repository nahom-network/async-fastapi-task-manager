# Async FastAPI Task Manager

Reusable async task manager for FastAPI apps. Persist, restore, and manage background clients with SQLAlchemy and asyncio.

## Features
- **Async Task Management**: Launch, track, and control background tasks for multiple clients.
- **Persistence**: Save and restore task state using SQLAlchemy (async).
- **Extensible Storage**: Plug in custom storage backends.
- **Client Protocol**: Define your own background client logic.
- **Debounced Persistence**: Efficiently batch saves to storage.
- **FastAPI Integration**: Designed for use in FastAPI apps.

## Installation

```bash
pip install async-fastapi-task-manager
```
Or clone and install locally:
```bash
git clone https://github.com/your-org/async-fastapi-task-manager.git
cd async-fastapi-task-manager
pip install .
```

## Usage Example

### Basic Usage

```python
from task_manager import TaskManager, SQLStorageBase, ClientProtocol

storage = SQLStorageBase("sqlite+aiosqlite:///./db.sqlite3")
manager = TaskManager(storage)

# Define your client class implementing ClientProtocol
class MyClient(ClientProtocol):
    def __init__(self, user_id: str, **kwargs): ...
    async def connect(self): ...
    async def disconnect(self): ...

# Add, start, and persist tasks
await manager.start("user123", MyClient, foo="bar", other="kwarg")
await manager.stop("user123")
```

### FastAPI Integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from task_manager import TaskManager, SQLStorageBase

storage = SQLStorageBase("sqlite+aiosqlite:///./db.sqlite3")
manager = TaskManager(storage)

# Define your client class implementing ClientProtocol
class MyClient(ClientProtocol):
    def __init__(self, user_id: str, **kwargs): ...
    async def connect(self): ...
    async def disconnect(self): ...

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start a specific task
    await manager.start("uid", MyClient, foo="bar", other="kwarg")
    # Restore all previously running tasks
    await manager.restore_all(MyClient)
    yield
    # Clean up on shutdown
    await manager.shutdown()

app = FastAPI(lifespan=lifespan)
```

## Project Structure
- `main.py`: Entry point.
- `task_manager/`: Core logic
  - `base.py`: TaskManager class
  - `models.py`: SQLAlchemy models
  - `storage.py`: Async storage implementation
  - `types.py`: Protocols for storage and clients
  - `utils.py`: Utility functions
- `tests/`: Pytest-based tests

## Configuration
- **Database**: Uses SQLAlchemy async engine. Example: `sqlite+aiosqlite:///./db.sqlite3`
- **Dependencies**: See `pyproject.toml` for required and optional packages.

## Development
Install dev dependencies:
```bash
pip install .[dev]
```
Run tests:
```bash
pytest
```

## License
MIT

## Author
Nahom (<dev@nahom.codes>)
