from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

__all__ = (
    'is_command',
    'is_response',
)


def is_command(data: Any) -> bool:
    return isinstance(data, dict) and '__rpc_command__' in data


def is_response(data: Any) -> bool:
    return isinstance(data, dict) and '__rpc_response__' in data
