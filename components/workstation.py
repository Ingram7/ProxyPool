#coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-04
"""

import logging
from APIserver.apiserver    import app
from components.collector   import Collector
from components.validator   import Validator
from components.detector    import Detector
from components.scanner     import Scaner
from components.tentacle    import Tentacle
from multiprocessing        import Pool
from multiprocessing        import Manager
from config.config          import MODE
from const.settings         import RUN_FUNC

logger = logging.getLogger()

class Workstation(object):
    """
    整个项目的启动工作面板
    """
    def __init__(self):
        self.collector = Collector()
        self.validator = Validator()
        self.detector  = Detector()
        self.scanner   = Scaner()
        self.tentacle  = Tentacle()
        self.proxyList = Manager().list()

    def run_validator(self,proxyList):
        self.validator.run(proxyList)

    def run_collector(self,proxyList):
        self.collector.run(proxyList)

    def run_detector(self,*params):
        self.detector.run()

    def run_scanner(self,*params):
        self.scanner.run()

    def run_tentacle(self,*params):
        self.tentacle.run()

    def work(self):
        """
        项目启动，根据config中的MODE配置执行对应的部件
        这样可以隔离部件功能，耦合性较低。异步多进程执行需要
        共享变量，使用了multiprocessing的Manager来生成
        共享List.
        """
        pool = Pool(5)
        func = []
        for i in MODE:
            if MODE[i]:
                func.append(eval('self.'+RUN_FUNC[i]))
        [pool.apply_async(fun,args=(self.proxyList,)) for fun in func]
        pool.close()
        app.run()



