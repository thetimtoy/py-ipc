import asyncio
import types

import pytest

from ipc import rpc, utils
from ipc.rpc.client_commands import ClientCommands


@pytest.fixture
def client() -> rpc.Client:
    return rpc.Client('', 0)


@pytest.mark.asyncio
async def test_rpc_client_invoke(
    client: rpc.Client, event_loop: asyncio.AbstractEventLoop
) -> None:
    class FakeTransport:
        def is_closing(self) -> bool:
            return False

        def write(self, _: bytes) -> None:
            pass

    client._transport = FakeTransport()  # type: ignore

    assert client._nonce == 0

    coro = client.commands.foo()
    try:
        assert isinstance(coro, types.CoroutineType)

        task = event_loop.create_task(coro)
        await asyncio.sleep(0)

        assert client._nonce == 1

        assert 0 in client._response_waiters
        fut = client._response_waiters[0]

        assert isinstance(fut, asyncio.Future)
        assert not fut.done()

        task.cancel()
        await asyncio.sleep(0)
        assert task.done()

    finally:
        coro.close()


def test_rpc_client_commands(client: rpc.Client) -> None:
    assert isinstance(rpc.Client.commands, utils._CachedProperty)
    assert not hasattr(client, '_commands')
    assert isinstance(client.commands, ClientCommands)
    assert hasattr(client, '_commands')
    assert callable(client.commands.foo)
    del client.commands
    assert not hasattr(client, '_commands')
    assert hasattr(client, 'commands')
