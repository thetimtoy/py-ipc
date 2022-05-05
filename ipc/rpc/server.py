from __future__ import annotations

from inspect import getmembers
from sys import stderr
from traceback import print_exception
from typing import (
    TYPE_CHECKING,
    Generic,
    overload,
)

from ipc.core.server import Server as BaseServer
from ipc.core.utils import NULL
from ipc.rpc.context import Context
from ipc.rpc.commands import Command
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
        commands: Dict[str, Command]
        connection_factory: Callable[[Self], ConnectionT]

    def __init__(
        self,
        host: str,
        port: int,
        *,
        connection_factory: Callable[[Self], ConnectionT] = NULL,
    ) -> None:
        super().__init__(host, port, connection_factory=connection_factory)

        self.commands = {}

        for _, v in getmembers(self, lambda o: isinstance(o, Command)):
            v: Command

            v._server = self

            self.add_command(v)

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

    def get_command(self, command_name: str) -> Optional[Command]:
        """Get a command by a name or alias.

        Parameters
        ----------
        command_name: :class:`str`
            The command name.
        """
        return self.commands.get(command_name)

    def command(self, command: Optional[Union[str, Callable[..., Any]]] = None) -> Any:
        if not callable(command):

            def decorator(func):
                nonlocal command
                
                if isinstance(command, str):
                    name = command
                else:
                    name = func.__name__

                command = Command(func=func, name=name)
                
                self.add_command(command)

                return command

            return decorator
        
        command = Command(func=command)

        self.add_command(command)

        return command

    if TYPE_CHECKING:

        @overload
        def add_command(self, command: str, func: Callable[..., Any]) -> Self:
            ...

        @overload
        def add_command(self, command: Callable[..., Any]) -> Self:
            ...

        @overload
        def add_command(self, command: Command) -> Self:
            ...

    def add_command(
        self,
        command: Union[str, Callable[..., Any], Command],
        func: Callable[..., Any] = NULL,
    ) -> Self:
        """Add a command."""
        if not isinstance(command, Command):
            if isinstance(command, str):
                name = command

                assert func is not NULL and not isinstance(func, Command)
            elif callable(command):
                name = command.__name__
                func = command

            command = Command(name=name, func=func)

        commands = self.commands

        for name in command.get_all_names():
            if name in commands:
                raise CommandAlreadyRegistered(name, command)

            commands[name] = command

        return self

    def remove_command(self, command_name: str) -> Self:
        """Remove a command by a name or alias.

        Parameters
        ----------
        command_name: :class:`str`
            The command name.
        """
        commands = self.commands

        try:
            command = commands[command_name]
        except KeyError:
            pass
        else:
            command._server = None

            for name in command.get_all_names():
                try:
                    del commands[name]
                except KeyError:
                    pass

        return self
