try:
    import uvloop  # type: ignore
except ImportError:
    pass
else:
    import asyncio

    if not isinstance(asyncio.get_event_loop_policy(), uvloop.EventLoopPolicy):
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
