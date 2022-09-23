import traceback

from .container import Container
from .container import Log
from .container import Setting
from .application.tools import pprint

# from wsgiref.simple_server import make_server
from .application.wsgi_app import make_server, make_multi_server


class Fast:
    def __init__(self, setting_path: str = None, setting_data: dict = None, server: tuple = None):
        """
        初始化，
        当setting_path和setting_data都不为None时，他会先加载setting_path，然后加载setting_data

        ------------------------------------------------
        0.2.3 添加server参数 (server_host, server_post)
            self.server_host = "0.0.0.0"
            self.server_post = 8089
            当setting_data和server都不为None时，server将失效
        ------------------------------------------------
        :param setting_path:
        :param setting_data:
        :param server
        """
        if server is not None and setting_data is None:
            setting_data = {"server_host": server[0], "server_port": server[1]}

        self.setting = Setting(setting_path, setting_data)
        self._container = Container()
        self._server = None
        self._log = Log()
        self._init_list = []

    def set_setting(self, setting_path: str = None, setting_data: dict = None):
        """
        设置初始参数，
        :param setting_path: 配置文件路径
        :param setting_data: 配置参数
        :return: None
        """
        self.setting.init(setting_path, setting_data)

    def add_router(self, fn, path, method='all'):
        """
        0.2.3 新增，支持增加controller
        :param fn: 类方法
        :param path: 路径
        :param method: 请求方式
        :return: None
        """
        if self._init_list is None:
            self._container.mapping.add(path, fn, method)
        else:
            self._init_list.append(("self._container.mapping.add", (path, fn, method)))

    def add_routers(self, router_list: list):
        """
        0.2.3 新增
        传入一个列表，调用add_router
        :param router_list:
        :return:
        """
        for item in router_list:
            self.add_router(*item)

    def add_filter(self, clazz, path, priority, method='all'):
        """
        0.2.3 新增，支持增加controller
        :param clazz: filter类
        :param path: 目标路径
        :param priority: 优先级
        :param method: 请求方式
        :return: None
        """
        if self._init_list is None:
            self._container.filter.add(path, method, clazz, priority)
        else:
            self._init_list.append(("self._container.filter.add", (path, method, clazz, priority)))

    def add_filters(self, filter_list: list):
        """
        0.2.3 增加
        传入一个列表，调用add_filter
        :param filter_list:
        :return:
        """
        for item in filter_list:
            self.add_filter(*item)

    def start(self, constructor=None):
        """
        0.2.2 添加constructor参数，支持启动时设置make_server
        :param constructor:
        :return:
        """
        # 初始化容器
        self.__init_container()
        # 初始化服务器
        self.__init_server(constructor)

        self._server.serve_forever()

    def __init_container(self):
        """
        0.4.0
        由原先的__init()函数拆分
        """
        # 初始化容器
        self._container.init_mapping(self.setting)
        # 容器初始化后开始处理init_list中的数据
        for item in self._init_list:
            if item[0] == 'self._container.mapping.add':
                fn = eval(item[0])
                args = item[1]
                fn(*args)
        self._container.init_filter(self.setting)
        for item in self._init_list:
            if item[0] == 'self._container.filter.add':
                fn = eval(item[0])
                args = item[1]
                fn(*args)
        # 初始化完后将_init_list置为None
        self._init_list = None

    def __init_server(self, constructor):
        """
        0.4.0
        由原先的__init()函数拆分
        """
        # 初始化服务器
        if constructor is None:
            if self.setting.server_workers > 1:
                print("Enter a multithreaded environment")
                self._server = make_multi_server(
                    self.setting.server_host, self.setting.server_port, self,
                    self.setting.server_workers, self.setting.server_waiters,
                    self.setting.server_process
                )
            else:
                self._server = make_server(self.setting.server_host, self.setting.server_port, self)
        else:
            try:
                self._server = constructor(self.setting.server_host, self.setting.server_port, self)
            except TypeError:
                traceback.print_exc()
                pprint("An exception occurred while your constructor was executing", color='red')
                pprint("Now we will use the default constructor to ensure that the program continues to execute", 'red')
                self._server = make_server(self.setting.server_host, self.setting.server_port, self)
        pprint('server start on %s:%d' % (self.setting.server_host, self.setting.server_port), color='blue')

    def wsgi_app(self, environ, start_response):
        response = self._container.dispatch(environ)
        start_response(response.status, response.response_headers())
        return response.response_data()

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)


def new_path(fn, path, method='all'):
    return fn, path, method


def new_filter(clazz, path, priority, method='all'):
    return clazz, path, priority, method
