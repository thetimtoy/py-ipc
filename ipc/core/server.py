from __future__ import annotations

from asyncio import (
    CancelledError,
    gather,
    get_event_loop,
    run,
)
from typing import (
    TYPE_CHECKING,
    Callable,
)

from ipc.core.connection import Connection
from ipc.core.event_manager import EventManager

if TYPE_CHECKING:
    from asyncio import AbstractServer
    from types import TracebackType
    from typing import (
        Any,
        Coroutine,
        List,
        Optional,
        Type,
        overload,
    )
    from typing_extensions import (
        Literal,
        Self,
    )

    from ipc.core.protocol import Protocol


__all__ = ('Server',)


class Server(EventManager):
    if TYPE_CHECKING:
        host: str
        port: int
        _connected: bool
        _connections: List[Connection]
        _server: AbstractServer
        connection_factory: Callable[[Server], Connection]

    _connected = False

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connection_factory: Callable[[Server], Connection] = Connection,
    ) -> None:
        super().__init__()

        self.host = host
        self.port = port
        self.connection_factory = connection_factory
        self._connections = []

    def __repr__(self) -> str:
        return (
            f'<{type(self).__name__} host={self.host} '
            f'port={self.port} connected={self.connected} '
            f'connections={len(self._connections)}>'
        )

    async def __aenter__(self) -> Self:
        await self.connect()

        return self

    async def __aexit__(
        self,
        exc_tp: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tp: Optional[TracebackType],
    ) -> None:
        await self.close()

    # Public

    if TYPE_CHECKING:

        @overload
        def connect(self, run_sync: Literal[True]) -> Self:
            ...

        @overload
        def connect(self, run_sync: Literal[False] = ...) -> Coroutine[Any, Any, Self]:
            ...

    def connect(self, run_sync: bool = False) -> Any:
        """Start the server.

        If ``run_sync`` is set to ``True``, :func:`asyncio.run` is called to initialize and
        manage the event loop and cleanup is done for you. If this is set to ``False``,
        a coroutine is returned that resolves when the server has made it online.
        By default, ``run_sync`` is ``False``.

        Parameters
        ----------
        run_sync: :class:`bool`, default: False
            Whether to run in a blocking manner.

        Examples
        --------
        Starts the server in an async context. :meth:`.connect` returns when the server is online
        and the connection is closed when :meth:`.close` is called. ::

            await server.connect()
            ...
            await server.close()

        A blocking call that initializes and manages the event loop for you.
        `:meth:`.connect` only returns once the loop or server has been closed. ::

            server.connect(run_sync=True)
        """

        def factory() -> Protocol:
            factory = self.connection_factory

            connection = factory(self)

            return connection._protocol

        async def create_server():
            if not self.connected:
                loop = get_event_loop()

                self._server = await loop.create_server(
                    factory,
                    host=self.host,
                    port=self.port,
                )

                self._connected = True
                if self._stop_events:
                    self._stop_events = False

                # Signal that we are ready to start accepting connections
                self.dispatch('ready')

            return self

        if not run_sync:
            return create_server()

        async def runner():
            await create_server()

            try:
                # runs the asyncio server until runner()
                # is cancelled or .disconnect() is called.
                await self._server.serve_forever()
            except CancelledError:
                pass
            finally:
                await self.disconnect()

        try:
            run(runner())
        except KeyboardInterrupt:
            pass

        return self

    async def close(self) -> Self:
        """Close the server along with any open connections.

        This method is idemponent.
        """
        if self.connected:
            await self.disconnect()

        if len(self._connections):
            coros: List[Coroutine[Any, Any, Any]] = []

            for connection in self._connections:
                connection._stop_events = True
                coros.append(connection.close())

            await gather(*coros)

        return self

    async def disconnect(self) -> Self:
        """Close the server.

        This method is idemponent."""
        if self._connected:
            self._connected = False
            self._stop_events = True

            server = self._server

            del self._server

            server.close()

            await server.wait_closed()

        return self

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def connections(self) -> List[Connection]:
        """A list of open connections leased by this server."""
        return self._connections.copy()

    # Default event listeners

    def on_disconnect(self, connection: Connection, exc: Optional[Exception]) -> None:
        """The default ``disconnect`` event listener.

        If ``exc`` is not ``None``, it is propagated to :meth:`.on_error`.

        Parameters
        ----------
        exc: typing.Optional[:class:`Exception`]: The exception that occured.
        """
        if exc is not None:
            raise exc

    # Type hints for event listeners

    if TYPE_CHECKING:

        def on_ready(self) -> ...:
            ...

        def on_connect(self, connection: Connection) -> ...:
            ...

        def on_message(self, connection: Connection, data: Any) -> ...:
            ...
