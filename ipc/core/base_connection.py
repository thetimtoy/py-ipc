from __future__ import annotations

from typing import TYPE_CHECKING

from ipc.core.errors import NotConnected
from ipc.core.mixins.context_manager import ContextManagerMixin
from ipc.core.mixins.event_manager import EventManagerMixin
from ipc.core.protocol import Protocol
from ipc.core.utils import (
    future,
    json_dumps,
    json_loads,
)

if TYPE_CHECKING:
    from asyncio import (
        Future,
        Transport,
    )
    from typing import (
        Any,
        Callable,
        Coroutine,
        Optional,
    )
    from typing_extensions import Self

__all__ = ('BaseConnection',)


class BaseConnection(EventManagerMixin, ContextManagerMixin):
    """Base class for objects that represent a connection."""

    if TYPE_CHECKING:
        _read_buffer: bytearray
        _write_buffer: Optional[bytearray]
        _protocol: Protocol
        _transport: Transport
        _close_waiter: Future[None]
        _paused: bool
        # must be implemented by subclasses
        host: str
        port: int

    __slots__ = (
        '_read_buffer',
        '_write_buffer',
        '_protocol',
        '_transport',
        '_close_waiter',
        '_paused',
    )

    def __init__(self):
        super().__init__()

        self._paused = False
        self._write_buffer = None
        self._read_buffer = bytearray()
        self._protocol = Protocol(
            connection_made=self._protocol_cb_connection_made,
            connection_lost=self._protocol_cb_connection_lost,
            data_received=self._protocol_cb_data_received,
            eof_received=self._protocol_cb_eof_received,
            pause_writing=self._protocol_cb_pause_writing,
            resume_writing=self._protocol_cb_resume_writing,
        )

    def __repr__(self) -> str:
        return (
            f'<{type(self).__name__} host={self.host} '
            f'port={self.port} connected={self.connected}>'
        )

    # Public

    async def close(self) -> Self:
        """Close this connection.

        This method is idemponent.
        """
        if self.connected:
            self._transport.close()

            await self._wait_closed()

        return self

    @property
    def connected(self) -> bool:
        """:class:`bool`: Whether this connection is open."""
        return hasattr(self, '_transport') and not self._transport.is_closing()

    # Internals

    def send(self, data: Any) -> Self:
        """Arrange for `data` to be sent asynchronously.

        `data` must be an object :func:`json.dumps` can serialize.
        """
        if not self.connected:
            raise NotConnected('Connection is closed.')

        json = json_dumps(data)

        to_send = json.encode() if isinstance(json, str) else json

        to_send = f'{len(to_send)} '.encode() + to_send

        if self._paused:
            if self._write_buffer is None:
                self._write_buffer = bytearray()

            self._write_buffer.extend(to_send)

        else:
            self._transport.write(to_send)

        return self

    def recv(
        self,
        *,
        predicate: Optional[Callable[..., Any]] = None,
        timeout: Optional[float] = None,
    ) -> Coroutine[Any, Any, Any]:
        """Shorthand method for ``wait_for('message')``.

        See :meth:`.wait_for` for more info.
        """
        return self.wait_for('message', predicate=predicate, timeout=timeout)

    def _wait_closed(self) -> Future[None]:
        """:class:`asyncio.Future`: Return a future that resolves
        when :meth:`._connection_lost` is called.
        """
        if not hasattr(self, '_close_waiter'):
            self._close_waiter = future()

        return self._close_waiter

    # Asyncio callbacks

    def _protocol_cb_connection_made(self, transport: Transport) -> None:
        """Called when the connection is made."""
        self._transport = transport

        self.dispatch('connect')

    def _protocol_cb_connection_lost(self, exc: Optional[Exception]) -> None:
        """Called when the connection is lost."""
        del self._transport

        if hasattr(self, '_close_waiter'):
            self._close_waiter.set_result(None)

            del self._close_waiter

        self.dispatch('disconnect', exc)

    def _protocol_cb_data_received(self, data: bytes) -> None:
        """Called when some data is received."""

        buffer = self._read_buffer

        buffer.extend(data)

        while True:
            ws_idx = buffer.find(b' ')

            if ws_idx == -1:
                return

            length = int(buffer[:ws_idx])

            start = ws_idx + 1  # incr by 1 for ws char
            end = start + length

            d = buffer[start:end]

            if len(d) < length:
                return

            del buffer[:end]

            self.dispatch('message', json_loads(d))

    def _protocol_cb_eof_received(self) -> bool:
        """Called when eof is received."""
        return False

    def _protocol_cb_pause_writing(self) -> None:
        """Called when the transport's write buffer is too large."""
        self._paused = True

    def _protocol_cb_resume_writing(self) -> None:
        """Called when the transport's write buffer has been
        drained and can be written to.
        """
        self._paused = False

        if self._write_buffer is not None:
            self._transport.write(self._write_buffer)

            self._write_buffer.clear()
