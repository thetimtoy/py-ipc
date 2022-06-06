from __future__ import annotations

from asyncio import wait_for
from typing import TYPE_CHECKING

from ipc.core.client import Client as BaseClient
from ipc.core.utils import cached_property, future
from ipc.rpc.client_commands import ClientCommands
from ipc.rpc.errors import ServerError
from ipc.rpc.utils import is_response

if TYPE_CHECKING:
    from asyncio import Future
    from typing import (
        Any,
        Dict,
        Optional,
        TypeVar,
        Union,
    )
    from typing_extensions import Self
    
    from ipc.rpc.types import CommandData, ResponseData

    T = TypeVar('T')


__all__ = ('Client',)


class Client(BaseClient):
    """Subclass of :class:`ipc.Client` that provides an implementation
    for rpc command invocation. This should be used to connect to a :class:`rpc.Server`.
    That being said, you can do anything with this client that you can do with a regular
    :class:`ipc.Client`.
    """

    if TYPE_CHECKING:
        _nonce: int
        _response_waiters: Dict[int, Future[ResponseData]]
        options: Dict[str, Any]
        next_options: Dict[str, Any]

    def __init__(self, host: str, port: int, **kwargs: Any) -> None:
        super().__init__(host, port)

        self._nonce = 0
        self._response_waiters = {}
        self.options = kwargs.copy()
        self.next_options = {}

    def _get_option(self, key: str, default: Optional[T] = None) -> Union[Any, T]:
        if self.next_options is not None:
            try:
                return self.next_options[key]
            except KeyError:
                pass

        return default

    def on_message(self, data: Any) -> None:
        self.handle_response(data)

    def handle_response(self, data: Any) -> None:
        """Handle a received command response.

        This method serves as a helper to resolve the future
        that :meth:`.invoke` is waiting on.
        """
        if not is_response(data):
            return

        # If this fails, we have an unusable response.
        # Would only happen if user messes with it.
        nonce = data['nonce']

        try:
            fut = self._response_waiters.pop(nonce)
        except KeyError:
            pass
        else:
            if not fut.done():
                fut.set_result(data)

                # NOTE: Not sure about this event, might remove/update it
                self.dispatch('response', data)

    def set(self, **kwargs: Any) -> Self:
        """Update custom options for the next command invocation.

        These take precedence over :attr`.options`
        Any custom command options are reset when :meth:`.invoke` is called.

        Parameters
        ----------
        **kwargs: Any
            Data to update options with.

        Examples
        --------
        Usage ::

            client = rpc.Client(..., command_timeout=1)

            # This specific invocation times out after 5 seconds
            await client.set(timeout=5).invoke('foo', ...)

            # And this one follows the default timeout of 1 second
            await client.invoke('foo', ...)
        """
        self.next_options.update(**kwargs)

        return self

    def get_option(self, key: str, default: T = None) -> Union[Any, T]:
        """Get an option by ``key``, returning ``default`` if it does not exist.

        Looks up ``key`` in :attr:`.next_options` first, and then :attr:`.options`
        if that fails. :meth:`.invoke` uses this method to resolve the options it will use.

        Parameters
        ----------
        key: :class:`str`
            The lookup key.
        default: Any, default: None
            The fallback to use in the case ``key`` hasn't been set.
        """
        try:
            return self.next_options[key]
        except KeyError:
            pass

        try:
            return self.options[key]
        except KeyError:
            pass

        return default

    @cached_property('_commands')
    def commands(self) -> ClientCommands:
        return ClientCommands(self)

    async def invoke(self, command: str, *args: Any, **kwargs: Any) -> Any:
        """Invoke a command.

        Parameters
        ----------
        command: :class:`str`
            The name of the command you are attempting to invoke.
        *args: Any
            The positional arguments to pass to the command.
        **kwargs: Any
            The key word arguments to pass to the command.

        Examples
        --------
        Usage ::

            resp = await client.invoke('foo', 123, bar='qux')

            assert resp == [1, 2, 3]
        """
        nonce = self._nonce

        self._nonce = nonce + 1

        data: CommandData = {
            '__rpc_command__': True,
            'command': command,
            'nonce': nonce,
        }

        if args:
            data['args'] = list(args)

        self.send(data)

        fut: Future[ResponseData] = future()
        self._response_waiters[nonce] = fut

        timeout: Optional[float] = self.get_option('timeout')

        self.next_options.clear()

        try:
            response = await wait_for(fut, timeout=timeout)
        finally:
            if nonce in self._response_waiters:
                del self._response_waiters[nonce]

        if 'error' in response:
            raise ServerError(response['error'])

        return response.get('return', None)
