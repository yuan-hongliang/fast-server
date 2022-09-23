
color_list = {
    'red': '31',
    'green': '32',
    'yellow': '33',
    'blue': '34',
    'default': '38'
}


def pprint(value: str, color='default', end='\n'):
    """
    -----------------------
    0.2.3 新增
    格式化输出数据
    -----------------------
    :param value:
    :param color:
    :param end:
    :return:
    """
    print("\033[{}m".format(color_list.get(color, '38')) + value + "\033[0m", end=end)
