# ProxyPool
 IP代理池 + API服务提供，可以自己插入采集器进行代理IP的爬取，支持 MongoDB 4.0 使用 Python3.7 

#### 环境  
* pymongo
* flask
* aiohttp
* requests
* bs4
* lxml

**API调用(APIserver)**
```python
root = 'http://localhost:5000'
# 请求代理 kind为代理种类，anony为高匿，normal为透明
root+'/proxy/<string:kind>'
# 请求代理 直接返回一个高匿代理
root+'/proxy'
# 请求代理 返回所有满足条件的目标库IP代理数据 条件可自己在APIserver的路由函数中编辑
root+'/proxy/target/<string:domain>/<string:suffix>'
```
可以在apiserver.py中自己实现路由。

#### 使用
* 确保本机安装MongoDB，并且下载好所有需要安装库,python3.7
* 可以先进行自定义的模式，在config中进行配置,可以运行单独的模块进行测试，如：
```python
 #运行模式,置 1 表示运行，置 0 表示 不运行,全置 0 表示只运行 API server
MODE = {
    'Collector' : 1,    #代理采集
    'Validator' : 1,    #验证存储
    'Scanner'   : 1,    #扫描本地库
    'Detector'  : 1,    #高分检测
    'Tentacle'  : 1,    #目标库验证扫描
}
 ```
 * 按照自己需求更改评分量（const.setting中,默认不用更改）
 * 可以在config中配置好数据库设置
 * 配置后可以直接在DOS或Pycharm等有标准stdout的环境下运行`python main.py`
 * 运行一段时间就可以看到稳定的效果
 
 #### 示例 
 * 对config中的targets进行设置，把自己要爬取的目标网站列进去:
 ```python
targets = [
    'https://www.bilibili.com/',
    'https://www.csdn.net/',
]
```

* 在本机运行FooProxy，过了5分钟后，MongoDB数据库中出现了两个collection: bilibili_com,csdn_net
* 自己的爬虫中使用API: ‘http://127.0.0.1:5000/proxy/target/bilibili/com’，
获取到了所有满足条件的代理IP,格式如下:
```json
[
    {
        "ip":"180.183.135.46",
        "port":"8080",
        "anony_type":"透明",
        "address":"英国 ",
        "createdTime":"2018-11-07 18:30:22",
        "score":75.27,
        "test_count":10,
        "url":"https://www.csdn.net/",
        "total":752.7,
        "resp_time":"1.829105s",
        "valid_time":"2018-11-07 19:52:29"
    },
    {
        "ip":"46.21.74.130",
        "port":"8080",
        "anony_type":"高匿",
        "address":"俄罗斯 ",
        "createdTime":"2018-11-07 18:25:36",
        "score":75.05,
        "test_count":11,
        "url":"https://www.csdn.net/",
        "total":825.55,
        "resp_time":"7.812447s",
        "valid_time":"2018-11-07 19:52:35"
    }
]
```
* 在爬虫中根据自己需求选择了代理IP数据进行后续爬取
 
