from typing import (
    TYPE_CHECKING,
    Any,
    List,
    TypeVar,
)
from typing_extensions import Literal, NotRequired, TypedDict


if TYPE_CHECKING:
    from ipc.core.connection import Connection as _Connection
    from ipc.rpc.server import Server

    # Bandaid for the fact that Connection is not generic
    class Connection(_Connection):
        if TYPE_CHECKING:
            server: Server

        def __init__(self, server: Server) -> None:
            ...

    class CommandData(TypedDict):
        __rpc_command__: Literal[True]
        command: str
        nonce: int
        args: NotRequired[List[Any]]

    ResponseData = TypedDict(
        'ResponseData',
        {
            '__rpc_response': Literal[True],
            'nonce': int,
            'return': NotRequired[Any],
            'error': NotRequired[str],
        },
    )


ConnectionT = TypeVar('ConnectionT', bound='Connection')
