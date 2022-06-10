import ipc


client = ipc.Client('127.0.0.1', 8000)


@client.listener('connect')
async def on_connect():
    """Fired when the client is connected."""
    print('Client is connected.')

    data = 'foo'

    print('Sending:', data)

    # Send the 'foo' string (any JSON object is acceptable)
    client.send(data)

    # .recv() here returns when the other side uses .send()
    d = await client.recv()

    print('Data received:', d)

    print('Closing connection...')
    await client.close()


# Run the client and let the library manage the event loop
client.connect(run_sync=True)
