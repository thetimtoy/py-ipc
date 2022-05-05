from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import (
        Any,
        Awaitable,
        Callable,
    )
    from typing_extensions import Self


__all__ = ('ContextManagerMixin',)


class ContextManagerMixin:
    __slots__ = ()

    if TYPE_CHECKING:
        connect: Callable[..., Awaitable[Any]]
        close: Callable[..., Awaitable[Any]]

    async def __aenter__(self) -> Self:
        if hasattr(self, 'connect'):
            await self.connect()

        return self

    async def __aexit__(self, *exc_info: Any) -> None:
        await self.close()
