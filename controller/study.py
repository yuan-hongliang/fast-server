from fast_server import controller, mapping


@controller(value='/firstserver')
class FirstServer(object):
    @mapping(value='hello')
    def hello(self, name):
        data = "hello "+name
        return data


