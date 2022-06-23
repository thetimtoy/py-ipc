from typing import (
    Any,
    Callable,
    TypeVar,
)


__all__ = ('FuncT',)

FuncT = TypeVar('FuncT', bound=Callable[..., Any])
