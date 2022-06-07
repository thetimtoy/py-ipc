import asyncio

from ipc import rpc


# listen on port 8000 @ 127.0.0.1
server = rpc.Server('127.0.0.1', 8000)


# Events


@server.listener('ready')
def on_ready():
    """Fired when the server is ready."""
    print('Server is ready.')


@server.listener('close')
def on_close():
    """Fired when the server is closed."""
    print('Server closed.')


@server.listener('connect')
def on_connect(conn):
    """Fired when an incoming connection has been established."""
    print(f'Connection {conn} opened ({len(server.connections)} open in total).')


@server.listener('disconnect')
def on_disconnect(conn, exc):
    """Fired when an incoming connection has been closed."""
    print(
        f'Connection {conn} closed ({len(server.connections)} open in total). exc: {exc}.'
    )


# Commands


# Create foo function (registered as command below)
# Invoked with .invoke('foo')
def foo(ctx):
    return 123


# Register the foo command (this is one way)
server.register(foo)


# Register the bar command (this is another way)
# Invoked with .invoke('bar', str, str)
@server.command('bar')
async def _bar(ctx, a, b):
    await asyncio.sleep(2)
    if not isinstance(a, str) or not isinstance(b, str):
        return -1

    return f'a={a} b={b}'


# Run the server and let the library manage the event loop
server.connect(run_sync=True)
