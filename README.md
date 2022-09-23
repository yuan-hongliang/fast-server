[toc]

# fast-server

## 1.安装

`pip install fast-server`


## 2.使用框架启动服务器

1、新建一个py文件，输入以下代码：

```python
from fast_server import Fast

def hello():
    return"<h1>HelloWorld</h1>"

if __name__ == '__main__':
    fast = Fast()
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


## 4.setting.json

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
    "workers": "1000",
    "waiters": "0",
    "process": "True"
  },
  "log": {
    "path": "log.txt",
    "max": "1000"
  }
}
```
> 上面的值有几个暂时用不上

## 5.controller

### 5.1controller注解和router注解

1.	你需要使用@controller来注解类，这个注解也只能用在类上。这个注解有一个可选参数value，可以设置router的父路径。
2.	在类中的方法要使用@router来注解。这个注解有一个参数value，用来设置router的子路径。他有一个可选参数method，可以设定请求方式。
3.	Controller类中的方法可以有参数，这些参数的参数名需要和请求表单中的参数名一样
4.	这些参数可以给定参数类型或者默认值。服务器的派发器在启动对应的业务方法时会按照一定规则，设定传入的实参可以有一个名叫request的参数，这个参数包含了当前请求的所有数据

如下是一个controller的使用演示
```python
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


### 5.2request重定向

你可以通过request.redirect(path)，这个函数可以实现页面的重定向
他有一个参数path就是重定向页面的名字

如下是重定向使用的演示
```python
@controller()
class Test3(object):

    @router("/img")
    def get_img(self, request: HttpRequest):
        return request.redirect("/img1.jpg")
```
 



## 6.filter

1.	你需要使用@web_filter来注解过滤器类
2.	他的参数value为路径，priority为优先级， method为针对的请求方式
3.	priority越小，这个filter执行的优先级越高，这个值理论上可以无限小也可以无限大
4.	优先级相同的filter执行顺序是随机的
5.	所有过滤器类都需要继承一个为Filter的抽象类
6.	他有两个方法需要实现，分别是before和after
7.	Before方法有一个request的参数，这个函数需要返回request
8.	After方法有一个request对象和一个response对象，他需要将这两个参数都返回

如图下是一个完整的过滤器
```python
@web_filter(value=["/"], priority=0, method=POST)
class filterTest(Filter):
    def before(self, request):
        print("执行了filter before post")
        return request

    def after(self, request, response):
        print("执行了filter after post")
        return request, response
```


## 7.resource

1.	你可以创建一个名为resource的文件夹，这个文件夹需要和main.py同级
2.	资源文件夹可以有多个，你需要在配置文件的container_resources中配置这些资源文件夹的名字
3.	在资源文件夹下的所有资源都会被加载到服务器的router中，你可以按照名字来访问这些资源文件
4.	访问时服务器将文件的格式对应的设置content-type
5.	资源文件加载时不会检查重复资源，前面加载的资源将会被后面同名的资源覆盖
6.	特别的，类似index.html文件可以使用 `/index.html` 或者 `/` 来访问



## 8.可视化界面
（该功能还在测试）

目前在我们的设计中，我们有三种方式的可视化平台，分别是：
1. 控制台格式化显示；
2. python标准ui库tkinter实现的桌面应用；
3. 通过浏览器访问的web界面。

这三种平台的使用应该有开发者来决定，选择其中的一种或几种，或者关闭不适用，亦或者使用我们定义的接口，由开发人员自己实现一个个性化的监控平台。
这个可视化界面将是我们这个框架的最重要功能之一，我们需要花费一定时间来进行优化升级。
