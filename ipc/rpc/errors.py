from __future__ import annotations

from typing import TYPE_CHECKING

from ipc.core.errors import IpcError

__all__ = (
    'RpcError',
    'CommandAlreadyRegistered',
)


class RpcError(IpcError):
    pass


class CommandError(RpcError):
    pass


class CommandAlreadyRegistered(CommandError):
    pass


class CommandInvokeError(CommandError):
    if TYPE_CHECKING:
        original: Exception

    def __init__(self, exc: Exception) -> None:
        self.original = exc
        super().__init__(
            f'Command raised an exception: {type(exc).__name__}: {exc}',
        )


class ServerError(CommandError):
    pass


class CommandNotFound(CommandError):
    if TYPE_CHECKING:
        command_name: str

    def __init__(self, command_name: str) -> None:
        self.command_name = command_name

        super().__init__(
            f'Command {command_name} not found.',
        )
