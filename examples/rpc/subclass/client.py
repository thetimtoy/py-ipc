# This example is fundamentally identical to examples/rpc/client.py
# Except that we are using subclasses of rpc.Client
from ipc import rpc


class MyClient(rpc.Client):
    def __init__(self):
        # connect to port 8000 on 127.0.0.1
        super().__init__('127.0.0.1', 8000)

    async def on_connect(self):
        """Fired when this client has connected to a server."""
        print('Client is connected.')

        d = await self.invoke('foo')

        print(f'command foo response: {d}.')

        d = await self.commands.bar('apple', 'orange')

        print(f'command bar response: {d}.')

        d = await self.commands.bar(1, 2)  # wrong args!
        # "d" will be -1 because our server checks isinstance(arg, str)
        # and returns it if it fails. just pretty basic error handling.

        print(f'command bar response (wrong args): {d}.')

        print('Closing connection...')
        await self.close()


client = MyClient()

client.connect(run_sync=True)
