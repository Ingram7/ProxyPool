#coding:utf-8



#采集器采集数据时间间隔,单位：秒
COLLECT_TIME_GAP    = 3600*1
#验证器的最大并发量
CONCURRENCY         = 300
#验证器一次取出多少条 抓取的 代理进行验证
VALIDATE_AMOUNT     = 500
#验证器验证抓取数据频率 ： 秒/次
VALIDATE_F          = 5
#验证器请求超时重试次数
VALIDATE_RETRY      = 4
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
DELETE_COMBO        = 20
#代理IP成功率的最低要求,低于此要求均删除,100次周期测试 0.4=40%
MIN_SUCCESS_RATE    = 0.4
#有效代理数据库数据转至高分稳定数据库的成功率最低要求 0.9=90%
#以及测试总数的最低要求
STABLE_MIN_RATE     = 0.9000
STABLE_MIN_COUNT    = 100
#目标网站IP代理库验证扫描的最大数，即最多验证多少个目标网站(包含数据库中已存在的),超出部分不会验证
MAX_T_LEN = 20
#验证目标库一次最多验证的条数
MAX_V_COUNT = 300
#是否要扫描验证以前的目标网站IP代理库
AGO = False
#目标库验证请求的超时时间 单位：秒
TIMEOUT = 20
#目标库验证失败重试次数,-1 表示无限次失败重试,0 表示不进行失败重试
RETRIES = 3
#使用代理IP的爬虫目标网站列表,最多 MAX_T_LEN 个
targets = [
    # 'https://segmentfault.com/',
    # 'https://www.csdn.net/',
    'https://www.bilibili.com/',
    # 'http://www.acfun.cn/'
]
#连续超过多少天没有进行验证的目标网站IP代理库则自动删除,单位:天
TARGET_EXPIRE = 3
#运行模式,置 1 表示运行，置 0 表示 不运行
#全置 0 表示只运行 API server
MODE = {
    'Collector' : 1,    #代理采集
    'Validator' : 1,    #验证存储
    'Scanner'   : 1,    #扫描本地库
    'Detector'  : 1,    #高分检测
    'Tentacle'  : 1,    #目标库验证扫描
}
