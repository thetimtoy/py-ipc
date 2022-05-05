__title__ = 'ipc'
__author__ = 'thetimtoy'
__version__ = '0.1.0'
__license__ = 'MIT'
__copyright__ = 'Copyright 2022 thetimtoy'


from typing import TYPE_CHECKING

from ipc.core.utils import setup_lazy_imports

if TYPE_CHECKING:
    from ipc import rpc as rpc
    from ipc.core import utils as utils
    from ipc.core.client import *
    from ipc.core.connection import *
    from ipc.core.errors import *
    from ipc.core.server import *


setup_lazy_imports(
    globals(),
    {
        'Client': 'ipc.core.client',
        'Connection': 'ipc.core.connection',
        'Server': 'ipc.core.server',
        'utils': {
            'module': 'ipc.core.utils',
            'variable': '*',
        },
        (
            'IpcError',
            'IpcStreamsError',
            'NotConnected',
        ): 'ipc.core.errors',
        'rpc': {
            'module': 'ipc.rpc',
            'variable': '*',
        },
    },
)

del (
    TYPE_CHECKING,
    setup_lazy_imports,
)
