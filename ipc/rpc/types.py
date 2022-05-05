from typing import (
    TYPE_CHECKING,
    TypeVar,
)


if TYPE_CHECKING:
    from ipc.core.connection import Connection as _Connection
    from ipc.rpc.server import Server

    # Bandaid for the fact that Connection is not generic
    class Connection(_Connection):
        if TYPE_CHECKING:
            server: Server

        def __init__(self, server: Server) -> None:
            ...


ConnectionT = TypeVar('ConnectionT', bound='Connection')
