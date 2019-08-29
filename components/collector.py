#coding:utf-8


import time
import logging
from tools.threads          import CrawlThread
from components.crawlers    import builtin_crawlers
from custom.custom          import  my_crawlers
from inspect                import isfunction
from config.config          import COLLECT_TIME_GAP

logger = logging.getLogger('Collector')

class Collector(object):
    """
    负责对IP代理数据的有效采集，供给验证器进行验证入库
    """
    def __init__(self):
        self.__proxyList = None
        self.__crawlers  = my_crawlers

    def find_crawlers(self):
        """
        查找采集器包含的代理采集爬虫，包含内置的和自定义的
        :return: 找到的爬虫 list 类型
        """
        _crawlers = [i for i in builtin_crawlers if isfunction(i)]
        custom_crawlers = [i for i in self.__crawlers if isfunction(i)]
        _crawlers.extend(custom_crawlers)
        logger.info('Find  %d  data collectors.'%len(_crawlers))
        return _crawlers

    def run(self,proxyList):
        """
        运行采集器，使用多线程进行采集，一个采集爬虫一个线程，采集结果存入proxyList
        :param proxyList: 与验证器共享的变量，存储采集到的IP代理数据，list类型
        """
        while 1:
            results = []
            t_res   = set()
            self.__proxyList = proxyList
            funcs = self.find_crawlers()
            threads = [CrawlThread(i) for i in funcs]
            for i in threads:
                i.start()
            for i in threads:
                i.join()
                results.append(i.get_result())
            for res in results:
                logger.info('Received %d proxy data from a spider.'%len(res))
                for x in res:
                    t_res.add(x)
            self.__proxyList.extend(t_res)
            time.sleep(COLLECT_TIME_GAP)
