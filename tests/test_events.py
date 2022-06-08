import asyncio
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Tuple,
)

import pytest

from ipc.core.event_manager import EventManager


def listener() -> None:
    pass


def get_listeners(
    events: EventManager,
) -> Tuple[List[Callable[..., Any]], Dict[str, List[Callable[..., Any]]]]:
    listeners = events.get_listeners_for('')
    all_listeners = events.get_all_listeners()

    return listeners, all_listeners


async def wait_for_task(events: EventManager, predicate: Callable[[], bool]) -> None:
    await events.wait_for('', predicate=predicate)

    assert False


def assert_listener_is_stored(events: EventManager) -> None:
    listeners, all_listeners = get_listeners(events)

    assert listener in listeners
    assert len(listeners) == 1
    assert '' in all_listeners
    assert listener in all_listeners['']
    assert len(all_listeners) == 1
    assert len(all_listeners['']) == 1


def assert_listener_not_stored(events: EventManager) -> None:
    listeners, all_listeners = get_listeners(events)

    assert listener not in listeners
    assert len(listeners) == 0
    assert '' not in all_listeners
    assert len(all_listeners) == 0


@pytest.fixture
def events():
    return EventManager()


@pytest.mark.asyncio
async def test_events_dispatch_raise_type_error(events: EventManager) -> None:
    with pytest.raises(TypeError, match='expected event to be str, not None'):
        events.dispatch(None)  # type: ignore

    events.on_test = None  # type: ignore

    with pytest.raises(
        TypeError, match='expected self.on_test to be a callable, not None'
    ):
        events.dispatch('test')


def test_events_add_listener_raise_type_error(events: EventManager) -> None:
    with pytest.raises(TypeError, match='expected event to be str, not None'):
        events.add_listener(None, listener)  # type: ignore

    with pytest.raises(TypeError, match='expected listener to be a callable, not None'):
        events.add_listener('', None)  # type: ignore


def test_events_remove_listener_raise_type_error(events: EventManager) -> None:
    with pytest.raises(TypeError, match='expected event to be str, not None'):
        events.add_listener(None, listener)  # type: ignore

    with pytest.raises(TypeError, match='expected listener to be a callable, not None'):
        events.add_listener('', None)  # type: ignore


def test_events_listener_decorator_raise_type_error(events: EventManager) -> None:
    with pytest.raises(TypeError, match='expected event to be str, not None'):
        events.listener(None)  # type: ignore

    with pytest.raises(TypeError, match='expected a callable, not None'):
        events.listener('')(None)  # type: ignore


@pytest.mark.asyncio
async def test_events_wait_for_raise_type_error(events: EventManager) -> None:
    with pytest.raises(TypeError, match='expected event to be str, not None'):
        await events.wait_for(None)  # type: ignore

    with pytest.raises(TypeError, match='expected predicate to be a callable, not 0'):
        await events.wait_for('', predicate=0)  # type: ignore


@pytest.mark.asyncio
async def test_events_wait_for_timeout(events: EventManager) -> None:
    with pytest.raises(asyncio.TimeoutError, match=None):
        await events.wait_for('', timeout=0)


def test_events_root_listener(events: EventManager) -> None:
    events.add_listener('test', listener, root=True)
    assert hasattr(events, 'on_test')
    assert events.on_test is listener  # type: ignore

    events.remove_listener('test', listener)
    assert not hasattr(events, 'on_test')

    events.add_listener('test', listener, root=True)
    assert hasattr(events, 'on_test')
    assert events.on_test is listener  # type: ignore

    events.remove_listeners_for('test')
    assert not hasattr(events, 'on_test')

    events.add_listener('test', listener, root=True)
    assert hasattr(events, 'on_test')
    assert events.on_test is listener  # type: ignore

    events.remove_all_listeners()
    assert not hasattr(events, 'on_test')


@pytest.mark.asyncio
async def test_events_cancel_waiters(
    events: EventManager, event_loop: asyncio.AbstractEventLoop
) -> None:
    predicate = lambda: True
    listeners = events._listeners
    event_loop.create_task(wait_for_task(events, predicate))

    await asyncio.sleep(0)

    assert '' in listeners
    assert predicate in listeners['']
    assert len(listeners) == 1
    assert len(listeners['']) == 1
    assert hasattr(predicate, '__ipc_event_waiter__')
    assert isinstance(predicate.__ipc_event_waiter__, asyncio.Future)

    events.cancel_waiters('')

    await asyncio.sleep(0)

    assert '' not in listeners
    assert len(listeners) == 0
    assert not hasattr(predicate, '__ipc_event_waiter__')


@pytest.mark.asyncio
async def test_events_cancel_all_waiters(
    events: EventManager, event_loop: asyncio.AbstractEventLoop
) -> None:
    predicate = lambda: True
    listeners = events._listeners
    event_loop.create_task(wait_for_task(events, predicate))

    await asyncio.sleep(0)

    assert '' in listeners
    assert predicate in listeners['']
    assert len(listeners) == 1
    assert len(listeners['']) == 1
    assert hasattr(predicate, '__ipc_event_waiter__')
    assert isinstance(predicate.__ipc_event_waiter__, asyncio.Future)

    events.cancel_all_waiters()

    await asyncio.sleep(0)

    assert '' not in listeners
    assert len(listeners) == 0
    assert not hasattr(predicate, '__ipc_event_waiter__')


@pytest.mark.asyncio
async def test_events_dispatch_no_args(events: EventManager) -> None:
    called = False

    def listener():
        nonlocal called

        called = True

    events.add_listener('', listener)
    events.dispatch('')

    await asyncio.sleep(0)

    assert called


@pytest.mark.asyncio
async def test_events_dispatch_one_arg(events: EventManager) -> None:
    arg = object()
    result = None

    def listener(given_arg):
        nonlocal result
        result = given_arg

    events.add_listener('', listener)
    events.dispatch('', arg)

    await asyncio.sleep(0)

    assert arg is result


@pytest.mark.asyncio
async def test_events_dispatch_many_args(events: EventManager) -> None:
    args = (object(), object(), object())
    result = None

    def listener(*given_args):
        nonlocal result
        result = given_args

    events.add_listener('', listener)
    events.dispatch('', *args)

    await asyncio.sleep(0)

    assert args == result


@pytest.mark.asyncio
async def test_events_dispatch_wait_for_no_args(
    events: EventManager, event_loop: asyncio.AbstractEventLoop
) -> None:
    event_loop.call_soon(events.dispatch, '')

    result = await events.wait_for('', timeout=0.01)

    assert result is None


@pytest.mark.asyncio
async def test_events_dispatch_wait_for_one_arg(
    events: EventManager, event_loop: asyncio.AbstractEventLoop
) -> None:
    arg = object()

    event_loop.call_soon(events.dispatch, '', arg)

    result = await events.wait_for('', timeout=0.01)

    assert arg is result


@pytest.mark.asyncio
async def test_events_dispatch_wait_for_many_args(
    events: EventManager, event_loop: asyncio.AbstractEventLoop
) -> None:
    args = (object(), object(), object())

    event_loop.call_soon(events.dispatch, '', *args)

    result = await events.wait_for('', timeout=0.01)

    assert args == result


def test_events_methods_return_self(events: EventManager) -> None:
    assert events.add_listener('', listener) is events
    assert events.remove_listener('', listener) is events
    assert events.remove_listeners_for('') is events
    assert events.remove_all_listeners() is events
    assert events.cancel_waiters('') is events
    assert events.cancel_all_waiters() is events


def test_events_remove_listener(events: EventManager) -> None:
    events.add_listener('', listener)

    assert_listener_is_stored(events)

    events.remove_listener('', listener)

    assert_listener_not_stored(events)


def test_events_remove_listeners_for(events: EventManager) -> None:
    events.add_listener('', listener)

    assert_listener_is_stored(events)

    events.remove_listeners_for('')

    assert_listener_not_stored(events)


def test_events_remove_all_listeners(events: EventManager) -> None:
    events.add_listener('', listener)

    assert_listener_is_stored(events)

    events.remove_all_listeners()

    assert_listener_not_stored(events)
