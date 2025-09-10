import hashlib
from typing import Callable


def factory_tag(factory: Callable[..., object]) -> str:
    # Use module + qualname as a stable identifier
    ident = f"{factory.__module__}.{factory.__qualname__}"
    # Hash it to a short, consistent string
    return hashlib.sha256(ident.encode()).hexdigest()[:16]
