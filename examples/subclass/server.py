# This example is fundamentally identical to examples/server.py
# Except that we are using subclasses of ipc.Server
import ipc


class MyServer(ipc.Server):
    def __init__(self):
        super().__init__('127.0.0.1', 8000)

    def on_ready(self):
        """Fired when the server is ready."""
        print('Server is ready.')

    async def on_connect(self, conn):
        """Fired when an incoming connection has been established."""
        print(f'Connection {conn} opened.')

        # .recv() here returns when the other side uses .send()
        d = await conn.recv()

        print('Data received:', d)

        to_send = ['bar']

        print('Sending:', to_send)

        # the client in client.py is waiting for a packet with .recv(), so we send one
        conn.send(to_send)

        # the client in client.py will close the connection soon, we will do nothing

    def on_disconnect(self, conn, exc):
        """Fired when an incoming connection has been closed."""
        # "exc" will be an Exception object if an error occured, else None
        print(f'Connection {conn} closed. exc: {exc}')


server = MyServer()

# Run the server and let the library manage the event loop
server.connect(run_sync=True)

print('Server closed.')
