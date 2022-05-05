from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import ipc

if TYPE_CHECKING:
    from typing import Any

server = ipc.Server(host='127.0.0.1', port=8000)


@server.listener('message')
async def on_message(connection: ipc.Connection, data: Any) -> None:
    print('Data received:', data)

    await asyncio.sleep(1)

    connection.send(data)


server.connect(run_sync=True)
