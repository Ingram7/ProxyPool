#coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-04
"""
import threading

class CrawlThread(threading.Thread):
    """
    采集爬虫的线程封装，只是多加了一个结果提取函数get_result
    """
    def __init__(self, func, args=() ):
        super(CrawlThread, self).__init__()
        self.func = func
        self.args = args
        self.setDaemon(True)

    def run(self):
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception as e:
            return None


