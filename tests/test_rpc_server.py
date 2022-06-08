import re

import pytest

from ipc import rpc


@pytest.fixture
def server() -> rpc.Server:
    return rpc.Server('', 0)


def command(ctx: rpc.Context) -> None:
    pass


def test_rpc_server_register_func_only(server: rpc.Server) -> None:
    server.register(command)
    commands = server.commands

    assert 'command' in commands
    assert len(commands) == 1
    assert commands['command'] is command


def test_rpc_server_register_with_name(server: rpc.Server) -> None:
    server.register('', command)
    commands = server.commands

    assert '' in commands
    assert len(commands) == 1
    assert commands[''] is command


def test_rpc_server_register_decorator_func_only(server: rpc.Server) -> None:
    server.register()(command)
    commands = server.commands

    assert 'command' in commands
    assert len(commands) == 1
    assert commands['command'] is command


def test_rpc_server_register_decorator_with_name(server: rpc.Server) -> None:
    server.register('')(command)
    commands = server.commands

    assert '' in commands
    assert len(commands) == 1
    assert commands[''] is command


def test_rpc_server_unregister(server: rpc.Server) -> None:
    server.register('')(command)
    commands = server.commands

    assert '' in commands
    assert len(commands) == 1
    assert commands[''] is command

    server.unregister('')

    assert '' not in commands
    assert len(commands) == 0


def test_rpc_server_methods_return_self(server: rpc.Server) -> None:
    assert server.register('', command) is server
    assert server.unregister('') is server
    assert server.register(command) is server


def test_rpc_server_register_raise_command_already_registered(server: rpc.Server) -> None:
    server.register('', command)
    with pytest.raises(rpc.CommandAlreadyRegistered):
        server.register('', lambda ctx: None)


def test_rpc_server_register_decorator_no_call_raise_runtime_error(
    server: rpc.Server,
) -> None:
    @server.register  # type: ignore
    def command():
        pass

    commands = server.commands

    assert 'command' in commands
    assert len(commands) == 1
    assert commands['command'] is not server
    assert command is server

    msg = re.escape(
        'Server object is not callable. '
        'Did you mean to call a command instead? If so, make sure to '
        'call the register() method when using it as a decorator. '
        'It should look like "@register()", not "@register".'
    )

    with pytest.raises(RuntimeError, match=msg):
        command()
