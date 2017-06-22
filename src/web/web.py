#! /usr/bin/env python
# coding=utf-8
import functools
import asyncio
import inspect
import logging
from urllib import parse
logging.basicConfig(level=logging.INFO)


def get(path):
    """define get(`path`) decorator"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(args, **kwargs):
            return func(args, **kwargs)

        wrapper.__method__ = 'GET'
        wrapper.__route__ = path
        return wrapper

    return decorator


def post(path):
    """define post decorator post(path)"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(args, **kwargs):
            return func(args, **kwargs)

        wrapper.__method__ = 'POST'
        wrapper.__route__ = path
        return wrapper

    return decorator


class RequestHandler(object):
    def __init__(self, app, fn):
        self._app = app
        self._func = fn

    @asyncio.coroutine
    def __call__(self, request):
        kw = ''
        if self._func.__method__ == 'GET':
            kw = dict()
            qs = request.query_string
            for k, v in parse.parse_qs(qs, True).items():
                kw[k] = v[0]
        r = yield from self._func((), **kw)
        return r


def add_route(app, fn):
    method = getattr(fn, '__method__', None)
    path = getattr(fn, '__route__', None)

    if method is None or method is None:
        raise ValueError('@get or @post not defined in %s' % str(fn))

    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)

    logging.info(
        'add route %s %s => %s(%s)' % (method, path, fn.__name__, ', '.join(inspect.signature(fn).parameters.keys())))

    app.router.add_route(method, path, RequestHandler(app, fn))


# 自动扫描并注册handlers
def add_routes(app, module_name):
    index = module_name.rfind('.')
    if index == -1:
        mod = __import__(module_name, globals(), locals())
    else:
        name = module_name[index + 1:]
        mod = getattr(__import__(module_name[:index], globals(), locals(), [name]), name)
    for attr in dir(mod):
        if attr.startswith('__'):
            continue
        fn = getattr(mod, attr)
        if callable(fn):
            method = getattr(fn, '__method__', None)
            path = getattr(fn, '__route__', None)
            if method and path:
                add_route(app, fn)
