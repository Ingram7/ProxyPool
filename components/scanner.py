#coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-08
"""
import time
import json
import math
import logging
import aiohttp
import asyncio
from config.DBsettings      import _DB_SETTINGS
from config.DBsettings      import _TABLE
from config.config          import COROUTINE_MAX
from config.config          import LOCAL_AMOUNT
from config.config          import VALIDATE_LOCAL
from const.settings         import mul_validate_url
from const.settings         import v_headers
from components.rator       import Rator
from components.dbhelper    import Database
from tools.util             import find_proxy
from tools.util             import get_proxy

logger = logging.getLogger('Scanner')

class Scaner(object):
    """
    本地扫描器，对本地standby有效代理数据库中的数据进行周期验证
    保证其以后调用数据的实时验证，通过内置打分器进行打分存储
    """
    def __init__(self):
        self.db = Database(_DB_SETTINGS)
        self.db.table = _TABLE['standby']
        self.rator = Rator(self.db)
        self.standby_data = []

    def check_allot(self,proxies):
        """
        将扫描器一次取出的要验证的本地standby数据库有效代理数据进行分组
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
        的LOCAL_AMOUNT，默认500，可以自己设置100或者更小，看自己需求，offse和LOCAL_AMOUNT这两个值
        越大被封IP的几率越大，建议前期offset为2，后续代理池稳定下来可以设置更大的值。

        Q:这么麻烦那我自己验证代理有效性不就行了?
        A:这是可以的。由于我比较懒，所以使用了验证网站的接口，也可以自己去访问一些验证服务器来判断返回的
        头部内容，根据response headers中的内容确定匿名程度，以及响应时间。比如访问:http://httpbin.org/get?show_env=1
        但是如果用这种办法，验证用的validate异步协程函数就要重写。

        :param proxies:扫描器一次取出来的待验证本地standby有效数据库的代理IP列表，格式[{},{},..]
        :return:返回分组结果,格式 {'查询参数字符串':[{},{},..],'查询参数字符串':[{},{},..],..}
        查询参数字符串对应的值为分组后的一组代理IP数据，dict类型
        """
        p_len = len(proxies)
        offset = 20
        params_dict = {}
        if p_len<=offset:
            return {'&'.join(['ip_ports%5B%5D={}%3A{}'.format(i['ip'],i['port'])
                             for i in proxies]):proxies}
        else:
            base = math.ceil(p_len/offset)
            p_groups = [proxies[i*offset:(i+1)*offset] for i in range(base)]
            for group in p_groups:
                url_str = '&'.join(['ip_ports%5B%5D={}%3A{}'.format(i['ip'],i['port'])
                             for i in group])
                params_dict[url_str] = group
            return params_dict

    def run(self):
        """
        运行本地扫描器
        """
        logger.info('Running Scanner.')
        self.rator.begin()
        loop = asyncio.get_event_loop()
        while 1:
            try:
                if self.standby_data :
                    pen = len(self.standby_data )
                    logger.info('Start the validation of the local "standby" database,length : %d ' % pen)
                    pop_len = pen if pen <= LOCAL_AMOUNT else LOCAL_AMOUNT
                    stanby_proxies = [self.standby_data.pop() for x in range(pop_len)]
                    prams_dict = self.check_allot(stanby_proxies)
                    semaphore = asyncio.Semaphore(COROUTINE_MAX)
                    logger.info('Start to verify the standby proxy data,amount: %d ' % pop_len)
                    tasks = [asyncio.ensure_future(self.validate(i,prams_dict[i],semaphore)) for i in prams_dict]
                    loop.run_until_complete(asyncio.gather(*tasks))
                    logger.info('Local validation finished.Left standby proxies:%d' % len(self.standby_data ))
                    time.sleep(VALIDATE_LOCAL)
                else:
                    self.standby_data = self.db.all()
            except Exception as e:
                logger.error('Error class : %s , msg : %s ' % (e.__class__, e))
                self.rator.end()
                loop.close()
                logger.info('Scanner shuts down.')
                return

    async def validate(self,url_str, proxies,semaphore):
        """
        异步验证协程，对本地standby中的代理数据进行异步验证
        :param url_str: IP代理分组中一个组的验证查询参数字符串
        :param proxies: 查询参数字符串对应的IP代理组
        :param semaphore: 协程最大并发量信号
        """
        _proxy = None
        async with semaphore:
            async with aiohttp.ClientSession() as session:
                while 1:
                    try:
                        async with session.get(mul_validate_url+url_str,
                                       headers=v_headers,proxy=_proxy) as response:
                            data = await response.text(encoding='utf-8')
                            data = json.loads(data)
                    except Exception as e:
                        _proxy = get_proxy(format=False)
                        if not _proxy:
                            logger.error('No available proxy to retry the request for validation.')
                            return
                        continue
                    else:
                        for res in data['msg']:
                            proxy = find_proxy(res['ip'],res['port'],proxies)
                            try:
                                if 'anony' in res and 'time' in res:
                                    proxy['anony_type'] = res['anony']
                                    proxy['resp_time'] = res['time']
                                    self.rator.mark_update(proxy, collected=False)
                                else:
                                    self.rator.mark_fail(proxy)
                            except KeyError as e:
                                logger.error('Error class : %s , msg : %s ' % (e.__class__, e))
                                continue
                        return
