from __future__ import annotations

from asyncio import (
    CancelledError,
    TimeoutError,
    wait_for,
)
from sys import stderr
from traceback import print_exc
from typing import TYPE_CHECKING

from ipc.core.utils import (
    future,
    maybe_awaitable,
    task,
)

if TYPE_CHECKING:
    from asyncio import Future
    from typing import (
        Any,
        Callable,
        Dict,
        List,
        Optional,
        Iterable,
    )
    from typing_extensions import Self

    from ipc.core.types import FuncT

__all__ = ('EventManagerMixin',)


class EventManagerMixin:
    """Mixin class to provide an API for events."""

    __slots__ = ('_listeners',)

    if TYPE_CHECKING:
        _listeners: Dict[str, List[Callable[..., Any]]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        self._listeners = {}

    # Internals

    def dispatch(self, event: str, *args: Any, root: bool = False) -> None:
        """Dispatch an event with the given arguments.

        Parameters
        ----------
        event: :class:`str`
            Event name to dispatch.
        *args:
            Positional arguments to pass to event listeners.
        root: :class:`bool`
            Whether to only trigger the root listener for this event.
        """
        if not root:
            try:
                listeners = self._listeners[event]
            except KeyError:
                pass
            else:
                to_remove = []

                for listener in listeners:
                    try:
                        fut: Future[Any] = listener.__ipc_event_waiter__
                    except AttributeError:
                        self._schedule_listener(listener, *args)
                    else:
                        if not fut.done():
                            try:
                                ok = listener(*args)
                            except Exception as exc:
                                fut.set_exception(exc)
                            else:
                                if not ok:
                                    continue

                                args_len = len(args)

                                fut.set_result(
                                    None
                                    if args_len == 0
                                    else args[0]
                                    if args_len == 1
                                    else args
                                )

                            to_remove.append(listener)

                for listener in to_remove:
                    self.remove_listener(event, listener)

        try:
            root_listener = getattr(self, f'on_{event}')
        except AttributeError:
            pass
        else:
            if event == 'error':
                task(self._handle_error(*args))
            else:
                self._schedule_listener(root_listener, *args)

    def _schedule_listener(self, listener: Callable[..., Any], *args: Any) -> None:
        """Wrap a listener in an asyncio task and schedule for it to be called soon."""
        task(self._wrap_listener(listener, *args))

    def _filter_listeners(
        self, listeners: Iterable[Callable[..., Any]], *, return_waiters: bool = False
    ) -> List[Callable[..., Any]]:
        """Remove callables from ``listeners`` that belong to :meth:`.wait_for`

        Parameters
        ----------
        listeners: Iterable[Callable[..., Any]]
            Iterable of event listeners
        return_waiters: :class:`bool`
            Whether to return the filtered waiters
        """
        ret = []

        for listener in listeners:
            is_waiter = hasattr(listener, '__ipc_event_waiter__')

            if is_waiter and return_waiters:
                ret.append(listener)
            elif not is_waiter and not return_waiters:
                ret.append(listener)

        return ret

    async def _wrap_listener(self, listener: Callable[..., Any], *args: Any) -> None:
        """Run the ``listener`` callable and handle if an :class:`Exception` is raised.

        If ``listener`` returns an awaitable, this method returns once that awaitable returns.
        """
        try:
            await maybe_awaitable(listener, *args)
        except Exception as exc:
            await self._handle_error(exc, *args)

    async def _handle_error(self, exc: Exception, *args: Any) -> None:
        """Call :meth:`.on_error` with the given arguments."""
        await maybe_awaitable(self.on_error, exc, *args)

    # Managing listeners

    def listener(self, event: str, *, root: bool = False) -> Callable[[FuncT], FuncT]:
        """Add an event listener.

        This is the decorator equivalent of :meth:`.add_listener`.

        Parameters
        ----------
        event: :class:`str`
            The event name.
        root: :class:`bool`
            Whether to add as a root listener.

        Examples
        --------
        Usage ::

            @listener('connect')
            def on_connect(...): ...
        """

        def decorator(func):
            self.add_listener(event, func, root=root)

            return func

        return decorator

    def add_listener(
        self,
        event: str,
        listener: Callable[..., Any],
        *,
        root: bool = False,
    ) -> Self:
        """Add an event listener.

        Parameters
        ----------
        event: :class:`str`
            The event name.
        listener: Callable[..., Any]
            The event listener, which can return an awaitable.
        root: :class:`bool`
            Whether to add as a root listener.

        Examples
        --------
        Usage ::
            def on_connect(...): ...
            add_listener('connect', on_connect)
        """
        if root:
            setattr(self, f'on_{event}', listener)
        else:
            try:
                listeners = self._listeners[event]
            except KeyError:
                listeners = self._listeners[event] = []

            listeners.append(listener)

        return self

    def remove_listener(self, event: str, listener: Callable[..., Any]) -> Self:
        """Remove an event listener.

        .. note::
            This method also checks whether ``listener`` has been added
            as a root listener and removes it as a root listener if so.

        Parameters
        ----------
        event: :class:`str`
            The event name.
        listener: Callable[..., Any]
            The event listener to remove.

        Examples
        --------
        Adding an event listener using :meth:`.add_listener`. ::

            def on_connect(...): ...
            add_listener('connect', on_connect)
            ...

        And then removing said listener later. ::

            remove_listener('connect', on_connect)
        """
        try:
            listeners = self._listeners[event]
        except KeyError:
            pass
        else:
            try:
                listeners.remove(listener)
            except ValueError:
                pass

            if not len(listeners):
                del self._listeners[event]

        try:
            root_listener = getattr(self, f'on_{event}')
        except AttributeError:
            pass
        else:
            if listener is root_listener:
                delattr(self, f'on_{event}')

        return self

    def get_all_listeners(self) -> Dict[str, List[Callable[..., Any]]]:
        """Get all listeners bound to this object.

        This helper also returns any root listeners.
        """
        listeners = {}

        for event in self._listeners:
            listeners[event] = self.get_listeners_for(event)

        return listeners

    def get_listeners_for(self, event: str) -> List[Callable[..., Any]]:
        """Get all listeners for a given event.

        This helper also returns the root listener if it exists.
        """
        try:
            listeners = self._listeners[event]
        except KeyError:
            listeners = []
        else:
            listeners = self._filter_listeners(listeners)

        try:
            root_listener = getattr(self, f'on_{event}')
        except AttributeError:
            pass
        else:
            listeners.append(root_listener)

        return listeners

    def remove_listeners_for(self, event: str) -> Self:
        """Remove all listeners for a given event.

        This helper also removes the root listener if it exists.
        """
        try:
            listeners = self._listeners[event]
        except KeyError:
            pass
        else:
            listeners = self._filter_listeners(listeners, return_waiters=True)

            if not len(listeners):
                del self._listeners[event]
            else:
                self._listeners[event] = listeners

        try:
            delattr(self, f'on_{event}')
        except AttributeError:
            pass

        return self

    def remove_all_listeners(self) -> Self:
        """Remove all listeners bound to this object."""
        for event in self._listeners:
            self.remove_listeners_for(event)

        return self

    def cancel_waiters(self, event: str) -> Self:
        """Cancel any :meth:`.wait_for` waiters for a given event.

        Note: As this helper cancels the underlying future and due to how
        asyncio tasks are implemented, :exc:`asyncio.CancelledError` isn't
        propagated if :meth:`.wait_for` is used in an event listener.
        To check for the error, you should wrap the :meth:`.wait_for` call
        in a try except block to catch exc:`asyncio.CancelledError`.

        Note: This method is experimental and may be removed.
        """
        try:
            listeners = self._listeners[event]
        except KeyError:
            pass
        else:
            for listener in self._filter_listeners(listeners, return_waiters=True):
                fut: Future[Any] = listener.__ipc_event_waiter__

                fut.cancel()

        return self

    def cancel_all_waiters(self) -> Self:
        """Cancel waiters for every event.

        See :meth:`.cancel_waiters` for more info.

        Note: This method is experimental and may be removed.
        """
        for event in self._listeners:
            self.cancel_waiters(event)

        return self

    async def wait_for(
        self,
        event: str,
        *,
        predicate: Optional[Callable[..., Any]] = None,
        timeout: Optional[float] = None,
    ) -> Any:
        """Wait for an event to be dispatched that meets the
        given ``predicate`` with an optional ``timeout``.

        If ``predicate`` is ``None``, this method returns on the first dispatched
        event with the provided name.

        If the dispatched event has multiple arguments, this method returns a tuple
        of said arguments; If the event has only one argument, that is returned instead.
        In the case that the event has no arguments, ``None`` is returned.

        Parameters
        ----------
        event: :class:`str`
            The event name.
        predicate: Optional[Callable[..., Any]], default: None
            A callable that accepts the same arguments that a regular event
            listener would for the given event and returns a boolish value.
        timeout: :class:`float`, default: None
            The number of seconds to wait before cancelling the waiter and
            raising :exc:`asyncio.TimeoutError`.

        Examples
        --------
        Proceeds when a ``disconnect`` event is triggered. ::

            await wait_for('disconnect')
            cleanup_stuff()

        Proceeds when a ``message`` event is triggered and ``data`` is an instance
        of :class:`dict` with a ``'foo'`` key. ::

            data = await wait_for('message', lambda data: isinstance(data, dict) and 'foo' in data)
            do_stuff_with_data(data)
        """
        if predicate is None:
            predicate = lambda *_: True

        fut = future()

        predicate.__ipc_event_waiter__ = fut

        self.add_listener(event, predicate)

        try:
            return await wait_for(fut, timeout)
        except (CancelledError, TimeoutError):
            print(fut.cancelled())

            self.remove_listener(event, predicate)

            raise

    # Default event listeners

    async def on_error(self, *args: Any) -> None:
        """The default ``error`` event listener.

        This prints the error message to :data:`sys.stderr`.
        """
        print('IPC exception caught:', file=stderr)
        print_exc(file=stderr)
