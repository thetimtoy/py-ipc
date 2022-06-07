from ipc import rpc


# connect to port 8000 on 127.0.0.1
client = rpc.Client('127.0.0.1', 8000)


@client.listener('connect')
async def on_connect():
    """Fired when this client has connected to a server."""
    print('Client is connected.')

    d = await client.invoke('foo')

    print(f'command foo response: {d}.')

    d = await client.commands.bar('apple', 'orange')

    print(f'command bar response: {d}.')

    d = await client.commands.bar(1, 2)  # wrong args!
    # "d" will be -1 because our server checks isinstance(arg, str)
    # and returns it if it fails. just pretty basic error handling.

    print(f'command bar response (wrong args): {d}.')

    print('Closing connection...')
    await client.close()


@client.listener('disconnect')
def on_disconnect(exc):
    """Fired when this client has disconnected from a server."""
    print(f'Client disconnected. exc: {exc}.')


# Run the client and let the library manage the event loop
client.connect(run_sync=True)
