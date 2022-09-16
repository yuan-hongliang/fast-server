from .futures import Filter

GET = "get"
POST = "post"

# def controller(clazz):
#     if isinstance(clazz, type):
#         ann = clazz.__dict__.get('__annotations__', None)
#     else:
#         ann = getattr(clazz, '__annotations__', None)
#     if ann == None:
#         setattr(clazz, '__annotations__', {})
#     # setattr(clazz, '__annotations__', {"controller":"controller"})
#     clazz.__annotations__["controller"] = "controller"
#     # print(clazz,clazz.__annotations__)
#     return clazz


def controller(value='all'):
    def _controller(clazz):
        if isinstance(clazz, type):
            ann = clazz.__dict__.get('__annotations__', None)
        else:
            err = str(clazz)+"  must be class !"
            raise Exception(err)
        if ann is None:
            setattr(clazz, '__annotations__', {})
        # setattr(clazz, '__annotations__', {"controller":"controller"})
        clazz.__annotations__["controller"] = "controller"
        if value != 'all':
            clazz.__annotations__["mapping_value"] = value
        return clazz
    return _controller


def _mapping(fn, value, method):
    if isinstance(fn, type):
        ann = fn.__dict__.get('__annotations__', None)
    else:
        ann = getattr(fn, '__annotations__', None)
    if ann is None:
        setattr(fn, '__annotations__', {})
    fn.__annotations__["mapping_value"] = value
    fn.__annotations__["mapping_method"] = method
    # print(fn.__annotations__)
    # setattr(fn, '__annotations__', {"mapping_value": value,"mapping_method":method})
    return fn


def mapping(value, method="all"):
    def __mapping(fn):
        return _mapping(fn, value, method)
    return __mapping


def get_mapping(value):
    def __mapping(fn):
        return _mapping(fn, value, GET)
    return __mapping


def post_mapping(value):
    def __mapping(fn):
        return _mapping(fn, value, POST)
    return __mapping


def web_filter(value='/', priority=1, method="all"):
    def f(clazz):
        """
        判断该方法是否是Filter的子类，不是则弹出异常
        """
        if not ischildof(clazz, Filter):
            err = str(clazz)+" This class must inherit from 'application.futures.Filter' !"
            raise Exception(err)
        '''
        判断value值是否为’/‘或者列表，不是则弹出异常
        '''
        if value == '/' or isinstance(value, list):
            if isinstance(clazz, type):
                ann = clazz.__dict__.get('__annotations__', None)
            else:
                ann = getattr(clazz, '__annotations__', None)
            if ann is None:
                setattr(clazz, '__annotations__', {})
            clazz.__annotations__["filter_value"] = value
            clazz.__annotations__["filter_priority"] = priority
            clazz.__annotations__["filter_method"] = method
        else:
            err = "Filter value must be list or '/'  !"
            raise Exception(err)
        return clazz
    return f


def ischildof(obj, cls):
    """
    判断一个类是否是另一个类的子类
    :param obj: 需要判断的类
    :param cls: 目标类
    :return:
    """
    try:
        for i in obj.__bases__:
            if i is cls or isinstance(i, cls):
                return True
        for i in obj.__bases__:
            if ischildof(i, cls):
                return True
    except AttributeError:
        return ischildof(obj.__class__, cls)
    return False
