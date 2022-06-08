import types

import pytest

import ipc


@pytest.fixture
def server() -> ipc.Server:
    return ipc.Server('', 0)


def test_server(server: ipc.Server) -> None:
    assert server.host == ''
    assert server.port == 0
    assert server.connections is not server._connections
    assert repr(server) == '<Server host= port=0 connected=False connections=0>'


@pytest.mark.asyncio
async def test_server_connect(server: ipc.Server) -> None:
    server._connected = True
    coro = server.connect()

    try:
        assert isinstance(coro, types.CoroutineType)
        assert await coro is server
        assert server.connect(run_sync=True) is server
    finally:
        coro.close()


def test_server_default_disconnect_handler(server: ipc.Server) -> None:
    exc = RuntimeError('test error')
    with pytest.raises(RuntimeError, match=exc.args[0]):
        server.on_disconnect(None, exc)

    server.on_disconnect(None, None)
