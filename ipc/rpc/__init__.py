from typing import TYPE_CHECKING

from ipc.core.utils import setup_lazy_imports

if TYPE_CHECKING:
    from ipc.rpc.client import *
    from ipc.rpc.commands import *
    from ipc.rpc.context import *
    from ipc.rpc.errors import *
    from ipc.rpc.server import *

__all__ = (
    'Client',
    'Command',
    'command',
    'Context',
    'Server',
    'RpcError',
    'CommandAlreadyRegistered',
)


setup_lazy_imports(
    globals(),
    {
        'Client': 'ipc.rpc.client',
        'Server': 'ipc.rpc.server',
        'Context': 'ipc.rpc.context',
        (
            'Command',
            'command',
        ): 'ipc.rpc.commands',
        (
            'RpcError',
            'CommandAlreadyRegistered',
        ): 'ipc.rpc.errors',
        (
            'is_command',
            'is_response',
        ): 'ipc.rpc.utils',
    },
)


del (
    TYPE_CHECKING,
    setup_lazy_imports,
)
