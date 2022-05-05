__all__ = (
    'IpcError',
    'IpcStreamsError',
    'NotConnected',
)


class IpcError(Exception):
    pass


class IpcStreamsError(IpcError):
    pass


class NotConnected(IpcStreamsError):
    pass
