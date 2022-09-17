from fast_server import controller, router


@controller(value='/firstserver')
class FirstServer(object):
    @router(value='hello')
    def hello(self, name):
        data = "hello "+name
        return data


