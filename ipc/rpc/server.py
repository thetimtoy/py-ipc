from __future__ import annotations

from sys import stderr
from traceback import print_exception
from typing import (
    TYPE_CHECKING,
    overload,
)

from ipc.core.server import Server as BaseServer
from ipc.core.types import ConnectionT
from ipc.core.utils import NULL
from ipc.rpc.context import Context
from ipc.rpc.errors import CommandAlreadyRegistered
from ipc.rpc.utils import is_command

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Dict,
        Optional,
        Union,
        TypeVar,
    )
    from typing_extensions import Self

    from ipc.rpc.types import CommandFunc

    CommandFuncT = TypeVar('CommandFuncT', bound=CommandFunc)

__all__ = ('Server',)


class Server(BaseServer[ConnectionT]):
    if TYPE_CHECKING:
        commands: Dict[str, CommandFunc]

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connection_factory: Callable[[Server], ConnectionT] = NULL,
    ) -> None:
        super().__init__(host, port, connection_factory=connection_factory)  # type: ignore

        self.commands = {}

    async def on_message(self, connection: ConnectionT, data: Any) -> None:
        await self.handle_command(connection, data)

    async def handle_command(
        self,
        connection: ConnectionT,
        data: Any,
        *,
        factory: Callable[[Self, ConnectionT, Any], Context] = Context,
    ) -> None:
        if not is_command(data):
            return

        ctx = factory(self, connection, data)

        await ctx.invoke()

    def on_command_error(self, ctx: Context) -> None:
        """The default ``command_error`` event listener.

        This listener prints to :data:`sys.stderr` and is fired
        when a command related error occurs.

        Parameters
        ----------
        ctx: :class:`.rpc.Context`
            The invocation context.
        """
        exc = ctx.error

        assert exc is not None

        ctx.respond(str(exc), error=True)

        print(f'IPC command {ctx.command_name} raised an exception:', file=stderr)
        print_exception(type(exc), exc, exc.__traceback__, file=stderr)

    if TYPE_CHECKING:

        @overload
        def command(
            self, command: Optional[str] = ...
        ) -> Callable[[CommandFuncT], CommandFuncT]:
            ...

        @overload
        def command(self, command: CommandFuncT) -> CommandFuncT:
            ...

    def command(self, command: Optional[Union[str, CommandFunc]] = None) -> Any:
        if not callable(command):

            def decorator(func):
                nonlocal command

                if isinstance(command, str):
                    name = command
                else:
                    name = func.__name__

                self.register(name, func)

                return command

            return decorator

        self.register(command)

        return command

    if TYPE_CHECKING:

        @overload
        def register(self, command: str, func: CommandFunc) -> Self:
            ...

        @overload
        def register(self, command: CommandFunc) -> Self:
            ...

    def register(
        self,
        command: Union[str, CommandFunc],
        func: CommandFunc = NULL,
    ) -> Self:
        """Register a command."""
        if isinstance(command, str):
            name = command
        elif callable(command):
            name = command.__name__
            func = command

        commands = self.commands

        if name in commands:
            raise CommandAlreadyRegistered(name, func)

        commands[name] = func

        return self

    def unregister(self, command_name: str) -> Self:
        """Unregister a command by a name or alias.

        Parameters
        ----------
        command_name: :class:`str`
            The command name.
        """
        try:
            del self.commands[command_name]
        except KeyError:
            pass

        return self
