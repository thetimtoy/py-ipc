import asyncio

from ipc import rpc


client = rpc.Client('127.0.0.1', 8000)


@client.listener('connect')
async def on_connect2():
    # This is an experimental API. This example is
    # equivalent to client.invoke('qux', 123, bar=456)
    resp = await client.commands.qux(123, bar='456')

    print('qux response:', resp)

    try:
        resp = await client.invoke('foo')
        print('foo response:', resp)
    except asyncio.TimeoutError:
        print('foo timed out.')

    resp = await client.invoke('baz')

    print('baz response:', resp)

    await client.close()


@client.listener('connect')
def on_connect():
    print('Connected.')


@client.listener('disconnect', root=True)
def on_disconnect(exc):
    print('Disconnected.')


client.connect(run_sync=True)
