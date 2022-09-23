"""
根据http.cookies做了一点小修改
原先包中获取数据时会加上一个‘Set-Cookie:’，并且以"\015\012"拼接数据
修改之后返回数据时用;连接
"""
from http import cookies
from http.cookies import Morsel, BaseCookie
import uuid
import urllib.parse
import sched
import threading
import time


class _Morsel(Morsel):
    """
    重写了Morsel的output方法，让他输出是不会带上header
    """
    def output(self, attrs=None, header=""):
        return self.OutputString(attrs)

    __str__ = output

    def OutputString(self, attrs=None):
        # Build up our result
        #
        result = []
        append = result.append

        # First, the key=value pair
        append("%s=%s" % (self.key, self.coded_value))

        # Now add any defined attributes
        if attrs is None:
            attrs = self._reserved
        items = sorted(self.items())
        for key, value in items:
            if value == "":
                continue
            if key not in attrs:
                continue
            if key == "expires" and isinstance(value, int):
                append("%s=%s" % (self._reserved[key], cookies._getdate(value)))
            elif key == "max-age" and isinstance(value, int):
                append("%s=%d" % (self._reserved[key], value))
            elif key == "comment" and isinstance(value, str):
                append("%s=%s" % (self._reserved[key], cookies._quote(value)))
            elif key in self._flags:
                if value:
                    append(str(self._reserved[key]))
            else:
                append("%s=%s" % (self._reserved[key], value))

        # Return the result
        return cookies._semispacejoin(result)


class _BaseCookie(BaseCookie):
    """
    重写了set方法，在添加新值时创建value对象用_Morsel
    重写了Morsel的output方法，让他输出是不会带上回车
    """
    def __set(self, key, real_value, coded_value):
        """Private method for setting a cookie's value"""
        M = self.get(key, _Morsel())
        M.set(key, real_value, coded_value)
        dict.__setitem__(self, key, M)

    def __setitem__(self, key, value):
        """Dictionary style assignment."""
        if isinstance(value, _Morsel):
            # allow assignment of constructed Morsels (e.g. for pickling)
            dict.__setitem__(self, key, value)
        else:
            rval, cval = self.value_encode(value)
            self.__set(key, rval, cval)

    def output(self, attrs=None, header="", sep=";"):
        """Return a string suitable for HTTP."""
        result = []
        items = sorted(self.items())
        for key, value in items:
            result.append(value.output(attrs))
        return sep.join(result)

    __str__ = output


class Cookie(_BaseCookie):
    """
    http.cookies.SimpleCookie
    ----------------------------------------------------------------
    SimpleCookie supports strings as cookie values.  When setting
    the value using the dictionary assignment notation, SimpleCookie
    calls the builtin str() to convert the value to a string.  Values
    received from HTTP are kept as strings.
    ----------------------------------------------------------------

    这个类本质上是对http.cookies.SimpleCookie的强化
    value_decode(self, val)和value_encode(self, val)都是直接用的SimpleCookie
    重写了构造函数
    """

    def value_decode(self, val):
        return cookies._unquote(val), val

    def value_encode(self, val):
        strval = str(val)
        return strval, cookies._quote(strval)

    def __init__(self, data=None):
        super(Cookie, self).__init__(data)
        self.__id = None
        if "cookie.id" not in self:
            # 使用uuid.uuid4()用随机数生成uuid
            self.__id = ''.join(str(uuid.uuid4()).split("-"))
            self["cookie.id"] = self.__id
        else:
            self.__id = self["cookie.id"].value

    def output(self, attrs=None, header="", sep=";"):
        return super(Cookie, self).output()

    __str__ = output

    @property
    def id(self):
        return self.__id

    def get_attribute(self, key, default=None):
        if key in self:
            return self[key].value
        else:
            return default

    def to_wsgi_header(self, attrs=None, header="Set-Cookie"):
        result = []
        items = sorted(self.items())
        for key, value in items:
            result.append((header, value.output(attrs)))
        return result


class Cache:
    def __init__(self, interval: int = 1):
        self.interval = interval
        self.lock = threading.RLock()

    def start(self):
        threading.Thread(target=self.loop_monitor).start()

    def task(self):
        pass

    def loop_monitor(self):
        scheduler = sched.scheduler(time.time, time.sleep)  # 生成调度器
        while True:
            scheduler.enter(self.interval, 1, self.task, ())
            scheduler.run()


class Session:
    expires = 30
    value = Cookie()

    def __init__(self, value=None, expires=30):
        self.expires = expires
        self.value = value

    def __str__(self):
        return "expires=%d,value=%s" % (self.expires, self.value)


class Sessions(Cache, dict):

    def task(self):
        self.lock.acquire()
        try:
            self.listener()
        finally:
            self.lock.release()

    def listener(self):
        del_item = []

        for key in self:
            value = self[key]
            value.expires -= 1
            if value.expires == 0:
                del_item.append(key)
            elif value.expires < 0:
                value.expires = -1

        for item in del_item:
            print(item)
            del self[item]

        del del_item

    def __setitem__(self, key, value):
        if isinstance(value, Session):
            dict.__setitem__(self, key, value)
        else:
            session = Session()
            session.value = value
            self[key] = value

    def add(self, key, value):
        self[key] = value
