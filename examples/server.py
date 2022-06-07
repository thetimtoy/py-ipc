import ipc


server = ipc.Server('127.0.0.1', 8000)


@server.listener('ready')
def on_ready():
    """Fired when the server is ready."""
    print('Server is ready.')


@server.listener('close')
def on_close():
    """Fired when the server is closed."""
    print('Server closed.')


@server.listener('connect')
async def on_connect(conn):
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


@server.listener('disconnect')
def on_disconnect(conn, exc):
    """Fired when an incoming connection has been closed."""
    # "exc" will be an Exception object if an error occured, else None
    print(f'Connection {conn} closed. exc: {exc}')


# Run the server and let the library manage the event loop
server.connect(run_sync=True)
