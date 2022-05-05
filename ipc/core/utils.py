from __future__ import annotations

from typing import TYPE_CHECKING, overload

from asyncio import get_running_loop
from distutils.util import strtobool
from importlib import import_module
from inspect import isawaitable
from os import environ

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
        Dict,
        Generic,
        Optional,
        Sequence,
        Type,
        TypeVar,
        Union,
    )
    from typing_extensions import Self

    T = TypeVar('T')
    T2 = TypeVar('T2')

__all__ = (
    'json_dumps',
    'json_loads',
    'future',
    'task',
    'setup_lazy_imports',
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


def json_dumps(obj: Any) -> bytes:
    ret = _json_dumps(obj)

    return ret if isinstance(ret, bytes) else ret.encode()


def json_loads(obj: bytes) -> Any:
    return _json_loads(obj)


def future() -> Future[Any]:
    return get_running_loop().create_future()


def task(coro: Coroutine[Any, Any, T]) -> Task[T]:
    return get_running_loop().create_task(coro)


def setup_lazy_imports(
    ns: Dict[str, Any],
    _exported: Dict[Union[str, Sequence[str]], Union[Dict[str, str], str]],
) -> None:
    exported: Dict[str, Union[str, Dict[str, str]]] = {}

    for name, options in _exported.items():
        if isinstance(name, str):
            exported[name] = options
        else:
            for n in name:
                exported[n] = options

    if not strtobool(environ.get('PYIPC_LAZY_IMPORTS', 'yes')):
        for name, options in exported.items():
            _import_name(name, options, ns)

        return

    def lazy_import(name):
        try:
            return ns[name]
        except KeyError:
            pass

        try:
            options = exported[name]
        except KeyError:
            raise AttributeError(
                f"module '{ns['__name__']}' has no attribute '{name}'"
            ) from None

        return _import_name(name, options, ns)

    ns['__getattr__'] = lazy_import


def _import_name(name: str, options: Union[str, Dict[str, str]], ns: Dict[str, Any]):
    if isinstance(options, str):
        module_name = options
        attr = name
    else:
        module_name = options['module']
        attr = options.get('variable', name)

    module = import_module(module_name)

    if attr == '*':
        res = module
    else:
        res = getattr(module, attr)

    ns[name] = res

    return res


async def maybe_awaitable(
    func: Callable[..., Union[T, Awaitable[T]]],
    *args: Any,
    **kwargs: Any,
) -> T:
    ret = func(*args, **kwargs)

    if isawaitable(ret):
        ret = await ret

    return ret  # type: ignore (type checker can't figure this out)


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
