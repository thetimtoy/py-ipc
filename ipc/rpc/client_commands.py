from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Coroutine,
    )
    from ipc.rpc.client import Client



class ClientCommands:
    __slots__ = ('__client',)

    def __init__(self, client: Client) -> None:
        self.__client = client

    def __getattr__(self, name: str) -> Callable[..., Coroutine[Any, Any, Any]]:
        client = self.__client

        return lambda *args, **kwds: client.invoke(name, *args, **kwds)
