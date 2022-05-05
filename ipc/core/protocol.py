from collections import namedtuple
from typing import TYPE_CHECKING

__all__ = ('Protocol',)

if TYPE_CHECKING:
    from asyncio import (
        Protocol as StreamProtocol,
        Transport,
    )
    from typing import (
        Callable,
        Optional,
    )

    _ConnectionMadeCallback = Callable[[Transport], None]
    _ConnectionLostCallback = Callable[[Optional[Exception]], None]
    _DataReceivedCallback = Callable[[bytes], None]
    _EofReceivedCallback = Callable[[], bool]
    _UpdateWritingCallback = Callable[[], None]

    class Protocol(StreamProtocol):
        connection_made: _ConnectionMadeCallback
        connection_lost: _ConnectionLostCallback
        data_received: _DataReceivedCallback
        eof_received: _EofReceivedCallback
        pause_writing: _UpdateWritingCallback
        resume_writing: _UpdateWritingCallback

        def __new__(
            cls,
            *,
            connection_made: _ConnectionMadeCallback,
            connection_lost: _ConnectionLostCallback,
            data_received: _DataReceivedCallback,
            eof_received: _EofReceivedCallback,
            pause_writing: _UpdateWritingCallback,
            resume_writing: _UpdateWritingCallback,
        ) -> 'Protocol':
            ...

else:
    Protocol = namedtuple(
        'Protocol',
        [
            'connection_made',
            'connection_lost',
            'data_received',
            'eof_received',
            'pause_writing',
            'resume_writing',
        ],
    )
    """Represents a streaming protocol."""
