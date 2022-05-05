from __future__ import annotations

from typing import TYPE_CHECKING

from ipc.core.base_connection import BaseConnection

if TYPE_CHECKING:
    from asyncio import Transport
    from typing import (
        Any,
        Optional,
    )
    from typing_extensions import Self

    from ipc.core.server import Server


__all__ = ('Connection',)


class Connection(BaseConnection):
    """Represents a client connection to the server"""

    if TYPE_CHECKING:
        server: Server[Self]

    def __init__(self, server: Server[Self]) -> None:
        super().__init__()

        self.server = server

    # Properties

    @property
    def host(self) -> str:
        return self.server.host

    @property
    def port(self) -> int:
        return self.server.port

    # Internals

    def dispatch(self, event: str, *args: Any) -> None:
        super().dispatch(event, *args)

        # We want to dispatch the same event on the server object,
        # but with the connection object as the first argument
        self.server.dispatch(event, self, *args)

    # Asyncio callbacks

    def _protocol_cb_connection_made(self, transport: Transport) -> None:
        self.server._connections.append(self)

        super()._protocol_cb_connection_made(transport)

    def _protocol_cb_connection_lost(self, exc: Optional[Exception]) -> None:
        self.server._connections.remove(self)

        super()._protocol_cb_connection_lost(exc)
