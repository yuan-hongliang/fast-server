import os

from .setting import Setting
from ..application.fast_http import HttpRequest, HttpResponse
from ..application.tools import pprint
from ..application.cookies import Sessions
from .fast_ip import IPList, IP
from .log import Log

import traceback
import inspect
import sys

ip0 = IP("0.0.0.0")


class Base:
    """
    一个基类，没啥大用
    """

    # 目前服务器支持的方法，之后直接在这里填充
    methods = ['post', 'get']

    def init(self, **kwargs):
        """
        所有继承自这个基类的子类，需要调用这个类来完成容器对象的初始化
        __init__(self) 仅实现对象的构建，而属性的初始化需要调用这个函数实现
        :param kwargs: 参数列表
        :return: None
        """
        pass


class Container(Base):
    """
    继承自Base的容器类，保存了服务器运行所需要的全部controller和filter
    mapping: 保存所有controller
    filter: 保存所有filter
    reject: 是一个列表，ip地址拦截队列
    -----------------------------------------------------------------
    0.3.0 修改
    添加 resource 属性
    修改了init_mapping方法
    -----------------------------------------------------------------
    """
    def __init__(self):
        self.mapping = ControllerMapping()
        self.filter = FilterChain()
        self.allow = IPList()
        self.reject = IPList()
        self.resource = Resource()
        self.session = Sessions()

    def init_mapping(self, setting: Setting):
        """
        -----------------------------------------------------------------
        0.2.3 新增
        将原来的init()函数拆分，只保留了mapping和reject的初始化
        拆分是为了能够确保add_router添加的mapping和filter在对应对象初始化后分别正确的添加
        -----------------------------------------------------------------
        0.3.0 修改
        添加对resource对象的初始化
        以及将资源文件添加进mapping中
        -----------------------------------------------------------------
        0.6.0 修改
        初始化拦截队列的功能拆出来
        -----------------------------------------------------------------
        :param setting:
        :return:
        """

        # 启动ControllerMapping()对象的初始化程序
        self.mapping.init(setting)
        pprint("controller loading completed\n" + "----------"*3)

        # 初始化资源文件
        self.resource.init(setting)
        for path in self.resource.res_path:
            self.mapping.add(path, self.resource.get_resource, 'all')
        pprint("resource loading completed\n" + "----------"*3)

    def init_filter(self, setting: Setting):
        """
        0.2.3新增
        将原来的init()函数拆分，只保留了filter的初始化
        拆分是为了能够确保add_router添加的mapping和filter在对应对象初始化后分别正确的添加
        :param setting:
        :return:
        """
        # 在完成了mapping的初始化后，获取已经保存的所有controller的path，放入一个path列表中
        path_list = []
        for method in self.mapping.controller:
            path_list += self.mapping.controller[method].keys()
        path_list = list(set(path_list))
        # 将path列表作为参数传递给FilterChain()的init函数，完成filer的初始化
        self.filter.init(setting, path_list)
        pprint("filter loading completed\n" + "----------"*3)

    def init_allow_reject(self, setting: Setting):
        # 初始化拦截队列
        self.reject.add_all(setting.container_reject)
        pprint("reject_list loading completed")

        if "0.0.0.0" in setting.container_allow:
            setting.container_allow = ["0.0.0.0"]
        self.allow.add_all(setting.container_allow)
        print(self.allow)
        pprint("allow_list loading completed")
        pprint("----------" * 3)

    def dispatch(self, environ) -> HttpResponse:
        """
        使用environ创建HttpRequest对象
        执行task方法获取HttpResponse对象
        将response对象错位参数返回
        :param environ: 请求体
        :return: response
        """
        request = HttpRequest(environ, self.session)
        response = self.task(request)
        return response

    def task(self, request: HttpRequest) -> HttpResponse:
        """
        执行request
        :param request: 打包后的请求体对象
        :return: response
        """
        # 创建一个空的response，保证task执行过程中可以保证由数据返回给客户端
        response = HttpResponse()
        try:
            '''
            拒绝该请求
            '''
            if (ip0 in self.allow or request.remote_addr in self.allow) and request.remote_addr not in self.reject:
                pass
            else:
                request.prohibit = True
                response.data = "Your are denied access to this server"
                response.set_status(403)
            '''
            处理Filter.before()
            '''
            if not request.prohibit:
                request = self.run_filter_before(request)

            if not request.prohibit:
                """
                执行对应的方法
                """
                request, response = self.run_function(request)
                if not request.prohibit:
                    """
                    执行Filter.after()
                    """
                    request, response = self.run_filter_after(request, response)
                    response.cookie = request.cookie
        except Exception as ex:
            """
            当task执行过程中出现异常时，修改空的response
            将程序执行时的错误日志返回给客户端
            """
            exc = traceback.format_exc()
            response.data = "server exception!\n"+exc
            response.set_status(500)
            print(ex)
            print(exc)
            Log().wlog(response)
        finally:
            return response

    def run_function(self, request: HttpRequest) -> tuple:
        """
        执行具体的业务函数
        ---------------------------------------------------------
        0.2.3
        修改了参数的获取逻辑，
        首先通过inspect.signature(fn).parameters.keys()获取所有非self的参数名
        然后通过inspect.getfullargspec(fn).defaults获取所有的默认参数
        再通过 inspect.getfullargspec(fn).annotations获取参数定义的数据类型
        defaults_index = len(defaults) - len(parameters)来正确的导入默认参数

            此版本前使用的参数设置方式：
            _count = count = fn.__code__.co_argcount
            for item in fn.__code__.co_varnames:
                if count != _count:
                    if item in parameter_map:
                        args += "\"" + str(parameter_map[item]) + "\","
                    elif item == "request":
                        args += "request,"
                    else:
                        args += "None,"
                count -= 1
                if count == 0:
                    break

        修改后函数支持默认参数，以及传递给定的参数类型
        ---------------------------------------------------------
        :param request: 请求体
        :return: request, response
        """
        # 首先判断服务器是否支持该请求的方式
        if request.method in Base.methods:
            # 之后判断对应的方法中是否有请求的资源
            if request.path in self.mapping.controller[request.method]:
                # 获取业务函数
                fn = self.mapping.controller[request.method][request.path]
                '''
                按照方法的参数在请求体的参数中寻找，
                若找到则按顺序添加，
                若未找到则将插入一个None值
                若方法的请求参数里有request，则将此参数传给他
                '''
                # 按照get请求和post请求的方式获取对应的请求参数
                parameter_map = request.parameter if request.method == 'get' else request.form
                args = ""

                # 获取其所有的非self方法
                # inspect.getfullargspec(fn).args也能获取所有的参数，但是他拿到的参数会包括'self'
                parameters = inspect.signature(fn).parameters.keys()

                # 获取所有的默认参数，以及给定的参数类型
                full_arg_spec = inspect.getfullargspec(fn)
                # 默认参数
                defaults = full_arg_spec.defaults
                # 给定的参数类型
                annotations = full_arg_spec.annotations

                # 确保默认参数列表
                defaults = defaults if defaults else []
                # 获取默认参数列表索引，<0时说名当前的参数没有设置默认值
                defaults_index = len(defaults) - len(parameters)
                # 遍历函数的参数列表
                for item in parameters:
                    # 如果能在请求参数中找到同名的参数，使用请求参数中的数据
                    if item in parameter_map:
                        # 如果函数给定的参数类型是str，或者没有指定特定的参数类型时，使用str
                        if annotations.get(item, type(str)) == type(str):
                            args += "\"" + str(parameter_map[item]) + "\","
                        else:
                            # 否则直接传递数据过
                            args += str(parameter_map[item]) + ","
                    # 如果item是request，将request对象传递过去
                    elif item == "request":
                        args += "request,"
                    else:
                        # 否则传递一个默认值
                        # 如果当前的参数存在默认值，则将这个默认值传递过去
                        if defaults_index >= 0:
                            # 下面的判断逻辑同上
                            type_ = annotations.get(item, type(str))
                            if type(str) == type_ and isinstance(defaults[defaults_index], str):
                                args += "\"" + str(defaults[defaults_index]) + "\","
                            else:
                                args += str(defaults[defaults_index]) + ","
                        # 否则传递一个None值
                        else:
                            args += "None,"
                    defaults_index += 1

                '''
                所有参数以字符串的形式添加到方法后，
                通过eval函数执行
                '''
                # 如果业务函数的请求参数时空的
                if args == "":
                    # 执行业务函数，并获取执行结果
                    data = fn()
                else:
                    # 通过eval获得执行参数
                    args = eval(args)
                    # 将参数传递给业务函数执行，并获取获取执行结果
                    data = fn(*args)

                """
                判断执行结果的类型，
                如果是HttpRequest对象，则处理这个对象
                如果时HttpResponse对象，则将他返回
                """
                # 如果是HttpRequest对象
                if isinstance(data, HttpRequest):
                    response = HttpResponse(data=data)
                    pass
                # 如果这个执行结果时一个HttpResponse对象，
                # 则之间将这个对象赋值给response作为返回值
                elif isinstance(data, HttpResponse):
                    response = data
                else:
                    # 否则创建一个新的response对象，
                    # 并将这个response对象返回
                    response = HttpResponse(data=data)
            else:
                # 没有找到这个path
                response = HttpResponse(data="this url is not Found!", status=404)
        else:
            # 没有找到这个method
            response = HttpResponse(data="this method is not Found!", status=404)
        # 将request和response返回
        return request, response

    def run_filter_before(self, request: HttpRequest) -> HttpRequest:
        """
        执行Filter.before()
        :param request: 打包后的请求体
        :return: request
        """
        if request.path in self.filter.filterChain:
            if request.method in self.filter.filterChain[request.path]:
                for priority in (dic := self.filter.filterChain[request.path][request.method]):
                    for clazz in dic[priority]:
                        request = clazz.before(request)
        return request

    def run_filter_after(self, request: HttpRequest, response: HttpResponse) -> tuple:
        """
        执行Filter.after()
        :param request: 请求体
        :param response: 响应体
        :return: request, response
        """
        if request.path in self.filter.filterChain:
            if request.method in self.filter.filterChain[request.path]:
                for priority in (dic := self.filter.filterChain[request.path][request.method]):
                    for clazz in dic[priority]:
                        request, response = clazz.after(request, response)
        return request, response


def get_all_class(page_list: list):
    """
    获取所有page_list中的所有类，保存在class_list中
    :param page_list: 包列表
    :type page_list: list
    :return: list 类列表
    """
    default_class = {"controller", "filter"}
    class_list = []

    # 去重
    page_list = set(page_list)

    for item in page_list:
        try:
            # 尝试导入这个包
            imp_module = __import__(item)
        except ImportError:
            if item not in default_class:
                pprint("no module name '{}'".format(item), color='red')
            # print(traceback.format_exc())
            # 导入失败则跳过
            pass
        else:
            # 导入成功后则将包块下的类加载到类列表中
            for name, _ in inspect.getmembers(sys.modules[item], inspect.isclass):
                obj = getattr(imp_module, name)
                class_list.append(obj)
            pprint("The module '{}' has been identified".format(item))
    # 返回这个列表
    return class_list


def remove_redundant_slashes(value: str):
    """
    这个方法将会将value中多余的'/'去除，
    同时如果开头缺少'/'也会添加上去，
    位的是保证path的格式一致

        item = item.replace("//", "/")
        if item[0] != '/':
            item = '/' + item
        while item[-1] == '/':
            item = item[0:-1]

    :param value: path
    :type value: str
    :return: str
    """
    if value == '/':
        return value

    # 去除多余的斜杠
    value = value.replace("//", "/")
    # 开头却上斜杠就加上
    if value[0] != '/':
        value = '/' + value
    # 去掉尾部的斜杠
    while value[-1] == '/':
        value = value[0:-1]
    # 返回去掉多余'/'后的path
    return value


class ControllerMapping(Base):
    """
    Controller类，保存所有的controller方法
    controller 保存所有的controller方法

        方法保存方式：
        {'method1':{'path1':fn1, 'path2':fn2, .....},
         'method2':{'path1':fn1, 'path2':fn2, .....}, ...}

    class_list 所有controller类
    """
    def __init__(self):
        # self.post_mapping = {}
        # self.get_mapping = {}
        self.controller = {}
        self.class_list = []

    def init(self, setting: Setting):
        """
        初始化controller
        :param setting: 系统设置
        :return: None
        """
        for method in ControllerMapping.methods:
            self.controller[method] = {}
        self.__init_mapping(setting)

    def add(self, name, fn, method):
        """
        添加一个controller

        -----------------------------
        0.2.3
        增加对method的判断，当他为all时将会吧所有的method都走一遍，
        增加对path的格式判定修改
        -----------------------------
        :param name: path
        :param fn: 请求的执行函数
        :param method: 请求方式，post,get
        :return: None
        """
        name = remove_redundant_slashes(name)
        if method == 'all':
            for m in ControllerMapping.methods:
                self.add(name, fn, m)
        else:
            self.controller[method][name] = fn
        # if method == 'post':
        #     self.post_mapping[name] = fn
        # else:
        #     self.get_mapping[name] = fn

    def __init_mapping(self, setting: Setting):
        self.class_list = get_all_class(setting.container_controller)

        for name in (post_mapping := self.__init_mapping_('post')):
            self.add(name, post_mapping[name], 'post')
        for name in (get_mapping := self.__init_mapping_('get')):
            self.add(name, get_mapping[name], 'get')

    def __init_mapping_(self, method):
        """
        这个方法将判断是否为controller类
        同时类中的方法是否有mapping注解
        按照mapping注解的value值以键值对的形式存入字典
        值便是对应的反射，
        使用时直接从对应的get或post队列中取出即用
        :param method:
        :return:
        """
        mapping_dir = {}
        for clazz in self.class_list:
            # func = clazz.fn
            if isinstance(clazz, type):
                anno = clazz.__dict__.get('__annotations__', None)
            else:
                anno = getattr(clazz, '__annotations__', None)
            if anno is None or "controller" not in anno:
                continue

            function_list = [e for e in dir(clazz) if not e.startswith('_')]

            for fn in function_list:

                func = eval("clazz()." + fn)

                func_anno = func.__annotations__

                if 'mapping_value' not in func_anno or "mapping_method" not in func_anno:
                    continue
                '''
                此处会判断该方法是否为所要求的
                '''
                if func_anno["mapping_method"] == "all" or func_anno["mapping_method"] == method:
                    value = func_anno["mapping_value"]

                    if "mapping_value" in anno:
                        value = anno["mapping_value"] + "/" + value

                    # 去除多余的斜杠
                    value = remove_redundant_slashes(value)

                    if mapping_dir.__contains__(value):
                        err = str(func.__code__) + "\n" + "=" * 10 + ">There are multiple identical 'mapping value'!"
                        raise Exception(err)

                    mapping_dir[value] = func

                    # print(value, func, "加载成功")
                    # time.sleep(0.5)
        return mapping_dir

    def __str__(self):
        s = "ControllerMapping: {"
        for method in self.controller:
            for fn in self.controller[method]:
                s += "{ "+method+" path:" + fn + ", fn:" + str(self.controller[method][fn]) + "}\n"
        # for i in self.post_mapping:
        #     s += "{ post path:"+i+", fn:"+str(self.post_mapping[i])+"}\n"
        # for i in self.get_mapping:
        #     s += "{ get path:"+i+", fn:"+str(self.get_mapping[i])+"}\n"
        return s+"}\n"


class FilterChain(Base):
    """
    filter类，用来保存所有的filter对象
    filterChain 一个filter链

        数据保存方式：
        {'path1': {'method1': OrderDic(), 'method2': OrderDic()},
         'path2': {'method1': OrderDic(), 'method2': OrderDic()}, ....}

        OrderDic():
        {'priority1': [class1, class2, ...], 'priority2': [class1, class2, ...], ...}

        注意：1.OrderDic()会按照 键 来给所有的 键值对 排序，
               这里的排序仅是按照迭代的顺序而言的，也就是使用 for in 时会按照键的 升序 或是 降序 来进行遍历，
               但是里面的 键值对 的保存方式还是按照 dict 来的，
               同时由于这个特性他的 key 一定要是同一数据类型

             2.这里的排序仅只针对优先级而言，
               也就是说，优先级确定，那这个filter的执行也是相对确定的，
               但是如果对于优先级相同的filter，他们的执行顺序将是随机的，或者说是不确定的

    class_list 保存了所有filter类的列表
    """
    def __init__(self):
        self.filterChain = {}
        self.class_list = []

    def init(self, setting: Setting, path_list: list):
        """
        初始化filter
        :param setting: 系统设置
        :param path_list: 方法列表
        :return: None
        """
        self.init_chain(path_list)
        self.class_list = get_all_class(setting.container_filter)
        for path in (filter_name_map := self.get_filter_name()):
            for item in filter_name_map[path]:
                self.add(path, item[2], item[0], item[1])

    def init_chain(self, path_list: list):
        for path in path_list:
            self.add_path(path)

    def add_path(self, path: str):
        """
        添加一个path到filterChain中
        :param path: path
        :type path: str
        :return: None
        """
        # 去除多余的'/'
        path = remove_redundant_slashes(path)
        # 添加path
        self.filterChain[path] = {}
        # 为每个method都分配一个OrderDic()
        for method in FilterChain.methods:
            self.filterChain[path][method] = OrderDic()

    def add(self, path, method, clazz, priority):
        """
        添加一个filter
        :param path: path
        :param method: 方法
        :param clazz: filter类，这个类必须继承自Filter
        :param priority: 优先级
        :return: None
        """
        if method == 'all':
            for method_ in self.methods:
                self.add(path, method_, clazz, priority)
        else:
            path = remove_redundant_slashes(path)
            for path_ in self.filterChain:
                if path == '/':
                    self.__add(path_, method, clazz, priority)
                else:
                    p1 = path.split('/')[1:]
                    p2 = path_.split('/')[1:]
                    if len(p1) <= len(p2):
                        flag = True
                        for i in range(len(p1)):
                            if p1[i] != p2[i]:
                                flag = False
                                break
                        if flag:
                            self.__add(path_, method, clazz, priority)

    def __add(self, path, method, clazz, priority):
        if priority in self.filterChain[path][method]:
            self.filterChain[path][method][priority].append(clazz)
        else:
            self.filterChain[path][method][priority] = [clazz]

    def get_filter_name(self):
        """
        获取所有filter类需要加强的请求
        :return: dict
        """
        filter_name_map = {}
        for clazz in self.class_list:
            if isinstance(clazz, type):
                ann = clazz.__dict__.get('__annotations__', None)
            else:
                ann = getattr(clazz, '__annotations__', None)
            if ann is None:
                continue
            if "filter_value" in clazz.__annotations__:
                if clazz.__annotations__["filter_value"] == "/":
                    if "/" in filter_name_map:
                        filter_name_map["/"].append(
                            [clazz(), clazz.__annotations__["filter_priority"], clazz.__annotations__["filter_method"]])
                    else:
                        filter_name_map["/"] = [
                            [clazz(), clazz.__annotations__["filter_priority"], clazz.__annotations__["filter_method"]]]
                else:
                    for item in clazz.__annotations__["filter_value"]:
                        '''
                        ‘/’出现在列表中会显得多余，
                        同时如果出现在列表中会给filter字典的创建造成一定麻烦
                        所以干脆在此处禁止列表中出现‘/’
                        要使用‘/’要单独写出
                        '''
                        if item == "/":
                            err = "If filter_value is a list,'/' cannot be in it!"
                            raise Exception(err)

                        # 去除多余的斜杠
                        item = remove_redundant_slashes(item)

                        if item in filter_name_map:
                            filter_name_map[item].append([clazz(), clazz.__annotations__["filter_priority"],
                                                          clazz.__annotations__["filter_method"]])
                        else:
                            filter_name_map[item] = [[clazz(), clazz.__annotations__["filter_priority"],
                                                      clazz.__annotations__["filter_method"]]]
        return filter_name_map

    def __str__(self):
        s = "FilterChain: {"
        for path in self.filterChain:
            s += "{ path: "+path
            for method in self.filterChain[path]:
                s += "{ method: "+method+", class: "+str(self.filterChain[path][method])+"}, "
            s += "}\n"
        return s+"}\n"


class OrderDic:

    """
    OrderDic()会按照 键 来给所有的 键值对 排序，
    这里的排序仅是按照迭代的顺序而言的，也就是使用 for in 时会按照键的从小到大或是从大到小来进行遍历，
    但是里面的 键值对 的保存方式还是按照 dict 来的，
    同时由于这个特性他的 key 一定要是同一数据类型
    """

    def __init__(self, data: dict = None, reverse=False):
        """
        初始化一个OrderDic
        :param data: 初始化数据
        :param reverse: 排序方式，False升序，True降序
        """

        if data is None:
            data = {}

        self.__orderList = []
        self.__orderDic = {}
        self.__reverse = reverse
        for key in data:
            self.add(key, data[key])

    def add(self, key, value):
        """
        添加一个值
        如果这个key已经存在，就会覆盖原来key的值，
        当添加一个新的值的时候，键会被另外保存在一个列表中，
        然后对这个列表进行排序，
        这个泪飙也是实现按照一定顺序迭代的关键
        :param key: 键
        :param value: 值
        :return: None
        """
        if key not in self.__orderDic:
            self.__orderList.append(key)
            self.__orderList.sort(reverse=self.__reverse)
        self.__orderDic[key] = value

    def remove(self, key):
        """
        删除一个键值对
        :param key: 键
        :return: None
        """
        del self.__orderDic[key]
        self.__orderList.remove(key)

    def get(self, key, default=None):
        """
        按照key获取一个值，
        如果没有找到就返回default
        :param key: 键
        :param default: 在没有找到这个键的情况下返回的值
        :return: value
        """
        if key in self.__orderDic:
            return self.__orderDic[key]
        else:
            return default

    def __iter__(self):
        """
        这里迭代时是从已经 排序好的 由键组成的列表 中顺序获取已经排好序的键
        :return: key
        """
        for i in self.__orderList:
            yield i

    def __getitem__(self, y):
        """
        这里时直接尝试从字典中获取对应的值，
        如果没有找到的话会报错
        :param y: key
        :return: value
        """
        return self.__orderDic[y]

    def __setitem__(self, key, value):
        self.add(key, value)

    def __len__(self):
        return len(self.__orderList)

    def __delitem__(self, key):
        self.remove(key)

    def __str__(self):
        st = "{"
        for i in self.__orderList:
            value = self.__orderDic[i]
            st += ("'"+i+"'" if isinstance(i, str) else str(i)) + ": " + \
                  ("'"+value+"'" if isinstance(value, str) else str(value))+","
        return st[:-1]+"} "


class Resource(Base):
    """
    0.3.0 添加
    实现对资源文件的扫描
    res_path 资源文件
        数据保存方式
        {path1: name1, path2: name2}
        说明：
            path: 加载到mapping后的名称或者叫path，例如：/index.html
            name：资源文件的名称，在计算机中的相对路径，例如：resource/index.html
    """

    def __init__(self):
        self.res_path = {}

    def init(self, setting: Setting):
        """
        扫描所有资源文件，添加进res_path
        :param setting:
        :return:
        """
        for file in Setting.container_resources:
            if os.path.isdir(file):
                pprint("'{}' folder scanning completed".format(file))
                for name in Resource.get_all_files(file):
                    path = name[name.find('/'):]
                    if path.find("/index.") >= 0:
                        self.res_path.update({'/': name})
                    self.res_path.update({path: name})
            else:
                if file != 'resource':
                    pprint("'{}' folder not found or it is not a folder".format(file), color='red')

    def get_resource(self, request: HttpRequest) -> HttpResponse:
        """
        这个函数将被作为值添加到mapping中
        资源文件被引用时，run_function函数将调用它
        获取文件访问路径并打包资源文件
        :param request:
        :return:
        """
        path = request.path
        if path in self.res_path:
            return Resource.get_resource_response(self.res_path[path])
        return HttpResponse(data="this resource is not Found!", status=404)

    @staticmethod
    def get_all_files(dir_: str) -> list:
        """
        获取文件夹下所有文件的名字
        :param dir_: 文件夹名
        :return: list
        """
        file_list = []
        files = os.listdir(dir_)
        for file in files:
            file = dir_ + "/" + file
            if os.path.isdir(file):
                file_list += Resource.get_all_files(file)
            else:
                file_list.append(file)
        return file_list

    @staticmethod
    def get_resource_response(file_path: str) -> HttpResponse:
        """
        将资源文件打包为Response对象
        -----------------------------------
        0.4.0
        现在他创建response对象时会直接将Resource.file_iterator返回的生成器做为data的参数
        -----------------------------------
        :param file_path:
        :return:
        """
        response = HttpResponse(Resource.file_iterator(file_path))

        file_paths = file_path.split('/')
        index = file_paths[-1].rfind('.')
        if index > 0:
            response.set_content_type(file_paths[-1][index+1:])
        return response

    @staticmethod
    def file_iterator(file_path, chunk_size=512):
        """
        文件读取迭代器
        :param file_path:文件路径
        :param chunk_size: 每次读取流大小
        :return: itr
        """
        with open(file_path, 'rb') as target_file:
            while True:
                chunk = target_file.read(chunk_size)
                if chunk:
                    yield chunk
                else:
                    break
