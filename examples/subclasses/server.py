from __future__ import annotations

import time
from typing import TYPE_CHECKING

import ipc

if TYPE_CHECKING:
    from typing import Optional


class Connection(ipc.Connection):
    server: 'Server'

    async def on_connect(self):
        print('Connected.')
        self.created_at = time.perf_counter()

        self.id = self.server.get_id()
        self.name = self.server.get_name()

        self.send([self.id, self.name])

        print(f'Sent id {self.id} and name {self.name}.')

        predicate = lambda d: d == 'ack'

        self.send('Hey there!')

        await self.recv(predicate=predicate)

        print('First message acknowledged.')

        self.send('Ok bye!')

        await self.recv(predicate=predicate)

        print('Second message acknowledged, closing connection.')

        await self.close()

    def on_disconnect(self, exc: Optional[Exception]):
        delta = (time.perf_counter() - self.created_at) * 1000

        print(f'Connection closed. Session lasted for: {round(delta, 3)}ms')

        if exc is not None:
            raise exc


names = [
    'apple',
    'banana',
    'pear',
    'cherry',
    'pineapple',
    'strawberry',
]


class Server(ipc.Server):
    def __init__(self) -> None:
        super().__init__(
            host='127.0.0.1',
            port=8000,
            connection_factory=Connection,
        )

        self.current_id = 0
        self.names = iter(names)

    def get_id(self) -> int:
        ret = self.current_id

        self.current_id += 1

        return ret

    def get_name(self) -> str:
        try:
            return next(self.names)
        except StopIteration:
            self.names = iter(names)

            return self.get_name()

    def on_ready(self):
        print(f'Server is ready. Listening for connections @ {self.host}:{self.port}')

    def on_close(self):
        print('Server closed.')


server = Server()

server.connect(run_sync=True)
