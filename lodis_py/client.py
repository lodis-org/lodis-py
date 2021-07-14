from enum import Enum
import logging

import requests
import mugen

from .error import CodeError, LodisError
from .util import u8x4_to_u32, u8x1_to_u8, u32_to_u8x4, i64_to_u8x8, to_bytes

logger = logging.getLogger(__name__)


class Command:
    # List
    LPUSH = "lpush"
    RPUSH = "rpush"
    LPOP = "lpop"
    RPOP = "rpop"
    RANDPOP = "randpop"
    LRANGE = "lrange"
    RRANGE = "rrange"
    LINDEX = "lindex"
    LRAND = "lrand"
    LLEN = "llen"
    LDEL = "ldel"
    LRM = "lrm"

    # Map
    HGET = "hget"
    HSET = "hset"
    HSETNX = "hsetnx"
    HGETALL = "hgetall"
    HMGET = "hmget"
    HMSET = "hmset"
    HINCRBY = "hincrby"
    HKEYS = "hkeys"
    HVALS = "hvals"
    HEXISTS = "hexists"
    HDEL = "hdel"
    HLEN = "hlen"
    HRM = "hrm"

    # ArrayMap
    ALPUSH = "alpush"
    ALPUSHNX = "alpushnx"
    ARPUSH = "arpush"
    ARPUSHNX = "arpushnx"
    AINCRBY = "aincrby"
    ALPOP = "alpop"
    ARPOP = "arpop"
    ARANDPOP = "arandpop"
    AGET = "aget"
    ARAND = "arand"
    ALRANGE = "alrange"
    ARRANGE = "arrange"
    AKEYS = "akeys"
    AVALS = "avals"
    AALL = "aall"
    AEXISTS = "aexists"
    ALEN = "alen"
    ADEL = "adel"
    ARM = "arm"
    # FLUSH = 'flush'


class ReturnType(Enum):
    Bytes = 0
    Bool = 1
    Int = 3
    List = 4
    # Some(v) or None
    ListOption = 5
    # key value pair
    Pair = 6
    # key value pairs
    Pairs = 7
    No = 8


class Response:
    def __init__(self, resp, return_type=ReturnType.Bytes):
        self._return_type = return_type
        self._value = None
        self._parse_db_response(resp)

    def _parse_db_response(self, resp):
        body = resp.content
        self._code = u8x1_to_u8(body[:1])

        # Check returned status
        if not self.is_success():
            self._error_code = body[:1].decode("utf-8")
            self._error_msg = body[1:].decode("utf-8")
            raise LodisError(self)

        # Bytes
        if self._return_type == ReturnType.Bytes:
            self._value = body[1:]
        # Bool
        elif self._return_type == ReturnType.Bool:
            self._value = u8x1_to_u8(body[1:2]) == 1
        # Int
        elif self._return_type == ReturnType.Int:
            self._value = u8x4_to_u32(body[1:5])
        # List
        elif self._return_type == ReturnType.List:
            index = 1
            vec = []
            N = len(body)
            while index < N:
                length = u8x4_to_u32(body[index : index + 4])
                val = body[index + 4 : index + 4 + length]
                vec.append(val)
                index += 4 + length
            self._value = vec
        # ListOption
        elif self._return_type == ReturnType.ListOption:
            index = 1
            vec = []
            N = len(body)
            while index < N:
                is_none = u8x1_to_u8(body[index : index + 1]) == 0
                index += 1
                if is_none:
                    vec.append(None)
                    continue

                length = u8x4_to_u32(body[index : index + 4])
                val = body[index + 4 : index + 4 + length]
                vec.append(val)
                index += 4 + length
            self._value = vec
        # Pair
        elif self._return_type == ReturnType.Pair:
            index = 1
            vec = []
            N = len(body)
            while index < N:
                length = u8x4_to_u32(body[index : index + 4])
                val = body[index + 4 : index + 4 + length]
                vec.append(val)
                index += 4 + length
            assert len(vec) == 0 or len(vec) == 2, "Returned Pair is wrong"
            self._value = vec
        # Pairs
        elif self._return_type == ReturnType.Pairs:
            index = 1
            vec = []
            N = len(body)
            while index < N:
                length = u8x4_to_u32(body[index : index + 4])
                val = body[index + 4 : index + 4 + length]
                vec.append(val)
                index += 4 + length
            assert len(vec) % 2 == 0, "Returned Pairs are wrong"
            self._value = [(vec[i * 2], vec[i * 2 + 1]) for i in range(len(vec) // 2)]
        # No
        elif self._return_type == ReturnType.No:
            self._value = None
        else:
            raise CodeError

    def value(self):
        return self._value

    def is_success(self):
        return self._code == 0


class LodisClient:
    def __init__(self, key_name, ip, port):
        self._ip = ip
        self._port = port
        self._session = requests.session()
        self._key_name = key_name

    @property
    def key_name(self):
        return self._key_name

    @key_name.setter
    def key_name(self, key_name):
        self._key_name = key_name

    def _request(self, url, data=None):
        _err: Exception = Exception()
        for _ in range(5):
            try:
                return self._session.post(url, data=data)
            except Exception as err:
                logger.error("Lodis: _request error: %s", err)
                _err = err
                continue
        raise _err

    def _db_url(self, command):
        url = f"http://{self._ip}:{self._port}/{command}/{self._key_name}"
        return url

    def _db_body(self, *args):
        body = b""
        for arg in args:
            arg_bytes = to_bytes(arg)
            t = u32_to_u8x4(len(arg_bytes)) + arg_bytes
            body += t
        return body

    # List
    def lpush(self, *values):
        assert len(values) != 0, "lpush: values is empty"

        url = self._db_url(Command.LPUSH)
        body = self._db_body(*values)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def rpush(self, *values):
        assert len(values) != 0, "rpush: values is empty"

        url = self._db_url(Command.RPUSH)
        body = self._db_body(*values)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def lpop(self):
        url = self._db_url(Command.LPOP)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Bytes)

    def rpop(self):
        url = self._db_url(Command.RPOP)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Bytes)

    def randpop(self):
        url = self._db_url(Command.RANDPOP)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Bytes)

    def lrange(self, start, end):
        """0 <= start, end < MAX_U32"""
        url = self._db_url(Command.LRANGE)
        body = self._db_body(u32_to_u8x4(start), u32_to_u8x4(end))
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.List)

    def rrange(self, start, end):
        """0 <= start, end < MAX_U32"""
        url = self._db_url(Command.RRANGE)
        body = self._db_body(u32_to_u8x4(start), u32_to_u8x4(end))
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.List)

    def lindex(self, index):
        """0 <= index < MAX_U32"""
        url = self._db_url(Command.LINDEX)
        body = self._db_body(i64_to_u8x8(index))
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Bytes)

    def lrand(self):
        """ Randomly getting an item"""
        url = self._db_url(Command.LRAND)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Bytes)

    def llen(self):
        url = self._db_url(Command.LLEN)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Int)

    def ldel(self, index):
        """0 <= index < MAX_U32"""
        url = self._db_url(Command.LDEL)
        body = self._db_body(u32_to_u8x4(index))
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def lrm(self):
        """Remove the list from lodis"""
        url = self._db_url(Command.LRM)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.No)

    # Map
    def hget(self, key):
        url = self._db_url(Command.HGET)
        body = self._db_body(key)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Bytes)

    def hset(self, key, value):
        url = self._db_url(Command.HSET)
        body = self._db_body(key, value)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def hsetnx(self, key, value):
        url = self._db_url(Command.HSETNX)
        body = self._db_body(key, value)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def hgetall(self):
        url = self._db_url(Command.HGETALL)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pairs)

    def hmget(self, *keys):
        assert len(keys) != 0, "hmget: keys is empty"

        url = self._db_url(Command.HMGET)
        body = self._db_body(*keys)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.ListOption)

    def hmset(self, *pairs):
        """pairs = [(k1, v1), (k2, v2), ...]"""

        assert len(pairs) != 0, "hmset: pairs is empty"

        url = self._db_url(Command.HMSET)
        body = self._db_body(*[i for pair in pairs for i in pair])
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def hkeys(self):
        url = self._db_url(Command.HKEYS)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.List)

    def hvals(self):
        url = self._db_url(Command.HVALS)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.List)

    def hexists(self, key):
        url = self._db_url(Command.HEXISTS)
        body = self._db_body(key)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Bool)

    def hdel(self, key):
        url = self._db_url(Command.HDEL)
        body = self._db_body(key)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def hlen(self):
        url = self._db_url(Command.HLEN)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Int)

    def hrm(self):
        """Remove the map from lodis"""
        url = self._db_url(Command.HRM)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.No)

    # ArrayMap
    def alpush(self, *pairs):
        """pairs = [(k1, v1), (k2, v2), ...]"""

        assert len(pairs) != 0, "alpush: pairs is empty"

        url = self._db_url(Command.ALPUSH)
        body = self._db_body(*[i for pair in pairs for i in pair])
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def alpushnx(self, *pairs):
        """pairs = [(k1, v1), (k2, v2), ...]"""

        assert len(pairs) != 0, "alpushnx: pairs is empty"

        url = self._db_url(Command.ALPUSHNX)
        body = self._db_body(*[i for pair in pairs for i in pair])
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def arpush(self, *pairs):
        """pairs = [(k1, v1), (k2, v2), ...]"""

        assert len(pairs) != 0, "arpush: pairs is empty"

        url = self._db_url(Command.ARPUSH)
        body = self._db_body(*[i for pair in pairs for i in pair])
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def arpushnx(self, *pairs):
        """pairs = [(k1, v1), (k2, v2), ...]"""

        assert len(pairs) != 0, "arpushnx: pairs is empty"

        url = self._db_url(Command.ARPUSHNX)
        body = self._db_body(*[i for pair in pairs for i in pair])
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def alpop(self):
        url = self._db_url(Command.ALPOP)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pair)

    def arpop(self):
        url = self._db_url(Command.ARPOP)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pair)

    def arandpop(self):
        url = self._db_url(Command.ARANDPOP)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pair)

    def aget(self, key):
        url = self._db_url(Command.AGET)
        body = self._db_body(key)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Bytes)

    def arand(self):
        """ Randomly getting an item"""

        url = self._db_url(Command.ARAND)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pair)

    def alrange(self, start, end):
        """0 <= start, end < MAX_U32"""

        url = self._db_url(Command.ALRANGE)
        body = self._db_body(u32_to_u8x4(start), u32_to_u8x4(end))
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Pairs)

    def arrange(self, start, end):
        """0 <= start, end < MAX_U32"""

        url = self._db_url(Command.ARRANGE)
        body = self._db_body(u32_to_u8x4(start), u32_to_u8x4(end))
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Pairs)

    def akeys(self):
        url = self._db_url(Command.AKEYS)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.List)

    def avals(self):
        url = self._db_url(Command.AVALS)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.List)

    def aall(self):
        url = self._db_url(Command.AALL)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pairs)

    def aexists(self, key):
        url = self._db_url(Command.AEXISTS)
        body = self._db_body(key)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Bool)

    def alen(self):
        url = self._db_url(Command.ALEN)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Int)

    def adel(self, key):
        url = self._db_url(Command.ADEL)
        body = self._db_body(key)
        resp = self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    def arm(self):
        """Remove the arraymap from lodis"""
        url = self._db_url(Command.ARM)
        resp = self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.No)

    def flush(self):
        raise NotImplementedError("Can't use the method directly")


class AsyncLodisClient:
    def __init__(self, key_name, ip, port, loop=None):
        self._ip = ip
        self._port = port
        self._session = mugen.session(loop=loop)
        self._key_name = key_name

    @property
    def key_name(self):
        return self._key_name

    @key_name.setter
    def key_name(self, key_name):
        self._key_name = key_name

    async def _request(self, url, data=None):
        _err: Exception = Exception()
        for _ in range(5):
            try:
                return await self._session.post(url, data=data)
            except Exception as err:
                _err = err
                continue

        logger.error("Lodis: _request error: %s", _err)
        raise _err

    def _db_url(self, command):
        url = f"http://{self._ip}:{self._port}/{command}/{self._key_name}"
        return url

    def _db_body(self, *args):
        body = b""
        for arg in args:
            arg_bytes = to_bytes(arg)
            t = u32_to_u8x4(len(arg_bytes)) + arg_bytes
            body += t
        return body

    # List
    async def lpush(self, *values):
        assert len(values) != 0, "lpush: values is empty"

        url = self._db_url(Command.LPUSH)
        body = self._db_body(*values)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def rpush(self, *values):
        assert len(values) != 0, "rpush: values is empty"

        url = self._db_url(Command.RPUSH)
        body = self._db_body(*values)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def lpop(self):
        url = self._db_url(Command.LPOP)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Bytes)

    async def rpop(self):
        url = self._db_url(Command.RPOP)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Bytes)

    async def randpop(self):
        url = self._db_url(Command.RANDPOP)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Bytes)

    async def lrange(self, start, end):
        """0 <= start, end < MAX_U32"""
        url = self._db_url(Command.LRANGE)
        body = self._db_body(u32_to_u8x4(start), u32_to_u8x4(end))
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.List)

    async def rrange(self, start, end):
        """0 <= start, end < MAX_U32"""
        url = self._db_url(Command.RRANGE)
        body = self._db_body(u32_to_u8x4(start), u32_to_u8x4(end))
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.List)

    async def lindex(self, index):
        """0 <= index < MAX_U32"""
        url = self._db_url(Command.LINDEX)
        body = self._db_body(i64_to_u8x8(index))
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Bytes)

    async def lrand(self):
        """ Randomly getting an item"""
        url = self._db_url(Command.LRAND)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Bytes)

    async def llen(self):
        url = self._db_url(Command.LLEN)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Int)

    async def ldel(self, index):
        """0 <= index < MAX_U32"""
        url = self._db_url(Command.LDEL)
        body = self._db_body(u32_to_u8x4(index))
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def lrm(self):
        """Remove the list from lodis"""
        url = self._db_url(Command.LRM)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.No)

    # Map
    async def hget(self, key):
        url = self._db_url(Command.HGET)
        body = self._db_body(key)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Bytes)

    async def hset(self, key, value):
        url = self._db_url(Command.HSET)
        body = self._db_body(key, value)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def hsetnx(self, key, value):
        url = self._db_url(Command.HSETNX)
        body = self._db_body(key, value)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def hgetall(self):
        url = self._db_url(Command.HGETALL)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pairs)

    async def hmget(self, *keys):
        assert len(keys) != 0, "hmget: keys is empty"

        url = self._db_url(Command.HMGET)
        body = self._db_body(*keys)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.ListOption)

    async def hmset(self, *pairs):
        """pairs = [(k1, v1), (k2, v2), ...]"""

        assert len(pairs) != 0, "hmset: pairs is empty"

        url = self._db_url(Command.HMSET)
        body = self._db_body(*[i for pair in pairs for i in pair])
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def hincrby(self, key, incr):
        """incr is int"""

        assert isinstance(incr, int)

        url = self._db_url(Command.HINCRBY)
        body = self._db_body(key, str(incr))
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def hkeys(self):
        url = self._db_url(Command.HKEYS)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.List)

    async def hvals(self):
        url = self._db_url(Command.HVALS)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.List)

    async def hexists(self, key):
        url = self._db_url(Command.HEXISTS)
        body = self._db_body(key)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Bool)

    async def hdel(self, key):
        url = self._db_url(Command.HDEL)
        body = self._db_body(key)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def hlen(self):
        url = self._db_url(Command.HLEN)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Int)

    async def hrm(self):
        """Remove the map from lodis"""
        url = self._db_url(Command.HRM)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.No)

    # ArrayMap
    async def alpush(self, *pairs):
        """pairs = [(k1, v1), (k2, v2), ...]"""

        assert len(pairs) != 0, "alpush: pairs is empty"

        url = self._db_url(Command.ALPUSH)
        body = self._db_body(*[i for pair in pairs for i in pair])
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def alpushnx(self, *pairs):
        """pairs = [(k1, v1), (k2, v2), ...]"""

        assert len(pairs) != 0, "alpushnx: pairs is empty"

        url = self._db_url(Command.ALPUSHNX)
        body = self._db_body(*[i for pair in pairs for i in pair])
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def arpush(self, *pairs):
        """pairs = [(k1, v1), (k2, v2), ...]"""

        assert len(pairs) != 0, "arpush: pairs is empty"

        url = self._db_url(Command.ARPUSH)
        body = self._db_body(*[i for pair in pairs for i in pair])
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def arpushnx(self, *pairs):
        """pairs = [(k1, v1), (k2, v2), ...]"""

        assert len(pairs) != 0, "arpushnx: pairs is empty"

        url = self._db_url(Command.ARPUSHNX)
        body = self._db_body(*[i for pair in pairs for i in pair])
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def aincrby(self, key, incr):
        """incr is int"""
        assert isinstance(incr, int)

        url = self._db_url(Command.AINCRBY)
        body = self._db_body(key, str(incr))
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def alpop(self):
        url = self._db_url(Command.ALPOP)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pair)

    async def arpop(self):
        url = self._db_url(Command.ARPOP)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pair)

    async def arandpop(self):
        url = self._db_url(Command.ARANDPOP)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pair)

    async def aget(self, key):
        url = self._db_url(Command.AGET)
        body = self._db_body(key)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Bytes)

    async def arand(self):
        """ Randomly getting an item"""
        url = self._db_url(Command.ARAND)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pair)

    async def alrange(self, start, end):
        """0 <= start, end < MAX_U32"""

        url = self._db_url(Command.ALRANGE)
        body = self._db_body(u32_to_u8x4(start), u32_to_u8x4(end))
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Pairs)

    async def arrange(self, start, end):
        """0 <= start, end < MAX_U32"""

        url = self._db_url(Command.ARRANGE)
        body = self._db_body(u32_to_u8x4(start), u32_to_u8x4(end))
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Pairs)

    async def akeys(self):
        url = self._db_url(Command.AKEYS)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.List)

    async def avals(self):
        url = self._db_url(Command.AVALS)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.List)

    async def aall(self):
        url = self._db_url(Command.AALL)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Pairs)

    async def aexists(self, key):
        url = self._db_url(Command.AEXISTS)
        body = self._db_body(key)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.Bool)

    async def alen(self):
        url = self._db_url(Command.ALEN)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.Int)

    async def adel(self, key):
        url = self._db_url(Command.ADEL)
        body = self._db_body(key)
        resp = await self._request(url, data=body)
        return Response(resp, return_type=ReturnType.No)

    async def arm(self):
        """Remove the arraymap from lodis"""
        url = self._db_url(Command.ARM)
        resp = await self._request(url, data=b"")
        return Response(resp, return_type=ReturnType.No)

    async def flush(self):
        raise NotImplementedError("Can't use the method directly")
