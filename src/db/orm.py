#! /usr/bin/env python
# coding=utf-8
import logging
import asyncio
from src.db.db import select
from src.db.db import execute


# 根据输入的数字生成占位字符串
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')

    return ','.join(L)


# Model类的元类
class ModelMetaClass(type):
    def __new__(cls, name, bases, attrs):
        # 排除Model类本身
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)
        # 表名
        tableName = attrs.get('__table__', None) or name
        logging.info('found Model name %s (table : %s)' % (name, tableName))
        # 获取所有属性和列名
        mappings = dict()
        fields = []
        primarykey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('found mapping (%s:%s)' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # 找到主键
                    if primarykey:
                        raise RuntimeError('duplicate primary key for field %s' % k)
                    else:
                        primarykey = k

                else:
                    fields.append(k)
        if not primarykey:
            raise RuntimeError('primary key not defined!')
        # 将列名从属性中去除
        for k in mappings.keys():
            attrs.pop(k)

        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primarykey
        attrs['__fields__'] = fields
        # 默认select，insert , update, delete语句
        attrs['__select__'] = 'select %s,%s from %s' % (primarykey, ','.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into %s (%s , %s) values (%s)' % (tableName, ','.join(escaped_fields), primarykey,
                                                                        create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (
            tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primarykey)

        attrs['__delete__'] = 'delete from %s where %s = ?' % (tableName, primarykey)
        return type.__new__(cls, name, bases, attrs)


# 所有实体类的基类
class Model(dict, metaclass=ModelMetaClass):
    def __init__(self, **kw):
        super().__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r'Model object has no attr named %s' % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            filed = self.__mappings__[key]
            if filed.default is not None:
                value = filed.default() if callable(filed.default) else filed.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value

    # 定义数据库方法
    @classmethod
    @asyncio.coroutine
    def find(cls, pk):
        """ find object by primary key """
        rs = yield from select('%s where %s = ?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])

    @classmethod
    async def findAll(cls):
        rs = await select('%s' % cls.__select__, [])
        return [cls(**r) for r in rs]

    @asyncio.coroutine
    def save(self):
        """ save object into database"""
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        row = yield from execute(self.__insert__, args)
        if row != 1:
            logging.warning('`insert` into database error with affect row %d' % row)


class Field(object):
    def __init__(self, name, colunm_type, primary_key, default):
        self.name = name
        self.colunm_type = colunm_type
        self.primary_key = primary_key
        self.default = default

    def __str__(self):
        return '<%s, %s : %s>' % (self.__class__.__name__, self.colunm_type, self.name)


class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)


class IntegerField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='bigint'):
        super().__init__(name, ddl, primary_key, default)


class FloatField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='real'):
        super().__init__(name, ddl, primary_key, default)


class BooleanField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='boolean'):
        super().__init__(name, ddl, primary_key, default)


class TextField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='text'):
        super().__init__(name, ddl, primary_key, default)