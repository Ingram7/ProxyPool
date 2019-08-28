# FooProxy
稳健高效的评分制 IP代理池 + API服务提供，可以自己插入采集器进行代理IP的爬取，支持 MongoDB 4.0 使用 Python3.7 
## 背景
 因为平时爬取某些网站数据时，经常被封IP，同时网上很多的接口又不方便，免费的也少，稳定的更少，所以自己写了一个评分制的ip代理API进行爬虫的供给
 起初对MySQL和MongoDB进行了兼容的编写，后来发现在高并发的情况下，MySQL并不能很好的读写数据，经常莫名其妙的出现死机、读写巨慢、缓执行等各种奇
 葩现象，对比MongoDB高效的数据文档读写，最终还是放弃了mysql的兼容。*(dev分支保留了对mysql的部分支持，如爬取评分)*
## 环境  
> **开发环境**
* PyCharm 2018.2.4 (Professional Edition)
* Python 3.7
* MongoDB 4.0
* Windows 7 64bits
> **需安装的库**
* pymongo
* flask
* aiohttp
* requests
* bs4
* lxml
## 项目目录
> * APIserver
>>  一个简单的代理API接口服务器，使用Flask实现，可以自己按需求写路由逻辑。这部分当然可以独立出来写，只是集成写在了项目里面。
> * components
>> 项目的主要运行部分，采集器、验证器、触手、打分检测等功能实现的模块。
> * **config**
>> 其中的DBsettings是数据库的设置，用户名密码之类的，以及存储的数据库名，还有备用有效数据库(standby)的自定义名字和高分稳定数据库(stable)的自定义名字。config文件是整个项目的主要参数配置，可以设置采集器采集间隔、验证器的抓取验证数量间隔和协程并发极值等。
> * const
>> 项目的静态配置，一般不用动的设置参数
> * **custom**
>> 自定义模块，可以编写自己要增加的爬虫采集函数到采集器中进行数据采集
> * log
>> 项目日志记录模块配置以及日志
> * tools
>> 一些工具函数
> * **main.py**
>> 项目入口文件
## 基本流程
整个项目的流程其实很简单，每一个模块只负责自己该干的活，其他的不管，这样职责分明，可以单独运行，耦合度小。
* 采集数据
* 验证数据
* 打分存储
* 循环扫描
* 择优剔劣
* API调用

 流程图：
 
![流程图](https://github.com/01ly/FooProxy/blob/dev/chart.png)

实现步骤：

![实现步骤](https://github.com/01ly/FooProxy/blob/master/pic/workss.png)

1.**采集数据(Collector)**

采集器进程是一个周期循环，使用了多线程对每一个代理网站进行数据采集，即：一个代理网站爬虫一个线程。因为没有数据共享，这里没有GPL。
项目内置了两个代理数据采集爬虫，一个是个人网站的nyloner,一个是66ip代理网站的爬虫(在crawlers.py文件中)，如果想要增加代理爬虫，
可以自己在custom目录下的custom.py文件中进行增加删减，只需要保证你的爬虫返回的结果数据结构和要求的一致就好。如下:
```python
def some_crawler_func():
    """
    自己定义的一个采集爬虫
    约定：
        1.无参数传入
        2.返回格式是：['<ip>:<port>','<ip>:<port>',...]
        3.写完把函数名加入下面的my_crawlers列表中，如
          my_crawlers = [some_crawler_func,...]
    """
    pass

my_crawlers = []
```
 一个数据采集爬虫函数就是一个采集器，写完函数在my_crawlers中加进去就可以。在config中设置一个周期时间，就可以让爬虫定期采集更新数据。
 > 在采集的过程中，如果出现采集器爬虫被封IP，可以通过自己的APIserver请求代理，然后再继续采集，这一部分没有写，不过可以实现

2.**验证数据(Validator)**

采集器进程和验证器进程共享一个变量:**proxyList**，是一个MultiProcessing.Manger.List对象。可以在多进程中
保持共享数据的同步(理论上)，采集器定期采集的代理数据可以通过proxyList实时的传递给验证器进行有效性验证，因为采集器一次传递的数据比较多，
所以验证器使用异步验证，能大大提高效率，具体使用自带的asyncio实现的.
> 验证器实现基本上也是调用了一个验证api来判断代理的有效性，可以自己更换api实现，可在validator.py中详细了解。在config中可以配置异步的并发量等来控制验证器。

3.**打分存储(Rator)**

打分器进程主要是与验证器配合，当采集器采集的数据经过验证器验证后，确定有效，则让打分器进行评分，中间可以加入自定义数据处理模块，
打分后直接存储在standby数据库，而后供本地检测器进行周期检测，打分器也是一个周期循环，不断的对代理数据进行更新补充。内置在验证器与扫描器中。
打分器主要的三个函数:**mark_success,mark_fail,mark_update**.
>* mark_success  对采集器传递给验证器的代理数据，验证成功后进行一次性的评分并且存储
>* mark_fail  对验证器进行验证，代理无效的数据进行失败打分处理(达到删除条件则删除，否则扣分更新数据库)
>* mark_update 对非初次打分的代理数据进行更新，即验证有效的数据再次验证时仍有效，则进行加分之类的数据库更新

> 具体的评分步骤在下面会详细说明，不过还有很大的提升空间，只是初步试了一下。

4.**循环扫描(Scanner)**

当验证器的有效数据经过打分器存进本地standby数据库中后，怎么保证这一次存进去的数据以后能保证调用时仍可用呢？使用扫描器周期循环检测！扫描器会在你给定的
扫描周期间隔不断地对本地standby数据库进行扫描验证，无效的数据则直接删除，有效的数据会对其得分、响应时间、验证时间等字段进行及时的更新，保证代理数据的实时有效。
> 在扫描器内部其实也是有一个验证函数来进行扫描验证。详见scanner.py

> **2018-11-05新增更新**:
>  **目标代理IP库扫描验证(Tentacle-触手)**:

> 可以在config中设置自己想要生成的只对目标网站有效代理IP数据库，如config中:
```python
#使用代理IP的爬虫目标网站列表 
targets = [
    'https://segmentfault.com/',
    'https://www.csdn.net/',
    'https://www.bilibili.com/',
    'http://www.acfun.cn/'
]
```
> 那么在数据库中便会有对应的有效IP代理库:segmentfault_com,csdn_net,bilibili_com,acfun_cn。

目标代理IP库扫描使用协程，当采集器采集数据通过验证器验证有效后，会把有效代理IP传入验证器内置的Tentacle进行目标网站url有效性验证，验证通过则存入对应的目标库。当
workstation的触手Tentacle开启时，会把指定的目标库进行扫描验证，评分更新或者删除。

5.**择优剔劣(Detector)**

存储在standby数据库中的数据经过扫描器的扫描检测，可以保证其有效性，当是如果想要稳定的代理供给APIserver，那么必须有一个检测器来进行挑拣代理，
Detector会周期性的进行扫描standby和stable两个数据库，对其中符合高分稳定条件的代理存进stable数据库，对失效的高分代理进行剔除，这些都可以在config中
进行自定义配置高分稳定条件。如：
```python
#采集器采集数据时间间隔,单位：秒
COLLECT_TIME_GAP    = 3600*1
#验证器的最大并发量
CONCURRENCY         = 100
#验证器一次取出多少条 抓取的 代理进行验证
VALIDATE_AMOUNT     = 500
#验证器验证抓取数据频率 ： 秒/次
VALIDATE_F          = 5
#验证器请求超时重试次数
VALIDATE_RETRY      = 5
#扫描器的最大并发协程数量
COROUTINE_MAX       = 300
#扫描器一次取出多少条 本地库 的代理进行验证
LOCAL_AMOUNT        = 500
#扫描器验证本地库频率 ： 秒/次
VALIDATE_LOCAL      = 60*1
#检测器检测数据库的频率: 秒/次
DETECT_LOCAL        = 60*1
#检测器一次取出多少条有效库的代理进行筛选
DETECT_AMOUNT       = 1000
#检测器一次取出多少条高分稳定数据库的代理进行检测
DETECT_HIGH_AMOUNT  = 1000
#高分稳定数据库代理数据连续多少次无效则从稳定数据库中剔除
DELETE_COMBO        = 30
#代理IP成功率的最低要求,低于此要求均删除,100次周期测试 0.2=20%
MIN_SUCCESS_RATE    = 0.2
#有效代理数据库数据转至高分稳定数据库的成功率最低要求 0.8=80%
#以及测试总数的最低要求
STABLE_MIN_RATE     = 0.8500
STABLE_MIN_COUNT    = 100
```
因为是对本地数据库的io操作，使用了异步asyncio可以大大提高效率。

6.**API调用(APIserver)**

有了稳定的高分代理数据，那么就可以挂起一个api server为我们的爬虫保驾护航，这一部分可以单独拿出来编写，使用其他框架django之类的都是不错的选择。
项目里只是为了演示使用，使用Flask进行了简单的路由设置，因为测试爬虫在本机，所以使用了下面几个api而已，具体可以自己扩展。
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
## 评分
> 简单的评分可以使代理ip筛选更加简单，其中的具体设置可以再const.settings中更改，一个代理IP数据的得分主要是：
> 1. 一次请求的基础分 score-basic ：100-10x(响应时间-1)
> 2. 请求成功的得分 score-success ： (基础分+测试总数x上一次分数)/(测试总数+1)+自定义成功加分数x成功率x连续成功数
> 3. 请求失败的得分 score-fail : (基础分+测试总数x上一次分数)/(测试总数+1)-自定义失败减分数x失败率x连续失败数
> 4. 稳定性 stability : 得分x成功率x测试数/自定义精度 

> 与三个变量成正比的稳定性根据得分设置可以很快的两极化稳定与不稳定的代理，从而进行筛选。
## 使用
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
 
 ## 示例 
 * 背景：小马要爬取[segmentfault](https://segmentfault.com/),[CSDN](https://www.csdn.net/)中的技术文章,可是爬了一段时间老是被目标网站检测到自己爬虫的机器行为，IP被封了。此时小马想要自己建个IP代理池，用来更换IP爬取，这样也可以把采集数据堆出来
 * 小马下载了FooProxy，并且根据使用提示安装好了对应的库和环境
 * 小马根据自己MongoDB数据库账户设置对config中的DBsettings.py的数据库相关参数进行了对应设置
 * 小马对config中的targets进行设置，把自己要爬取的目标网站列进去:
 ```python
targets = [
    'https://segmentfault.com/',
    'https://www.csdn.net/',
]
```
 * 小马想要的IP代理数据是这样的：
 > 1. 代理IP对目标网站有效，而且代理IP的分数要在60分以上，已经被检测了10次以上
 > 2. 代理IP验证失败可以重试5次，仍然失败则证明该IP无效，等待回应超过30秒则认为失败
 > 3. 代理池对以前自己设置生成的其他目标网站的目标库不进行验证
 > 4. 代理IP一次验证最多300条，验证完再验证下一个300条
 根据上面的需求，小马配置了config对应参数如下:
 ```python
#目标库验证失败重试次数,-1 表示无限次失败重试,0 表示不进行失败重试
RETRIES = 5
#目标库验证请求的超时时间 单位：秒
TIMEOUT = 30
#是否要扫描验证以前的目标网站IP代理库
AGO = False
#验证目标库一次最多验证的条数
MAX_V_COUNT = 300
```
> 根据需求的第一条，小马在APIserver中编写了路由函数:
```python
@app.route('/proxy/target/<string:domain>/<string:suffix>/')
@app.route('/proxy/target/<string:domain>/<string:suffix>')
def get_target_proxy(domain,suffix):
    #定义查询返回条件
    query = {'score':{'>=':60},'test_count':{'>=':10}}
    #按照分数降序排列
    sort_by = {'score':-1}
    db_name = '_'.join([domain.lower().strip(),suffix.lower().strip()])
    if db_name in common_db.handler.list_collection_names():
        proxies = common_db.select(query,tname=db_name,sort=sort_by)
        for i in proxies:
            del i['_id']
        return json.dumps(proxies)
    else:
        return 'Wrong domain or suffix you requested.'
```
* 小马在本机运行FooProxy，过了5分钟后，MongoDB数据库中出现了两个collection: segmentfault_com,csdn_net
* 小马在本机运行爬虫，在自己的爬虫中使用API: ‘http://127.0.0.1:5000/proxy/target/csdn/net’，
获取到了所有满足条件的代理IP,格式如下:
```json
[
    {
        "ip":"180.183.135.46",
        "port":"8080",
        "anony_type":"透明",
        "address":"泰国 ",
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
* 小马在爬虫中根据自己需求选择了代理IP数据进行后续爬取
 
 ## 不足
 * 稳定性没有很好的标准判断，不过100次测试85%以上的成功率就已经很好了
 * ~~没有编写验证器与API服务器的超时请求代理功能~~
 * API 服务器没有单独拿出来编写
 * 还没有加入存活时间的考量
 * ~~还没接入爬虫测试~~
 * ...
 ## 效果
 1. **备用有效数据库**，开启1.5个小时后:
 ![备用有效数据库](https://github.com/01ly/FooProxy/blob/dev/pic/2018-10-09_2-07-47.png)
 2. **高分稳定数据库**
 ![高分稳定数据库](https://github.com/01ly/FooProxy/blob/dev/pic/2018-10-09_2-09-42.png)
 3. **目标代理IP库(csdn为例)**
 ![目标代理IP库](https://github.com/01ly/FooProxy/blob/master/pic/2018-11-05-21-03-00.png)
 ## 后话
 * 比较符合预期
 * 经过连续5天的测试，程序运行正常
 * 备用有效数据库与高分稳定数据库的同步更新误差在5分钟左右
 * 只有一个数据采集爬虫的情况下，一个小时采集一次，一次1000条数据[采集66ip代理网]，8个小时内稳定的有效代理995左右，高分稳定的有200条左右，主要在于代理网站的质量
 * 经过并发爬虫测试，可以使用到实际项目中
 
## 交流讨论

微信公众号:![wx](qrcode.jpg)  
QQ群:![qq](qq.png)