from fast_server import controller, mapping, MediaFile
from fast_server import GET, POST
from fast_server import HttpRequest
from time import sleep
import datetime


@controller(value="/test")
class Test3(object):
    @mapping(value="/hello")
    def test(self, name, pwd, request: HttpRequest):
        data = {
            'name': name,
            'pwd': pwd,
            3: 3,
            'method': request.method
        }
        return data

    @mapping(value="/helloll")
    def test2(self):
        with open("C:/Users/86132/Desktop/资源/图片资源/background/一/1589473051347.png", "rb") as f:
            bytes_ = f.read()
        media_file = MediaFile(bytes_)
        return media_file

    def test3(self):
        print("test3")

    def test4(self):
        print("test4")

    def test5(self):
        print("test5")


@controller()
class Test4:
    def __init__(self):
        self.aaaaa = "a"

    @mapping(value="/hello2", method=POST)
    def test(self, name, pwd):
        # data={"name":name,"pwd":pwd,1:1}
        # print(data)
        data = {
            'name': name,
            'pwd': pwd,
            3: 3,
            "aaaa": self.aaaaa,
            'method': 'post'
        }
        return data
        # return name+pwd

    def test2(self):
        print("test2")

    def test3(self):
        print("test3")

    def test4(self):
        print("test4")

    def test5(self):
        print("test5")


class Test5:
    @mapping(value="/hello3")
    def test(self):
        print("test")

    def test2(self):
        print("test2")

    def test3(self):
        print("test3")

    def test4(self):
        print("test4")

    def test5(self):
        print("test5")


class Test6:
    @mapping(value="/hello4")
    def test(self):
        print("test")

    def test2(self):
        print("test2")

    def test3(self):
        print("test3")

    def test4(self):
        print("test4")

    def test5(self):
        print("test5")


@controller()
class Test25:
    @mapping(value="/hello5", method=POST)
    def test(self):
        print("test")

    def test2(self):
        print("test2")

    def test3(self):
        print("test3")

    def test4(self):
        print("test4")

    def test5(self):
        print("test5")
