[toc]

<p style="font-size: 45px;color: orange">fast-server</p>

## 1.安装

`pip install fast-server`

---

## 2.使用框架启动服务器

1、新建一个py文件，输入以下代码：

```python
from fast_server import Fast

def hello():
    return"<h1>HelloWorld</h1>"

if __name__ == '__main__':
    fast = Fast(server=("0.0.0.0", 8084))
    fast.add_router(hello,'/hello')
    fast.start()
```

2、启动这个代码，待控制台提示：
```
The module 'controller' has been identified
controller loading completed
------------------------------
reject_list loading completed
------------------------------
'resource' folder scanning completed
resource loading completed
------------------------------
The module 'filter' has been identified
filter loading completed
------------------------------
serve on 0.0.0.0:8084
```
服务器启动成功，端口启动在`8089`

3、在浏览器输入`http://localhost:8089/hello`
 可以看到结果
 

---

## 3.工程结构

如下是一个项目的初始结构，如下所示：

```
project
│   main.py
│   setting.json    
│
└───controller
│   │   __init__.py
|   |   ...
|
└───filter
│   │   __init__.py
|   |   ...
|
└───resource
│   │   index.html
|   |   ...
│   

```

1.	Controller包中是所有的router
2.	Filter包中是所有的过滤器
3.	Main.py为fast.start()所在主函数位置
4.	Setting.json配置文件
5.	Controller，Filter，Setting.py 这三个文件应该和main.py同级


### 3.1.setting.json

```json
{
  "container": {
    "controller": [
      "controller"
    ],
    "filter": [
      "filter"
    ],
    "resources": ["resource"],
    "reject": []
  },
  "server": {
    "host": "0.0.0.0",
    "port": "8086",
    "workers": "1",
    "waiters": "0",
    "process": "False"
  },
  "log": {
    "path": "log.txt",
    "max": "1000"
  }
}
```
将上面的数据保存为文件`setting.json`后你可以使用
```python
from fast_server import Fast
fast = Fast(setting_path="setting.json")
```
来加载配置文件

> 1. 上面的值有几个暂时用不上
> 2. 上面的值都是可选值，可以不指定
> 3. 若不指定。上面给出的也是系统的默认值

或者，你不想另外创建一个文件，你可以使用字典：
```python
setting_data = {
  "container": {
    "controller": ["controller"],
    "filter": ["filter"],
    "resources": ["resource"],
    "reject": []},
  "server": {
    "host": "0.0.0.0",
    "port": "8086",
    "workers": "1",
    "waiters": "0",
    "process": "False"
  },
  "log": {
    "path": "log.txt",
    "max": "1000"
  }
}
from fast_server import Fast
fast = Fast(setting_data=setting_data)
```

> * 这些命名可以使用`_`合并：
> * 比如说：
> * `"server": {"host": "0.0.0.0"}`
> * 可以写成：`"server_host":"0.0.0.0"`
> * 或者你还可以使用`fast.setting.server_host="0.0.0.0"`

### 3.2.controller

#### 3.2.1 @controller() @router()

1.	你需要使用`@controller`来注解类，
2.  `from fast_server import controller`
3.  这个注解也只能用在类上。这个注解有一个可选参数value，可以设置router的父路径。
4.	在类中的方法要使用`@router`来注解。
5.  `from fast_server import router`
6.  这个注解有一个参数value，用来设置router的子路径。他有一个可选参数method，可以设定请求方式。
7.	Controller类中的方法可以有参数，这些参数的参数名需要和请求表单中的参数名一样
8.	这些参数可以给定参数类型或者默认值。服务器的派发器在启动对应的业务方法时会按照一定规则，设定传入的实参可以有一个名叫request的参数，这个参数包含了当前请求的所有数据

如下是一个controller的使用演示
```python
from fast_server import controller, router, HttpRequest
@controller(value="/user")
class Test3(object):
    @router(value="/login")
    def test(self, name, pwd, request: HttpRequest):
        data = {
            'name': name,
            'pwd': pwd,
            'method': request.method
        }
        return data
```

> * 你可以在参数中添加request来获取一个HttpRequest对象
> * 这个对象包含了该次请求所需要的所有数据
> * 包括请求头，请求体，parameter，form，cookie等

> - 你的controller包下应该有一个`__init__.py`的文件
> - 比如你的包下面有一个`test.py`的模块中有controller方法
> - `__init__.py`中需要添加`from .test import *`


### 3.3.filter

1.	你需要使用`@web_filter`来注解过滤器类
2.  `from fast_server import web_filter`
3.	他的参数value为路径，priority为优先级， method为针对的请求方式
4.	priority越小，这个filter执行的优先级越高，这个值理论上可以无限小也可以无限大
5.	优先级相同的filter执行顺序是随机的
6.	所有过滤器类都需要继承一个为Filter的抽象类
7.  `from fast_server import Filter`
8.	他有两个方法需要实现，分别是before和after
9.	before方法有一个request的参数，这个函数需要返回request
10.	after方法有一个request对象和一个response对象，他需要将这两个参数都返回

如图下是一个完整的过滤器
```python
from fast_server import web_filter, Filter, POST
@web_filter(value=["/"], priority=0, method=POST)
class filterTest(Filter):
    def before(self, request):
        print("执行了filter before post")
        return request

    def after(self, request, response):
        print("执行了filter after post")
        return request, response
```

> - 你的filter包下应该有一个`__init__.py`的文件
> - 比如你的包下面有一个`test.py`的模块中有filter方法
> - `__init__.py`中需要添加`from .test import *`

### 3.4.resource

1.	你可以创建一个名为resource的文件夹，这个文件夹需要和main.py同级
2.	资源文件夹可以有多个，你需要在配置文件的`container_resources`中配置这些资源文件夹的名字
3.	在资源文件夹下的所有资源都会被加载到服务器的router中，你可以按照名字来访问这些资源文件
4.	访问时服务器将文件的格式对应的设置content-type
5.	资源文件加载时不会检查重复资源，前面加载的资源将会被后面同名的资源覆盖
6.	特别的，类似index.html文件可以使用 `/index.html` 或者 `/` 来访问

---


## 4 一些函数和类

### 4.1.request重定向

你可以通过`request.redirect(path)`，这个函数可以实现页面的重定向
他有一个参数path就是重定向页面的名字

如下是重定向使用的演示
```python
from fast_server import controller, router, HttpRequest
@controller()
class Test3(object):
    @router("/img")
    def get_img(self, request: HttpRequest):
        return request.redirect("/img1.jpg")
```

### 4.2.cookie
#### 4.2.1 Cookie
```python
from fast_server import controller, router, HttpRequest
@controller(value="/user")
class Test3(object):
    @router(value="/login")
    def test(self, name, pwd, request: HttpRequest):
        data = {
            'name': name,
            'pwd': pwd,
            'method': request.method
        }
        for i in data:
            request.cookie[i] = data[i]
        return data
```
> 1. cookie本质上是一个字典，你可以使用字典的方式获取值
> 2. 以及设置对应cookie的信息
> 3. `request.cookie.id`可以获取cookie的id

#### 4.2.2 Session

1. 使用request.session获取session
2. session的用法和cookie的用法一样
3. 他其实是封装了Cookie
4. 你可以设置Session的生命期，它默认会在服务器保存30分钟

### 4.3 替换内置的wsgi应用

#### 4.3.1.make_server
`fast.start()`的完整定义是：
`fast.start(constructor=make_server)`

在使用这个函数启动服务器时，你可以使用遵循wsgi协议的make_server作为
参数传递给他，让服务器使用自定义的wsgi应用

#### 4.3.2 call方法

`Fast`类实现了`__call__`方法

以官方的wsgi应用为例，make_server有一个参数app，
你可以将`fast`对象直接作为参数传递给这个app，
也可以实现替换服务器内置的wsgi应用。

```python
from wsgiref.simple_server import make_server
from fast_server import Fast

fast = Fast()
server = make_server("0.0.0.0", 8080, fast)
server.serve_forever()

```

### 4.4 reject_list

这是一个拦截队列，在配置文件中的"`container_reject`"中定义，
当服务器遇到拦截队列中的IP地址时，会直接阻止这个请求，并返回一个`403`

### 4.5 @post_router, @get_router
这两个注解本质上都是@router

`@post_router(value)` ==> `@outer(value, fast_server.POST)`

`@get_router(value)` ==> `@outer(value, fast_server.GET)`


### 4.6 HttpRequest, HttpResponse

request对象中封装了本次请求的所有数据，
你可以在方法的参数中添加request，然后就可以在方法中使用这个对象
```python
from fast_server import HttpRequest
def test(name, pwd, request: HttpRequest):
    pass
```
response对象会有服务器创建，在函数中使用return返回的数据都会被服务器解析后，
打包为response对象。

你可以在方法中自己创建一个response对象，然后设置好响应题的数据，
相应类型等，将response对象最为参数直接返回，服务器会直接使用这个response对象，
而不会自己在打包一个新的。
```python
from fast_server import HttpResponse
def test():
    data = "hello world"
    response = HttpResponse(data=data, charset='utf-8', status=200)
    return response
```

---


## 5. 单线程模式，多线程模式，多进程模式
### 5.1.单线程模式

设置配置数据中的`server_workers==1`时，服务器启动在单线程模式下。

### 5.2 多线程模式和多进程模式

1. `server_workers`是指工作线程的最大数，当设置这个数大于1时，
服务器就会启动在多线程模式下。
2. 设置`server_process==True`可以让服务器进入多进程模式。
3. `server_waiters`是进程中等待队列的大小，当他为`0`时，
    等待队列理论上无限大。当队列塞满之后，新的请求将会被阻塞。

> windows下暂不支持使用多进程模式，该模式目前只能运行在linux环境下。
> 当在windows下尝试进入多进程模式时，服务器会提示异常
> 然后切换为多线程模式

---


## 6.可视化界面
（该功能还在测试）

目前在我们的设计中，我们有三种方式的可视化平台，分别是：
1. 控制台格式化显示；
2. python标准ui库tkinter实现的桌面应用；
3. 通过浏览器访问的web界面。

这三种平台的使用应该有开发者来决定，选择其中的一种或几种，或者关闭不适用，亦或者使用我们定义的接口，由开发人员自己实现一个个性化的监控平台。
这个可视化界面将是我们这个框架的最重要功能之一，我们需要花费一定时间来进行优化升级。
