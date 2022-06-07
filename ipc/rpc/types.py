from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Protocol,
)
from typing_extensions import Literal, NotRequired, TypedDict


if TYPE_CHECKING:
    from ipc.rpc.context import Context

    class CommandData(TypedDict):
        __rpc_command__: Literal[True]
        command: str
        nonce: int
        args: NotRequired[List[Any]]

    ResponseData = TypedDict(
        'ResponseData',
        {
            '__rpc_response__': Literal[True],
            'nonce': int,
            'return': NotRequired[Any],
            'error': NotRequired[str],
        },
    )

    class CommandFunc(Protocol):
        __name__: str

        def __call__(self, ctx: Context, *args: Any) -> Any:
            ...
