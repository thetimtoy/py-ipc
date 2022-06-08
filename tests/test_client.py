import types

import pytest

import ipc


@pytest.fixture
def client() -> ipc.Client:
    return ipc.Client('', 0)


def test_client(client: ipc.Client) -> None:
    assert client.host == ''
    assert client.port == 0
    assert not client._paused
    assert client._write_buffer is None
    assert not hasattr(client, '_close_waiter')
    assert not hasattr(client, '_transport')
    assert repr(client) == '<Client host= port=0 connected=False>'


@pytest.mark.asyncio
async def test_client_connect(client: ipc.Client) -> None:
    # client.connected will return True
    class FakeTransport:
        def is_closing(self):
            return False

    client._transport = FakeTransport()  # type: ignore

    coro = client.connect()

    try:
        assert isinstance(coro, types.CoroutineType)
        assert await coro is client
        assert client.connect(run_sync=True) is client
    finally:
        coro.close()


def test_client_default_disconnect_handler(client: ipc.Client) -> None:
    exc = RuntimeError('test error')
    with pytest.raises(RuntimeError, match=exc.args[0]):
        client.on_disconnect(exc)

    client.on_disconnect(None)
