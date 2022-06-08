import asyncio

import pytest

from ipc import utils
from ipc.core.utils import maybe_awaitable

JSON_PAYLOAD = {
    'string': '',
    'number': 0,
    'boolean': False,
    'null': None,
    'object': {},
    'array': [],
}


async def noop():
    pass


def test_utils_json_dumps_loads() -> None:
    b = utils.json_dumps(JSON_PAYLOAD)

    assert isinstance(b, bytes)

    d = utils.json_loads(b)

    assert isinstance(d, dict)
    assert d == JSON_PAYLOAD
    assert utils.json_dumps(d) == b


def test_utils_future_raise_runtime_error() -> None:
    with pytest.raises(RuntimeError, match='no running event loop'):
        utils.future()


@pytest.mark.asyncio
async def test_utils_future(event_loop: asyncio.AbstractEventLoop) -> None:
    fut = utils.future()

    assert isinstance(fut, asyncio.Future)
    assert fut.get_loop() is event_loop

    with pytest.raises(asyncio.InvalidStateError, match='Exception is not set.'):
        fut.exception()

    fut.set_result(None)
    assert fut.done()


def test_utils_task_raise_runtime_error() -> None:
    coro = noop()
    try:
        with pytest.raises(RuntimeError, match='no running event loop'):
            utils.task(coro)
    finally:
        coro.close()


@pytest.mark.asyncio
async def test_utils_task(event_loop: asyncio.AbstractEventLoop) -> None:
    coro = noop()

    try:
        task = utils.task(coro)

        assert isinstance(task, asyncio.Task)
        assert task.get_loop() is event_loop

        with pytest.raises(asyncio.InvalidStateError, match='Exception is not set.'):
            task.exception()

        task.cancel()
        await asyncio.sleep(0)
        assert task.done()
    finally:
        coro.close()


@pytest.mark.asyncio
async def test_utils_maybe_awaitable() -> None:
    o = object()

    def func():
        return o

    result = await maybe_awaitable(func)
    assert result is o


@pytest.mark.asyncio
async def test_utils_maybe_awaitable_coro() -> None:
    o = object()

    async def func():
        return o

    result = await maybe_awaitable(func)
    assert result is o


@pytest.mark.asyncio
async def test_utils_maybe_awaitable_aw(event_loop: asyncio.AbstractEventLoop) -> None:
    o = object()

    def func():
        fut = event_loop.create_future()
        fut.set_result(o)
        return fut

    result = await maybe_awaitable(func)
    assert result is o


@pytest.mark.asyncio
async def test_utils_maybe_awaitable_args() -> None:
    args = (object(), object(), object())

    def func(*given_args):
        return given_args

    result = await maybe_awaitable(func, *args)
    assert result == args


@pytest.mark.asyncio
async def test_utils_maybe_awaitable_coro_args() -> None:
    args = (object(), object(), object())

    async def func(*given_args):
        return given_args

    result = await maybe_awaitable(func, *args)
    assert result == args


@pytest.mark.asyncio
async def test_utils_maybe_awaitable_aw_args(
    event_loop: asyncio.AbstractEventLoop,
) -> None:
    args = (object(), object(), object())

    def func(*given_args):
        fut = event_loop.create_future()
        fut.set_result(given_args)
        return fut

    result = await maybe_awaitable(func, *args)
    assert result == args


def test_utils_cached_property() -> None:
    o = object()

    class Test:
        def get_foo(self) -> object:
            return o

        foo = utils.cached_property('_foo')(get_foo)

    test = Test()

    assert isinstance(Test.foo, utils._CachedPropertyImpl)
    assert Test.foo._name == '_foo'
    assert Test.foo._func is Test.get_foo
    assert not hasattr(test, '_foo')
    assert test.foo is o
    assert hasattr(test, '_foo')
    assert test._foo is o  # type: ignore
    del test.foo
    assert not hasattr(test, '_foo')
    assert hasattr(test, 'foo')


def test_utils_null_sentinel() -> None:
    assert repr(utils.NULL) == '<NULL>'
    assert not utils.NULL
