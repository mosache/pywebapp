import asyncio
import logging
import aiomysql


@asyncio.coroutine
def create_pool(loop, **kw):
    logging.info('create datebase connect pool')
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw.get('user'),
        password=kw.get('password'),
        db=kw.get('db'),
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )


async def destory_pool():
    if __pool is not None:
        __pool.close()
        await __pool.wait_closed()


@asyncio.coroutine
def select(sql, args, size=None):
    logging.info(sql, args)
    global __pool
    with(yield from __pool) as conn:
        cur = yield from conn.cursor(aiomysql.DictCursor)
        yield from cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = yield from cur.fetchmany(size)
        else:
            rs = yield from cur.fetchall()
        yield from cur.close()
        logging.info('rows returned: %s' % len(rs))
        return rs


@asyncio.coroutine
def execute(sql, args):
    logging.info(sql, args)
    global __pool
    with(yield from __pool) as conn:
        try:
            cur = yield from conn.cursor(aiomysql.DictCursor)
            yield from cur.execute(sql.replace('?', '%s'), args or ())
            affected = cur.rowcount
            yield from cur.close()
        except BaseException as e:
            raise
        return affected
