import asyncio
import logging

from aiohttp import web

logging.basicConfig(level=logging.INFO)


def index(request):
    return web.Response(body=b'<h1>pywebapp</h1>', content_type='text/html')


@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET', '/', index)
    server = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server start at 127.0.0.1:9000')
    return server


mloop = asyncio.get_event_loop()
mloop.run_until_complete(init(mloop))
mloop.run_forever()
