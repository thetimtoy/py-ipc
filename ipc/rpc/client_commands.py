from __future__ import annotations

from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Coroutine,
        MutableMapping,
    )
    from ipc.rpc.client import Client


_client_mapping: MutableMapping[ClientCommands, Client] = WeakKeyDictionary()


class ClientCommands:
    __slots__ = ('__weakref__',)

    def __init__(self, client: Client) -> None:
        _client_mapping[self] = client

    def __getattribute__(self, name: str) -> Callable[..., Coroutine[Any, Any, Any]]:
        client = _client_mapping[self]

        return lambda *args, **kwds: client.invoke(name, *args, **kwds)
