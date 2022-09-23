
# {
#   "container": {
#     "controller": [
#       "controller"
#     ],
#     "filter": [
#       "filter"
#     ],
#     "reject": []
#   },
#   "server": {
#     "host": "0.0.0.0",
#     "port": "8089",
#     "monitor": "1000",
#     "requesters": "1000",
#     "workers": "1000",
#     "waiters": "1000"
#   },
#   "log": {
#     "path": "log.txt",
#     "max": "1000"
#   }
# }

import json

ver = {"container_controller": "list",
       "container_filter": "list",
       "container_reject": "list",
       "server_host": "str",
       "server_port": "int",
       "server_workers": "int",
       "server_waiters": "int",
       "server_process": "bool",
       "log_path": "str",
       "log_max": "int"}

ver_int = {"server_port",
           "server_workers",
           "server_waiters",
           "log_max"}

ver_list = {"container_controller",
            "container_filter",
            "container_reject",
            "container_resources"}

ver_bool = {"server_process"}


class Setting:
    """
    Setting 类用来保存所有配置数据
    ---------------------------------
    0.2.4
    端口号拼错了改一下
    之前是post，现改为port
    ---------------------------------

    Attributes:
        container_controller(list): controller包名
        container_filter(list): 过滤器包名
        container_reject(list): 拦截队列
        server_host(str): 主机号
        server_port(int): 端口号
        server_workers(int): 工作内核数量
        server_waiters(int): 等待队列长度
        server_process(bool): 是否开启多进程
        log_path(str): 日志保存地址
        log_max(int): 日志最大长度
    """

    container_controller = ["controller"]
    container_filter = ["filter"]
    container_reject = []
    container_resources = ['resource']
    server_host = "0.0.0.0"
    server_port = 8089
    server_workers = 1
    server_waiters = 0
    server_process = False
    log_path = "log.txt"
    log_max = 1000

    def __init__(self, setting_path: str, setting_data: dict):
        """
        初始化Setting类

        :parameter setting_path: 配置文件的地址
        :type setting_path: str
        :parameter setting_data: 配置数据，它必须是一个字符串
        :type setting_data(dict): dict

        """

        self.container_controller = ["controller"]
        self.container_filter = ["filter"]
        self.container_reject = []
        self.container_resources = ['resource']

        self.server_host = "0.0.0.0"
        self.server_port = 8089
        self.server_workers = 1
        self.server_waiters = 0
        self.server_process = False

        self.log_path = "log.txt"
        self.log_max = 1000

        self.init(setting_path, setting_data)

    def init(self, setting_path: str = None, setting_data: dict = None):
        """
        初始化配置数据，
        当两个值都不唯None时，他会先加载setting_path，然后加载setting_data
        :param setting_path: 配置文件路径
        :param setting_data: 配置文件数据，他是一个字典
        :return: None
        """
        if setting_path is not None:
            with open(setting_path, 'r', encoding='UTF-8') as f:
                setting = json.load(f)
            self.set_by_data(setting)

        if setting_data is not None:
            self.set_by_data(setting_data)

    def set_by_data(self, setting_data: dict):

        if not isinstance(setting_data, dict):
            raise TypeError("setting_data must be dict")

        for i in setting_data:
            if isinstance(setting_data[i], dict):
                for j in setting_data[i]:
                    self.__set_data(i + "_" + j, setting_data[i][j])
            else:
                self.__set_data(i, setting_data[i])

        self._verification()

    def __set_data(self, val, data):
        if val in ver_int:
            data = int(data)
        if val in ver_bool:
            data = eval(data)
        setattr(self, val, data)

    def _verification(self):
        """
        他会验证setting中的所有属性是否符合预期的类型

        :return: None
        """
        for item in ver:
            # print(item, getattr(self, item))

            if not isinstance(getattr(self, item), eval(ver[item])):
                raise Exception(item+" must be "+ver[item])

            if item in ver_list:
                for i in getattr(self, item):
                    if not isinstance(i, str):
                        raise Exception(item+"'s member must be str,but "+str(i)+" is not")
