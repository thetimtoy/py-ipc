import asyncio

from ipc import rpc


class Server(rpc.Server):
    def __init__(self):
        # pass the host and port to the super class
        super().__init__('127.0.0.1', 8000)

        self.add_command(self.baz)
        self.add_command('baz1', self.baz)

    def on_ready(self):
        print('Server is ready.')

    def on_close(self):
        print('Server closed.')

    def on_connect(self, conn):
        print(f'Connection {conn} opened ({len(self.connections)} open in total).')

    def on_disconnect(self, conn, exc):
        print(
            f'Connection {conn} closed ({len(self.connections)} open in total). exc: {exc}.'
        )

    def on_command_error(self, ctx: rpc.Context):
        ctx.error = getattr(ctx.error, 'original', ctx.error)

        super().on_command_error(ctx)

    # An async command
    @rpc.command()
    async def foo(self, ctx: rpc.Context):
        # A fake IO operation
        await asyncio.sleep(1.5)

        # Return a list of numbers
        return [1, 2, 3]

    # @rpc.command()
    def baz(self, ctx: rpc.Context):
        # await asyncio.sleep(3)

        return 'hi'  # [{'foo': 'bar', 'baz': 'qux', 'one': 'two'}] * 30

    # "bar" command that has a name not inherited from its callback
    # and some aliases
    # It returns a coroutine
    @rpc.command(name='bar', aliases=['noop', 'bar2'])
    def _bar_command(self, ctx: rpc.Context, *args, **kwargs):
        # self.foo is a a command object, call its .invoke() coroutine method
        return self.foo

    # command to add the "qux" command
    @rpc.command()
    def add_qux(self, ctx: rpc.Context):
        if self.get_command('qux') is None:
            self.add_command(qux)

        # return a plain string
        return 'added qux'


server = Server()

# This command would be called like so:
# await client.request('qux', 69, bar=420)
# Where "69" would be the "foo" arg and
# "bar=420" would be the "bar" kwarg
@rpc.command()
def qux(ctx: rpc.Context, foo, *, bar):
    assert foo == 123
    assert bar == '456'

    return ['qux'] * 5


# Add the "qux" command
server.add_command(qux)


# command to remove the "qux" command
@server.command()
def remove_qux(ctx: rpc.Context):
    server.remove_command('qux')

    # return a plain string
    return 'removed qux'


# Let the library manage the startup + cleanup with
# "run_sync" set to True
server.connect(run_sync=True)
