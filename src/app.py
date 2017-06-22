import asyncio
import logging
import os
from aiohttp import web
from jinja2 import Environment, FileSystemLoader
from src.web.middleware import logger_factory, response_factory
from src.web.web import add_routes
from src.db.db import create_pool
logging.basicConfig(level=logging.INFO)


def index(request):
    return web.Response(body=b'<h1>pywebapp</h1>', content_type='text/html')


def init_jinja2(app, **kw):
    logging.info('init jinja2..')
    options = dict(
        autoescape=kw.get('autoescape', True),
        block_start_string=kw.get('block_start_string', '{%'),
        block_end_string=kw.get('block_end_string', '%}'),
        variable_start_string=kw.get('variable_start_string', '{{'),
        variable_end_string=kw.get('variable_end_string', '}}'),
        auto_reload=kw.get('auto_reload', True)
    )
    path = kw.get('path', None)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    logging.info('set template path to %s' % path)

    env = Environment(loader=FileSystemLoader(path), **options)
    filters = kw.get('filters')
    if filters is not None:
        for name, f in filters.items():
            env.filters[name] = f
    app['__templating__'] = env


@asyncio.coroutine
def init(loop):
    yield from create_pool(loop=loop, host='127.0.0.1', port=3306, user='vurtne', password='911025', db='pytest')
    app = web.Application(loop=loop, middlewares=[logger_factory, response_factory])
    init_jinja2(app)
    add_routes(app, 'handlers')
    server = yield from loop.create_server(app.make_handler(), '127.0.0.1', 9000)
    logging.info('server start at 127.0.0.1:9000')
    return server


mloop = asyncio.get_event_loop()
mloop.run_until_complete(init(mloop))
mloop.run_forever()
