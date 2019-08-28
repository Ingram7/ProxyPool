#coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-11-03
"""
import time
import datetime
import logging
import random
import asyncio
import aiohttp
from string             import ascii_letters
from tools.util         import format_proxies
from tools.util         import time_to_date
from config.config      import VALIDATE_LOCAL
from config.config      import MAX_V_COUNT
from const.settings     import headers
from const.settings     import TARGETS_DB
from config.config      import targets
from config.config      import AGO
from config.config      import MAX_T_LEN
from config.config      import TARGET_EXPIRE
from config.config      import TIMEOUT
from config.config      import RETRIES
from config.DBsettings  import _DB_SETTINGS
from tools.util         import gen_target_db_name
from tools.util         import get_ip_addr
from tools.util         import internet_access
from tools.async_tools  import send_async_http
from components.dbhelper import Database

logger = logging.getLogger('Tentacle')

class Tentacle(object):
    """
    目标库扫描验证类，可以内置在其他部件中，是workstation的“触手”，对
    每一个获得的代理IP针对目标网址进行逐个验证，并对本地存有的目标库
    进行定时检测扫描，剔除无效的代理IP
    """
    def __init__(self,targets=targets):
        """
        初始化
        :param targets: 默认加载config中的目标url列表targets
        """
        self.targets = targets
        self.db = Database(_DB_SETTINGS)

    def begin(self):
        """
        做开始扫描验证前的准备工作：
        * 连接数据库
        * 清除过期的目标库
        * 保存更新存储目标库信息的targets数据库
        """
        self.db.connect()
        self.clean_expired_targets()
        self.save_targets()

    def end(self):
        self.db.close()

    def load_target_db(self) -> dict:
        """
        加载所有待验证目标库中的所有数据
        """
        _targets = set()
        allowed_targets = []
        _dict = {}
        if AGO:
            targets_inside = self.db.all(tname=TARGETS_DB)
            for i in targets_inside:
                url = i['url']
                if url in self.targets:
                    continue
                elif url:
                    _targets.add(url)
        [allowed_targets.extend(i) for i in (self.targets,_targets)]
        for url in allowed_targets:
            _name = gen_target_db_name(url)
            _data = self.db.all(tname=_name)
            _dict[url] = _data
            logger.info('Loaded %d proxies from db: %s '%(len(_data),_name))
        return _dict

    def save_targets(self):
        """
        保存当前config设置的targets信息到数据库
        """
        data = {}
        now = datetime.datetime.now()
        j = 0
        for i in targets:
            inside_data = self.db.select({'url': i}, tname=TARGETS_DB)
            if inside_data:
                self.db.update({'url': i},{'validTime':now.isoformat()},tname=TARGETS_DB)
                continue
            data['url'] = i
            data['createdTime'] = now.isoformat()
            data['validTime'] = now.isoformat()
            data['db'] = gen_target_db_name(i)
            data['_id'] = str(j + random.randint(0,100000))+\
                          ascii_letters[random.randint(0,52)]+\
                          str(int(time.time()*1000))
            self.db.save(data, tname=TARGETS_DB)

    def clean_expired_targets(self):
        """
        清除过期目标库
        """
        if not self.db.connected:
            return
        now = datetime.datetime.now()
        expired_created_time = (now - datetime.timedelta(days=TARGET_EXPIRE)).isoformat()
        all_data = self.db.all(tname=TARGETS_DB)
        for tar in all_data:
            if tar['validTime'] < expired_created_time:
                db_name = gen_target_db_name(tar['url'])
                _std_count = self.db.handler[db_name].drop()
                self.db.delete({'url':tar['url']},tname=TARGETS_DB)
                logger.info('Deleted expired target website proxy collection:(%s)' % (db_name))

    def run(self):
        """
        运行Tentacle
        逻辑：
        * 创建单一异步session，使用信号量控制连接池
        * 判断是否联网
        * 联网则加载需要扫描验证的目标库数据
        * 每一个目标库扫一遍作为一个周期
        * 在扫每一个目标库时加入一次性扫描最大数限制MAX_V_COUNT
        """
        logger.info('Running Tentacle.')
        self.begin()
        loop = asyncio.get_event_loop()
        sem = asyncio.Semaphore(MAX_V_COUNT)
        conn = aiohttp.TCPConnector(verify_ssl=False, limit=MAX_V_COUNT)
        session = aiohttp.ClientSession(loop=loop, connector=conn)
        while 1:
            if not internet_access():
                continue
            try:
                _dict = self.load_target_db()
                for url in _dict:
                    logger.info('Start the validation of the target url:%s'%url)
                    data = _dict[url]
                    _len = len(data)
                    _count = MAX_V_COUNT if MAX_V_COUNT <= _len else _len
                    start = 0
                    while 1:
                        _data = data[start:start+_count]
                        if not _data:
                            logger.info('Target url:%s -> validation finished,total proxies:%d'%(url,_len))
                            break
                        tasks = []
                        for i in _data:
                            ip = i['ip']
                            port = i['port']
                            proxy = format_proxies(':'.join([ip,port]))
                            tasks.append(self.async_visit_target(self.db,url,proxy,i,sem,session))
                        loop.run_until_complete(asyncio.gather(*tasks))
                        start += _count
                time.sleep(VALIDATE_LOCAL)
            except Exception as e:
                self.end()
                logger.error('%s,msg: %s ' % (e.__class__, e))
                logger.error('Shut down the Tentacle.')

    async def async_visit_target(self,db,url,proxy,bullet,sem,session,scan=True):
        """
        异步请求协程，对单个代理IP数据进行异步验证
        :param db:处理操作的数据库
        :param url:目标网站url
        :param proxy:要验证对目标网址是否有用的代理IP，dict类型
        :param bullet:单个代理ip对象的所有数据
        :param sem:协程并发信号量
        :param session:异步请求session
        :param scan:是否进行的是目标库扫描操作，False则表示进行的是初次入库验证
        """
        data = {
            'ip': bullet['ip'],
            'port': bullet['port'],
            'anony_type': bullet['anony_type'],
            'address': bullet['address'],
            'createdTime': bullet['createdTime'],
            'score':bullet['score'],
            'test_count': int(bullet['test_count']) + 1,
            'url': url,
        }
        db_name = gen_target_db_name(url)
        async with sem:
            ret = await send_async_http(session, 'head', url,
                                        retries=RETRIES,
                                        headers=headers,
                                        proxy=proxy['http'],
                                        timeout=TIMEOUT)
            t, code = ret['cost'], ret['code']
            if code == 200:
                data['score'] = round(
                    (bullet['score'] * bullet['test_count'] + round((1 - t / 15) * 100, 2)) / data['test_count'], 2)
                data['total'] = round(data['score'] * data['test_count'], 2)
                data['resp_time'] = str(t) + 's'
                data['valid_time'] = time_to_date(int(time.time()))
                if scan:
                    self.update(db,data,db_name)
                else:
                    self.success(db,data,db_name)
            else:
                if scan:
                    self.fail(db,data,db_name)

    async def specified_validate(self,db,bullet,session,sem):
        """
        初次入库验证协程，内置在Validator中的Tentacle调用此协程进行代理Ip
        从采集器中采集验证后进行初次入目标库的验证操作
        :param db:处理操作的数据库对象
        :param bullet:单个代理ip对象的所有数据
        :param session:异步请求session
        :param sem:协程并发信号量
        """
        ip = bullet['ip']
        port = bullet['port']
        proxy = format_proxies(':'.join([ip, port]))
        max_thread_count = MAX_T_LEN if MAX_T_LEN <= len(self.targets) else len(self.targets)
        allowed_targets = self.targets[:max_thread_count]
        tasks = [self.async_visit_target(db,i,proxy,bullet,sem,session,scan=False) for i in allowed_targets]
        resp = asyncio.gather(*tasks)
        await resp

    def success(self,db,bullet,tname):
        """
        初次在Validator中调用触手成功验证目标url后进行入库操作
        :param db: 处理操作的数据库对象
        :param bullet: 单个代理ip对象的所有数据
        :param tname: 目标url对应的数据集合
        """
        ip = bullet['ip']
        port = bullet['port']
        _data = db.select({'ip':ip,'port':port},tname=tname)
        bullet['address'] = get_ip_addr(ip) if bullet['address'] == 'unknown' or\
                                               bullet['address'] == '' else bullet['address']
        if _data:
            bullet['_id'] = _data[0]['_id']
            self.update(db,bullet,tname)
            return
        bullet['createdTime'] = time_to_date(int(time.time()))
        try:
            db.save(bullet,tname=tname)
        except Exception as e:
            logger.error('%s,msg: %s ' % (e.__class__, e))
            return

    def update(self,db,bullet,tname):
        """
        验证成功后对已存在于目标库中的代理数据进行更新
        :param db: 处理操作的数据库对象
        :param bullet: 单个代理ip对象的所有数据
        :param tname: 目标url对应的数据集合
        """
        ip = bullet['ip']
        port = bullet['port']
        if bullet['createdTime']=='':
            bullet['createdTime']=time_to_date(int(time.time()))
        bullet['address'] = get_ip_addr(ip) if bullet['address'] == 'unknown' or \
                                               bullet['address'] == '' else bullet['address']
        db.update({'ip':ip,'port':port},bullet,tname=tname)

    def fail(self,db,bullet,tname):
        """
        验证失败对已存在于目标库中的代理数据进行失败操作
        :param db: 处理操作的数据库对象
        :param bullet: 单个代理ip对象的所有数据
        :param tname: 目标url对应的数据集合
        """
        try:
            ip = bullet['ip']
            port = bullet['port']
            proxy = ':'.join([ip,port])
            db.delete({'ip':ip,'port':port},tname=tname)
            logger.warning('Deleted inoperative proxy %s in %s'%(proxy,tname))
        except Exception as e:
            logger.error('%s,msg: %s ' % (e.__class__, e))
            return