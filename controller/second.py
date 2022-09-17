from fast_server import controller
from fast_server import router
from fast_server import post_router
from fast_server import GET, POST


@controller(value="/second")
class Test(object):
    @router(value="/hello6", method=GET)
    def test(self):
        print("hello world")
        return "this is test"

    def test2(self):
        print("test2")

    def test3(self):
        print("test3")

    def test4(self):
        print("test4")

    def test5(self):
        print("test5")


@controller()
class Test2:
    @post_router("/hello7")
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
