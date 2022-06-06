from __future__ import annotations

from typing import TYPE_CHECKING, Any
from typing_extensions import TypeGuard

if TYPE_CHECKING:
    from ipc.rpc.types import CommandData, ResponseData

__all__ = (
    'is_command',
    'is_response',
)


def is_command(data: Any) -> TypeGuard[CommandData]:
    return isinstance(data, dict) and '__rpc_command__' in data


def is_response(data: Any) -> TypeGuard[ResponseData]:
    return isinstance(data, dict) and '__rpc_response__' in data
