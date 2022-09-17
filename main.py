from fast_server import Fast, new_path


def yuan():
    return "<h1>Hello Yuan！！！</h1>"


def liang(name, pwd: int = 123):
    print(pwd)
    print(type(pwd))
    data = name
    return "hello {}".format(data)


route = [
    (yuan, "/yuan"),
    (liang, "liang")
]


if __name__ == '__main__':
    fast = Fast("application.json")
    fast.add_routers(route)
    fast.start()
