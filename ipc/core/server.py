from __future__ import annotations

from asyncio import (
    CancelledError,
    gather,
    get_event_loop,
    run,
)
from typing import (
    TYPE_CHECKING,
    Generic,
)

from ipc.core.connection import Connection
from ipc.core.mixins.context_manager import ContextManagerMixin
from ipc.core.mixins.event_manager import EventManagerMixin
from ipc.core.types import ConnectionT
from ipc.core.utils import NULL

if TYPE_CHECKING:
    from asyncio import AbstractServer
    from typing import (
        Any,
        Callable,
        Coroutine,
        List,
        Optional,
        overload,
    )
    from typing_extensions import (
        Literal,
        Self,
    )

    from ipc.core.protocol import Protocol


__all__ = ('Server',)


class Server(Generic[ConnectionT], EventManagerMixin, ContextManagerMixin):
    if TYPE_CHECKING:
        host: str
        port: int
        _connected: bool
        _connections: List[ConnectionT]
        _server: AbstractServer
        connection_factory: Callable[[Self], ConnectionT]

    _connected = False

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connection_factory: Callable[[Self], ConnectionT] = Connection,
    ) -> None:
        super().__init__()

        self.host = host
        self.port = port
        self.connection_factory = connection_factory
        self._connections = []

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
            connection = self.connection_factory(self)

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
        coros: List[Coroutine[Any, Any, Any]] = []

        if self.connected:
            coros.append(self.disconnect())

        if len(self._connections):
            for connection in self._connections:
                coros.append(connection.close())

        if len(coros):
            await gather(*coros)

        return self

    async def disconnect(self) -> Self:
        if self._connected:
            self._connected = False

            server = self._server

            del self._server

            server.close()

            await server.wait_closed()

            self.dispatch('close')

        return self

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def connections(self) -> List[ConnectionT]:
        """A list of open connections leased by this server."""
        return self._connections.copy()

    # Default event listeners

    def on_disconnect(self, connection: ConnectionT, exc: Optional[Exception]) -> None:
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

        def on_close(self) -> ...:
            ...

        def on_connect(self, connection: ConnectionT) -> ...:
            ...

        def on_message(self, connection: ConnectionT, data: Any) -> ...:
            ...
