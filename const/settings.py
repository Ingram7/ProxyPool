#coding:utf-8


import random

#代理ip的API接口,此处用FooProxy的API接口
proxy_api = 'http://127.0.0.1:5000/proxy'

#代理ip验证可用性验证接口
proxy_validate_url 	= 'http://www.moguproxy.com/proxy/checkIp/ipList?ip_ports%5B%5D={}%3A{}'
#多重查询接口
mul_validate_url =  'http://www.moguproxy.com/proxy/checkIp/ipList?'
#ip地址查询接口:url+ip
IP_check_url 		= 'https://ip.cn/index.php?ip='
IP_check_url_01     = 'http://www.chacuo.net/?m=ip&act=f&t=1&ip='
IP_check_url_02		= 'https://tool.lu/ip/ajax.html'
IP_check_url_03		= 'http://whois.pconline.com.cn/ip.jsp?ip='
#采集器内置爬虫采集地址
builtin_crawl_urls 	= {
    #count 表示爬取数量
    'nyloner':{
        'url':'https://www.nyloner.cn/proxy',
        'count':1000,
    },
    #其需要的追加参数在下面设置,详见_66ip_params
    '66ip':{
        'url':'http://www.66ip.cn/nmtq.php',
        'count':2000,
    },
    #西刺代理(不建议)500个nn高匿可用的大概最多有10个吧..后面加 nn代表高匿，nt代表透明,wn代表https，wt代表http
    # 'xici':{
    #     'url':'http://www.xicidaili.com/wt',
    #     'count':1000,
    # },
}
_66ip_params = {
    #提取数量
    'getnum': builtin_crawl_urls['66ip']['count'],
    #运营商选择，0：全部运营商，1：中国电信，2：中国联通，3：中国移动，4：中国铁通
    'isp': 0,
    #匿名性选择，0：不限匿名性，1：透明代理，2：普通匿名，3：高级匿名，4：超级匿名
    'anonymoustype': 4,
    #指定IP段
    'start':'',
    #指定端口
    'ports':'',
    #排除端口
    'export':'',
    #指定地区
    'ipaddress':'',
    #过滤条件，0：国内外，1：国内，2：国外，
    'area': 0,
    #代理类型选择，0：http，1：https，2：全部，
    'proxytype': 2,
    'api': '66ip',
}
#sql语句与MongoDB语句的映射
con_map = {
    '=':'$eq',
    '<':'$lt',
    '<=':'$lte',
    '>':'$gt',
    '>=':'$gte',
    '!=':'$ne',
}
#代理数据稳定性精度,数值越大精度越高 200-500间较好,一次更改后不能动
#除非数据库清空后重新进行抓取，保持数据稳定的一致性
PRECISION 		= 500
#失败一次扣除的基本分数
FAIL_BASIC 		= 5
#成功一次增加的基本分
SUCCESS_BASIC 	= 0.1
#日志配置文件路径
LOG_CONF 		= 'log/log.conf'
#运行模式函数映射
RUN_FUNC = {
    'Collector' : 'run_collector',
    'Validator' : 'run_validator',
    'Scanner'   : 'run_scanner',
    'Detector'  : 'run_detector',
	'Tentacle'	: 'run_tentacle'
}
#存放目标网站IP代理库列表的库名
TARGETS_DB = 'targets'
#伪造请求头部浏览器
user_agents = [
	"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
	"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
	"Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
	"Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
	"Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
	"Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
	"Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/523.15 (KHTML, like Gecko, Safari/419.3) Arora/0.3 (Change: 287 c9dfb30)",
	"Mozilla/5.0 (X11; U; Linux; en-US) AppleWebKit/527+ (KHTML, like Gecko, Safari/419.3) Arora/0.6",
	"Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.2pre) Gecko/20070215 K-Ninja/2.1.1",
	"Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9) Gecko/20080705 Firefox/3.0 Kapiko/3.0",
	"Mozilla/5.0 (X11; Linux i686; U;) Gecko/20070322 Kazehakase/0.4.5",
	"Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.8) Gecko Fedora/1.9.0.8-1.fc10 Kazehakase/0.5.6",
	"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.56 Safari/535.11",
	"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_3) AppleWebKit/535.20 (KHTML, like Gecko) Chrome/19.0.1036.7 Safari/535.20",
	"Opera/9.80 (Macintosh; Intel Mac OS X 10.6.8; U; fr) Presto/2.9.168 Version/11.52",
	"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.11 TaoBrowser/2.0 Safari/536.11",
	"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.71 Safari/537.1 LBBROWSER",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; LBBROWSER)",
	"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E; LBBROWSER)",
	"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.84 Safari/535.11 LBBROWSER",
	"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
	"Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; QQBrowser/7.0.3698.400)",
	"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
	"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; Trident/4.0; SV1; QQDownload 732; .NET4.0C; .NET4.0E; 360SE)",
	"Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; QQDownload 732; .NET4.0C; .NET4.0E)",
	"Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E)",
	"Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
	"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/21.0.1180.89 Safari/537.1",
	"Mozilla/5.0 (iPad; U; CPU OS 4_2_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5",
	"Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b13pre) Gecko/20110307 Firefox/4.0b13pre",
	"Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:16.0) Gecko/20100101 Firefox/16.0",
	"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11",
	"Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10"
]
#伪造请求头部
headers = {
	'user-agent': random.choice(user_agents),
}
#验证代理请求头部
v_headers = {
	'user-agent': random.choice(user_agents),
	'Accept': 'application/json, text/plain, */*',
	'Accept-Encoding': 'gzip, deflate',
	'Accept-Language': 'zh-CN,zh;q=0.9',
	'Connection': 'keep-alive',
	'Host': 'www.moguproxy.com',
	'Referer': 'http://www.moguproxy.com/moitor/',
	'X-Requested-With': 'XMLHttpRequest',
}