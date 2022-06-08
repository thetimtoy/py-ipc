import asyncio
import types


def fake_run(coro: types.CoroutineType):
    coro.close()


asyncio.run = fake_run
