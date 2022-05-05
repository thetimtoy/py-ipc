import asyncio

import ipc


async def main():
    async with ipc.Client('127.0.0.1', 8000) as client:
        data = 'foo'

        print('Sending:', data)

        client.send(data)

        print('Data received:', await client.recv())


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
