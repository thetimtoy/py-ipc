# This example is fundamentally identical to examples/client.py
# Except that we are using subclasses of ipc.Client
import ipc


class MyClient(ipc.Client):
    def __init__(self):
        super().__init__('127.0.0.1', 8000)

    async def on_connect(self):
        """Fired when the client is connected."""
        print('Client is connected.')

        to_send = 'foo'

        print('Sending:', to_send)

        # Send the 'foo' string (any JSON object is acceptable)
        self.send(to_send)

        # .recv() here returns when the other side uses .send()
        d = await self.recv()

        print('Data received:', d)

        print('Closing connection...')
        await self.close()


client = MyClient()

# Run the client and let the library manage the event loop
client.connect(run_sync=True)
