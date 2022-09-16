from .container import Container
from .container import Log
from .container import Setting

from wsgiref.simple_server import make_server


class Fast:
    def __init__(self, setting_path: str = None, setting_data: dict = None):
        self.setting = Setting(setting_path, setting_data)
        self._container = Container()
        self._server = None
        self._log = Log()

    def set_setting(self, setting_path: str = None, setting_data: dict = None):
        self.setting.init(setting_path, setting_data)

    def start(self):
        self.__init()

        self._server.serve_forever()

    def __init(self):
        # 初始化容器
        self._container.init(self.setting)
        # print(self._container.mapping)
        # print(self._container.filter)
        # print(self._container.reject)
        # 初始化服务器
        self._server = make_server(self.setting.server_host, self.setting.server_post, self)
        print('serve on %s:%d' % (self.setting.server_host, self.setting.server_post))

    def wsgi_app(self, environ, start_response):
        response = self._container.dispatch(environ)
        start_response(response.status, response.response_headers())
        return response.response_data()

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)
