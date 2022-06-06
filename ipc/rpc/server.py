from __future__ import annotations

from sys import stderr
from traceback import print_exception
from typing import (
    TYPE_CHECKING,
    Generic,
    overload,
)

from ipc.core.connection import Connection
from ipc.core.server import Server as BaseServer
from ipc.core.utils import NULL
from ipc.rpc.context import Context
from ipc.rpc.errors import CommandAlreadyRegistered
from ipc.rpc.types import ConnectionT
from ipc.rpc.utils import is_command

if TYPE_CHECKING:
    from typing import (
        Any,
        Callable,
        Dict,
        Optional,
        Union,
    )
    from typing_extensions import Self

__all__ = ('Server',)


class Server(Generic[ConnectionT], BaseServer[ConnectionT]):
    if TYPE_CHECKING:
        commands: Dict[str, Callable[..., Any]]
        connection_factory: Callable[[Self], ConnectionT]

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connection_factory: Callable[[Self], ConnectionT] = NULL,
    ) -> None:
        if connection_factory is NULL:
            connection_factory = Connection  # type: ignore
            
        super().__init__(host, port, connection_factory=connection_factory)

        self.commands = {}

    async def on_message(self, connection: ConnectionT, data: Any) -> None:
        await self.handle_command(connection, data)

    async def handle_command(
        self,
        connection: ConnectionT,
        data: Any,
        *,
        factory: Callable[[ConnectionT, Any], Context] = Context,
    ) -> None:
        if not is_command(data):
            return

        ctx = factory(connection, data)

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

    def command(self, command: Optional[Union[str, Callable[..., Any]]] = None) -> Any:
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
        def register(self, command: str, func: Callable[..., Any]) -> Self:
            ...

        @overload
        def register(self, command: Callable[..., Any]) -> Self:
            ...

    def register(
        self,
        command: Union[str, Callable[..., Any]],
        func: Callable[..., Any] = NULL,
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
