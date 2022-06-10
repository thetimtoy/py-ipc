# This example is fundamentally identical to examples/rpc/server.py
# Except that we are using subclasses of rpc.Server
import asyncio

from ipc import rpc


class MyServer(rpc.Server):
    def __init__(self):
        # listen on port 8000 @ 127.0.0.1
        super().__init__('127.0.0.1', 8000)

        # self.foo() added as a command, with 'foo' (inferred) as the name
        self.register(self.foo)
        # self._bar() added as a command, with 'bar' (provided) as the name
        self.register('bar', self._bar)

    # Events

    def on_ready(self):
        """Fired when the server is ready."""
        print('Server is ready.')

    def on_connect(self, conn):
        """Fired when an incoming connection has been established."""
        print(f'Connection {conn} opened ({len(self.connections)} open in total).')

    def on_disconnect(self, conn, exc):
        """Fired when an incoming connection has been closed."""
        print(
            f'Connection {conn} closed ({len(self.connections)} open in total). exc: {exc}.'
        )

    # Commands

    # Invoked with .invoke('foo')
    def foo(self, ctx):
        return 123

    # Invoked with .invoke('bar', str, str)
    async def _bar(self, ctx, a, b):
        await asyncio.sleep(2)
        if not isinstance(a, str) or not isinstance(b, str):
            return -1

        return f'a={a} b={b}'


server = MyServer()

server.connect(run_sync=True)

print('Server closed.')
