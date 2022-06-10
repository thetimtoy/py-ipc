from __future__ import annotations

from sys import version_info
from asyncio import get_running_loop
from inspect import isawaitable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from asyncio import (
        Future,
        Task,
    )
    from typing import (
        Any,
        Awaitable,
        Callable,
        Coroutine,
        Generic,
        Optional,
        Type,
        TypeVar,
        Union,
        overload,
    )
    from typing_extensions import Self

    T = TypeVar('T')
    T2 = TypeVar('T2')

__all__ = (
    'json_dumps',
    'json_loads',
    'future',
    'task',
    'maybe_awaitable',
    'NULL',
)

try:
    import orjson as json  # type: ignore
except ImportError:
    try:
        import ujson as json  # type: ignore
    except ImportError:
        import json

_json_dumps = json.dumps
_json_loads = json.loads

_HAS_TASK_NAMES = version_info >= (3, 8)


def json_dumps(obj: Any) -> bytes:
    ret = _json_dumps(obj)

    return ret if isinstance(ret, bytes) else ret.encode()


def json_loads(obj: bytes) -> Any:
    return _json_loads(obj)


def future() -> Future[Any]:
    return get_running_loop().create_future()


def task(coro: Coroutine[Any, Any, T], name: str | None = None) -> Task[T]:
    create_task = get_running_loop().create_task

    if _HAS_TASK_NAMES:
        return create_task(coro, name=name)  # type: ignore

    return create_task(coro)


async def maybe_awaitable(
    func: Callable[..., Union[Any, Awaitable[Any]]],
    *args: Any,
    **kwargs: Any,
) -> Any:
    ret = func(*args, **kwargs)

    if isawaitable(ret):
        ret = await ret

    return ret


def cached_property(name: str) -> Callable[[Callable[[T], T2]], _CachedProperty[T, T2]]:
    return lambda func: _CachedProperty(name, func)


class _CachedPropertyImpl:
    __slots__ = (
        '_name',
        '_func',
    )

    def __init__(self, name: str, func: Callable[..., Any]) -> None:
        self._name = name
        self._func = func

    def __get__(self, instance: Optional[object], owner: type) -> Any:
        if instance is None:
            return self

        try:
            return getattr(instance, self._name)
        except AttributeError:
            value = self._func(instance)

            setattr(instance, self._name, value)

            return value

    def __delete__(self, instance: object) -> None:
        try:
            delattr(instance, self._name)
        except AttributeError:
            pass


if TYPE_CHECKING:

    class _CachedProperty(Generic[T, T2]):
        def __init__(self, name: str, func: Callable[[T], T2]) -> None:
            ...

        @overload
        def __get__(self, instance: T, owner: Type[T]) -> T2:
            ...

        @overload
        def __get__(self, instance: None, owner: Type[T]) -> Self:
            ...

        def __get__(self, instance: Optional[T], owner: Type[T]) -> Any:
            ...

        def __delete__(self, instance: T) -> None:
            ...

else:
    _CachedProperty = _CachedPropertyImpl


class _NullSentinel:
    __slots__ = ()

    def __repr__(self) -> str:
        return '<NULL>'

    def __bool__(self) -> bool:
        return False


NULL: Any = _NullSentinel()
