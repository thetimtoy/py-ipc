from ipc.rpc import utils


def test_rpc_utils_is_command() -> None:
    assert not utils.is_command(None)
    assert not utils.is_command({})
    assert utils.is_command({'__rpc_command__': None})


def test_rpc_utils_is_response() -> None:
    assert not utils.is_response(None)
    assert not utils.is_response({})
    assert utils.is_response({'__rpc_response__': None})
