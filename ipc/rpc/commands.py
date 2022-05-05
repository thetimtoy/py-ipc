from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Generic,
    TypeVar,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        List,
        Optional,
        Type,
        Union,
        overload,
    )
    from typing_extensions import (
        Concatenate,
        ParamSpec,
    )

    from ipc.rpc.context import Context
    from ipc.rpc.server import Server

    P = ParamSpec('P')
    T2 = TypeVar('T2')
    CT = TypeVar('CT', bound='Command')
else:
    P = TypeVar('P')

__all__ = (
    'Command',
    'command',
)


T = TypeVar('T')
ServerT = TypeVar('ServerT', bound='Server')


class Command(Generic[ServerT, P, T]):
    if TYPE_CHECKING:
        _func: Union[
            Callable[Concatenate[ServerT, Context, P], T],
            Callable[Concatenate[Context, P], T],
        ]
        _server: Optional[ServerT]
        name: str
        aliases: List[str]

    _server = None

    def __init__(
        self,
        *,
        func: Union[
            Callable[Concatenate[ServerT, Context, P], T],
            Callable[Concatenate[Context, P], T],
        ],
        name: Optional[str] = None,
        aliases: Optional[List[str]] = None,
    ) -> None:
        self._func = func
        self.name = name if name is not None else func.__name__
        self.aliases = aliases if aliases is not None else []

    def __call__(self, ctx: Context, *args: P.args, **kwargs: P.kwargs) -> T:
        if self._func is None:
            raise RuntimeError(
                f'Command {self.name} without a callback cannot be invoked.'
            )

        # Types are ignored below, pyright just can't seem to understand it.
        if self._server is not None:
            return self._func(self._server, ctx, *args, **kwargs)  # type: ignore
        else:
            return self._func(ctx, *args, **kwargs)  # type: ignore

    def get_all_names(self) -> List[str]:
        return [self.name, *self.aliases]


if TYPE_CHECKING:

    @overload
    def command(
        **kwargs: Any,
    ) -> Callable[
        [
            Union[
                Callable[Concatenate[ServerT, Context, P], T],
                Callable[Concatenate[Context, P], T],
            ]
        ],
        Command[ServerT, P, T],
    ]:
        ...

    @overload
    def command(*, _cls: Type[CT], **kwargs: Any) -> Callable[[Callable[..., Any]], CT]:
        ...


def command(
    *,
    _cls: Type[CT] = Command,
    **kwargs: Any,
) -> Any:
    return lambda func: _cls(func=func, **kwargs)
