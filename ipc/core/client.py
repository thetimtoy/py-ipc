from __future__ import annotations

from asyncio import (
    get_event_loop,
    run,
)
from typing import TYPE_CHECKING

from ipc.core.base_connection import BaseConnection
from ipc.core.utils import future

if TYPE_CHECKING:
    from typing import (
        Any,
        Coroutine,
        Optional,
        overload,
    )
    from typing_extensions import (
        Literal,
        Self,
    )


__all__ = ('Client',)


class Client(BaseConnection):
    """Represents an outgoing connection to a server"""

    if TYPE_CHECKING:
        host: str
        port: int

    def __init__(self, host: str, port: int) -> None:
        super().__init__()

        self.host = host
        self.port = port

    async def __aenter__(self) -> Self:
        await self.connect()

        return await super().__aenter__()

    # Public

    if TYPE_CHECKING:

        @overload
        def connect(self, run_sync: Literal[True]) -> Self:
            ...

        @overload
        def connect(self, run_sync: Literal[False] = ...) -> Coroutine[Any, Any, Self]:
            ...

    def connect(self, run_sync: bool = False) -> Any:
        """Attempt to connect to a listening server.

        If ``run_async`` is set to ``True``, :func:`asyncio.run` is called to initialize and
        manage the event loop and cleanup is done for you. If this is set to ``False``,
        a coroutine is returned that resolves when the client has made it online.
        By default, ``run_sync`` is ``False``.

        If this method is called while a connection is open, it does nothing.

        Parameters
        ----------
        run_sync: :class:`bool`, default: False
            Whether to run in a blocking manner.

        Examples
        --------
        Starts the client in an async context. :meth:`.connect` returns when the client is online
        and the connection is closed when :meth:`.close` is called. ::

            await client.connect()
            ...
            await client.close()

        A blocking call that initializes and manages the event loop for you.
        `:meth:`.connect` only returns once the loop or the connection is closed. ::

            client.connect(run_sync=True)
        """

        async def create_connection():
            if not self.connected:
                if self._stop_events:
                    self._stop_events = False
                await get_event_loop().create_connection(
                    lambda: self._protocol,
                    host=self.host,
                    port=self.port,
                )

            return self

        if not run_sync:
            return create_connection()

        async def runner():
            await create_connection()

            self._close_waiter = future()

            await self._close_waiter

        try:
            run(runner())
        except KeyboardInterrupt:
            pass

        return self

    # Asyncio callbacks
    def _protocol_cb_connection_lost(self, exc: Optional[Exception]) -> None:
        self._stop_events = True
        return super()._protocol_cb_connection_lost(exc)

    # Type hints for event listeners

    if TYPE_CHECKING:

        def on_connect(self) -> ...:
            ...

        def on_message(self, data: Any) -> ...:
            ...
