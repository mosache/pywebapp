#! /usr/bin/env python
# coding=utf-8
import asyncio
import logging
import json
from aiohttp import web

logging.basicConfig(level=logging.INFO)


# 日志
@asyncio.coroutine
def logger_factory(app, handler):
    @asyncio.coroutine
    def logger(request):
        # 记录日志
        logging.info('Request : %s %s' % (request.method, request.path))
        return (yield from handler(request))

    return logger


# 把response转换为web.Response
@asyncio.coroutine
def response_factory(app, handler):
    @asyncio.coroutine
    def response(request):
        r = yield from handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        elif isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        elif isinstance(r, str):
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        elif isinstance(r, dict):
            template = r['__template__']
            if template is None:
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda o: o.__dict__).encode('utf-8'))
                resp.content_type = 'application/json;charset=utf-8'
                return resp
            else:
                resp = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type = 'text/html;charset'
                return resp
        # default
            resp = web.Response(body=str(r).encode('utf-8'))
            resp.content_type = 'text/plain;charset=utf-8'
            return resp
    return response
