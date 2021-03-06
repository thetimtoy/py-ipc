from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    TypeVar,
)

from ipc.core.utils import maybe_awaitable
from ipc.rpc.errors import (
    CommandError,
    CommandInvokeError,
    CommandNotFound,
)

if TYPE_CHECKING:
    from typing import (
        Any,
        List,
        Optional,
    )
    from typing_extensions import Self

    from ipc.core.connection import Connection
    from ipc.rpc.server import Server
    from ipc.rpc.types import (
        CommandData,
        CommandFunc,
        ResponseData,
    )

__all__ = ('Context',)


class Context:
    if TYPE_CHECKING:
        _nonce: int
        args: List[str]
        command: Optional[CommandFunc]
        error: Optional[CommandError]
        _responded: bool

    error = None
    _responded = False

    def __init__(
        self,
        server: Server,
        connection: Connection,
        data: CommandData,
    ) -> None:
        self.connection = connection
        self.server = server
        self._nonce = data['nonce']
        self.args = data.get('args', [])
        self.command_name = data['command']
        self.command = self.server.commands.get(self.command_name)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        await self.connection.close()

        return self

    async def invoke(self) -> None:
        self.server.dispatch('command', self)

        command = self.command

        try:
            if command is None:
                raise CommandNotFound(self.command_name)

            ret = await maybe_awaitable(command, self, *self.args)

            if not self._responded:
                self.respond(ret)

            self.server.dispatch('command_success', self)

        except Exception as exc:
            if not isinstance(exc, CommandError):
                exc = CommandInvokeError(exc)

            self.error = exc

            self.server.dispatch('command_error', self)

    def respond(self, data: Any, error: bool = False) -> Self:
        if self._responded:
            raise CommandError('Context has already been responded to.')

        response: ResponseData = {
            'nonce': self._nonce,
            '__rpc_response__': True,
        }

        if error:
            response['error'] = data
        else:
            response['return'] = data

        if self.connection.connected:
            self.connection.send(response)

        self._responded = True

        return self
