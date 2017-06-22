#! /usr/bin/env python
# coding=utf-8
from src.web.web import get, post
from src.beans.Models import User
import asyncio


@get('/')
@asyncio.coroutine
def index(request):
    users = yield from User.findAll()
    return {
        '__template__': 'test.html',
        'users': users
    }
