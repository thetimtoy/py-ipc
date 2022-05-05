from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import ipc

if TYPE_CHECKING:
    from typing import Any, Optional


class Client(ipc.Client):
    def __init__(self) -> None:
        super().__init__(host='127.0.0.1', port=8000)

    def on_connect(self) -> None:
        print('Connected.')

    def on_disconnect(self, exc: Optional[Exception]) -> None:
        print('Disconnected.')

        if exc is not None:
            ...

    def on_message(self, data: Any) -> None:
        print('Data received:', data)

        if isinstance(data, list):
            self.id, self.name = data

            print(f'Received id {self.id} and name {self.name}.')

            return

        self.send('ack')


client = Client()

client.connect(run_sync=True)  # Run until the server-end closes the signal
