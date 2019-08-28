# coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-04
"""
import time
import math
import json
import copy
import asyncio
import aiohttp
import logging
from config.DBsettings      import _DB_SETTINGS
from config.DBsettings      import _TABLE
from config.config          import CONCURRENCY
from config.config          import VALIDATE_AMOUNT
from config.config          import VALIDATE_F
from const.settings         import mul_validate_url
from const.settings         import v_headers
from components.rator       import Rator
from components.dbhelper    import Database
from components.tentacle    import Tentacle
from tools.util             import get_proxy

logger = logging.getLogger('Validator')

class Validator(object):
    """
    IP代理数据有效性验证器，对采集器传递过来的代理数据进行有效性验证
    通过内置打分器进行打分存储
    """
    def __init__(self):
        self.db         = Database(_DB_SETTINGS)
        self.db.table   =  _TABLE['standby']
        self.rator      = Rator(self.db)
        self.Tentacle   = Tentacle()

    def check_allot(self,proxies):
        """
        将验证器一次取出的采集器传递过来的待验证代理数据进行分组
        分成几组则有多少个异步协程来验证IP代理数据，一组中有多少个代理IP
        则一个协程一次验证的代理IP就有多少个。建议一次验证的IP数不要太多，
        防止目标验证网站封掉本机IP，如果你已经爬取到一定数量的IP代理并存储
        到standby或stable数据库中，则可以将数值设置大一点，最大不能超过100
        如果是刚刚开始建立FooProxy数据库，则建议将offset设置为2，慢慢爬取建立
        稳定数据库后，再设置大一点的数值。此处设置为20是因为我的本地数据库已经很大。

        Q:为甚要有这个函数？
        A:前期因为使用单个IP代理对应一个异步协程验证，一次取出500个代理进行验证，经常被
        目标验证网站http://www.moguproxy.com封掉IP或者断开连接，此时使用查询分组可以
        减少一次性访问的异步协程的数量，但是如果offset值设置过大会引起目标验证网站的多线程
        验证压力增大，被封IP的几率大大增加，所以设置一个合适的offset比较好。

        Q:那究竟要多大啊这个offset?
        A:前期刚刚开始使用FooProxy项目来建立代理池的话，建议设为2，即是最小值了，此时不会增加目标网站
        的多线程验证压力，不会引起注意，但是也要设置好一次取出的待验证IP代理数据的量，在config中设置
        的VALIDATE_AMOUNT，默认500，可以自己设置100或者更小，看自己需求，offse和VALIDATE_AMOUNT这两个值
        越大被封IP的几率越大，建议前期offset为2，后续代理池稳定下来可以设置更大的值。

        Q:这么麻烦那我自己验证代理有效性不就行了?
        A:这是可以的。由于我比较懒，所以使用了验证网站的接口，也可以自己去访问一些验证服务器来判断返回的
        头部内容，根据response headers中的内容确定匿名程度，以及响应时间。比如访问:http://httpbin.org/get?show_env=1
        但是如果用这种办法，验证用的validate_proxy函数就要重写。

        :param proxies:扫描器一次取出来的待验证的采集器传递过来的的代理IP列表，格式['<ip>:<port>',..]
        :return:返回分组结果,格式 ['查询参数字符串',...]
        """
        p_len = len(proxies)
        offset = 20
        params_dict = []
        if p_len<=offset:
            return ['&'.join(['ip_ports%5B%5D={}%3A{}'.format(i.split(':')[0],i.split(':')[1])
                             for i in proxies ])]
        else:
            base = math.ceil(p_len/offset)
            p_groups = [proxies[i*offset:(i+1)*offset] for i in range(base)]
            for group in p_groups:
                url_str = '&'.join(['ip_ports%5B%5D={}%3A{}'.format(i.split(':')[0],i.split(':')[1])
                             for i in group])
                params_dict.append(url_str)
            return params_dict

    def run(self, proxyList):
        """
        运行验证器
        :param proxyList: 与采集器共享的代理数据变量，负责传递采集器采集到的代理IP数据供给
        验证器进行验证存储
        """
        logger.info('Running Validator.')
        self.rator.begin()
        semaphore = asyncio.Semaphore(CONCURRENCY)
        loop = asyncio.get_event_loop()
        conn = aiohttp.TCPConnector(limit=CONCURRENCY)
        session = aiohttp.ClientSession(loop=loop, connector=conn)
        while 1:
            try:
                if proxyList:
                    self.rator.pull_table(self.db.table)
                    pen = len(proxyList)
                    logger.info('Proxies from Collector is detected,length : %d '%pen)
                    pop_len =  pen if pen <= VALIDATE_AMOUNT else VALIDATE_AMOUNT
                    stanby_proxies =[proxyList.pop() for x in range(pop_len)]
                    prams_dict = self.check_allot(stanby_proxies)
                    logger.info('Start to verify the collected proxy data,amount: %d '%pop_len)
                    tasks = [asyncio.ensure_future(self.validate_proxy(i,semaphore,session)) for i in prams_dict]
                    loop.run_until_complete(asyncio.gather(*tasks))
                    logger.info('Validation finished.Left collected proxies:%d'%len(proxyList))
                    time.sleep(VALIDATE_F)
            except Exception as e:
                logger.error('%s,msg: %s '%(e.__class__,e))
                self.rator.end()
                logger.info('Validator shuts down.')
                return

    async def validate_proxy(self,url_str,sem,session):
        """
         验证器验证函数，可以根据自己的验证逻辑重写
        :param url_str:查询参数字符串
        :param sem:协程的最大并发信号量，控制协程连接数
        :param session:异步请求session
        """
        _proxies = None
        async with sem:
            while 1:
                try:
                    async with session.get(mul_validate_url+url_str,
                                            proxy = _proxies,
                                            headers=v_headers,
                                            ) as response:
                        data = await response.text(encoding='utf-8')
                        data = json.loads(data)
                except Exception as e:
                        _proxies = get_proxy(format=False)
                        if not _proxies:
                            logger.error('No available proxy to retry the request for validation.')
                            return
                        continue
                else:
                    for res in data['msg']:
                        if 'anony' in res and 'time' in res:
                            ip, port = res['ip'],res['port']
                            bullet = {'ip':ip,'port':port,'anony_type':res['anony'],
                                      'address':'','score':0,'valid_time':'',
                                      'resp_time':res['time'],'test_count':0,
                                      'fail_count':0,'createdTime':'','combo_success':1,'combo_fail':0,
                                      'success_rate':'0.00%','stability':0.00}
                            data = copy.deepcopy(bullet)
                            self.rator.mark_success(bullet)
                            await self.Tentacle.specified_validate(self.db,data,session,sem)
                    return