from fast_server import controller, router, MediaFile
from fast_server import GET, POST
from fast_server import HttpRequest
from time import sleep
import datetime


@controller(value="/user")
class Test3(object):
    @router(value="/login")
    def test(self, name, pwd, request: HttpRequest):
        data = {
            'name': name,
            'pwd': pwd,
            'method': request.method
        }
        for i in data:
            request.cookie[i] = data[i]
        return data

    @router(value="/info")
    def test2(self, request: HttpRequest):
        print(request.cookie.id)
        for key, value in request.cookie.items():
            print(key, value)
        return request.cookie.get_attribute("name")

    @router("/img")
    def get_img(self, request: HttpRequest):
        return request.redirect("/img1.jpg")



