from fast_server import Filter
from fast_server import web_filter
from fast_server import POST, GET


@web_filter(value=["/test"], priority=0, method=POST)
class filterTest(Filter):
    def before(self, request):
        print("执行了filter before post")
        return request

    def after(self, request, response):
        print("执行了filter after post")
        return request, response


@web_filter(value=["/test"], priority=0, method=GET)
class filterTest22(Filter):
    def before(self, request):
        # print(request.get_url(),request.get_address())
        # p=request.get_parameter()
        # # print(p['name'])
        # p['name']='袁洪'
        # request.set_parameter(p)
        print("执行了filter before get")
        return request

    def after(self, request, response):
        print("执行了filter after get")
        return request, response


@web_filter(value=["/test"], priority=1)
class filterTest_s(Filter):
    def before(self, request):
        print("执行了filter before all")
        return request

    def after(self,  request, result):
        print("执行了filter after all")
        return request, result


@web_filter(value="/", priority=2)
class filterTest2(Filter):
    def before(self, request):
        print("执行了filter b‘/’1")
        return request

    def after(self, request, result):
        print("执行了filter a‘/’1")
        return request, result


@web_filter(value="/", priority=2)
class filterTest44(Filter):
    def before(self, request):
        print("执行了filter b‘/’2")
        return request

    def after(self, request, result):
        print("执行了filter a‘/’2")
        return request, result


@web_filter(value=["/hello7"])
class filterTest3(Filter):
    def before(self, request):
        return request

    def after(self, request, result):
        return request, result
