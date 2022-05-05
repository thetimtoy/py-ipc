from typing import (
    Any,
    Callable,
    TypeVar,
)

from ipc.core.connection import Connection

__all__ = (
    'ConnectionT',
    'FuncT',
)


ConnectionT = TypeVar('ConnectionT', bound=Connection)
FuncT = TypeVar('FuncT', bound=Callable[..., Any])
