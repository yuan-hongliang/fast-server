
color_list = {
    'red': '31',
    'green': '32',
    'yellow': '33',
    'blue': '34',
    'default': '38'
}


def pprint(value: str, color='default', end='\n'):
    print("\033[{}m".format(color_list.get(color, '38')) + value + "\033[0m", end=end)
