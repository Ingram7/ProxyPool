#coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-05
"""
import time
import logging
from tools.util         import time_to_date
from tools.util         import get_ip_addr_03
from config.DBsettings  import _TABLE
from const.settings     import PRECISION
from config.config      import MIN_SUCCESS_RATE
from const.settings     import FAIL_BASIC,SUCCESS_BASIC

logger = logging.getLogger('Rator')

class Rator(object):
    """
    打分器，对代理IP的打分存储，内置于验证器和扫描器中
    """
    def __init__(self,db):
        """
        初始化
        :param db: 打分器对应的数据库，即要将代理数据进行存储、更新、删除操作的数据库
        """
        self.raw_filter     = set()
        self.local_data     = []
        self.db             = db

    def begin(self):
        self.db.table = _TABLE['standby']
        self.db.connect()

    def end(self):
        self.db.close()

    def pull_table(self,tname):
        """
        将数据库中某个数据集的所有IP数据存入过滤器，防止重复存储打分
        :param tname:数据集名称
        """
        if not tname:
            return
        table_data = self.db.all(tname)
        for i in table_data:
            self.raw_filter.add(':'.join([i['ip'],i['port']]))

    def mark_success(self,data):
        """
        代理IP数据经过验证器验证成功，进行第一次的打分存储
        :param data: 单个要存储的代理IP数据，dict类型
        """
        ip = data['ip']
        port = data['port']
        # proxy = ':'.join([ip,port])
        _data = self.db.select({'ip':ip,'port':port})
        if _data:
            self.mark_update(data)
            return
        address = get_ip_addr_03(ip)
        elapsed = round(int(data['resp_time'].replace('ms', '')) / 1000, 3)
        score = round(100 - 10 * (elapsed - 1), 2)
        stability = round(score/PRECISION,4)
        valid_time = time_to_date(int(time.time()))
        data['createdTime'] = valid_time
        data['valid_time'] = valid_time
        data['address'] = address
        data['score'] = score
        data['test_count'] = 1
        data['stability'] = stability
        data['success_rate'] = '100%'
        self.db.save(data)

    def mark_fail(self,data):
        """
        对第二次或以上的单个代理IP数据进行验证失败的打分更新操作，
        将combo_fail+1,combo_success置0,以及对其扣分，满足删除条件则直接删除
        :param data:单个IP代理数据 dict 类型
        """
        if data:
            ip = data['ip']
            port = data['port']
            proxy = ':'.join([ip, port])
            _score = data['score']
            _count = data['test_count']
            _f_count = data['fail_count']
            _success_rate = data['success_rate']
            _combo_fail = data['combo_fail']
            valid_time = time_to_date(int(time.time()))
            data['score'] = round(_score-FAIL_BASIC*((_f_count+1)/(_count+1))*(_combo_fail+1),2)
            data['combo_fail']    = _combo_fail+1
            data['combo_success'] = 0
            data['test_count']    = _count+1
            data['fail_count']    = _f_count+1
            data['valid_time']    = valid_time
            success_rate = round(1-((_f_count+1)/( _count+1)),3)
            data['success_rate'] = str(success_rate*100) + '%'
            data['stability'] = round(data['score']*data['test_count']*
                                             success_rate /PRECISION,4)
            if (_count >= 100 and _success_rate <= str(MIN_SUCCESS_RATE*100)+'%') or \
                    int(_score) < 0:
                logger.warning('Deleting unstable proxy: %s '%proxy)
                self.db.delete({'ip':ip,'port':port})
            else:
                self.db.update({'ip':ip,'port':port},data)

    def mark_update(self,data,collected=True):
        """
        对单个代理IP数据进行验证成功的打分更新操作，
        将combo_success+1,combo_fail置0,以及对其加分
        :param data: 单个代理IP数据 dict类型
        :param collected: 是否是第一次进行验证的代理
        """
        ip = data['ip']
        port = data['port']
        proxy = ':'.join([ip, port])
        valid_time = time_to_date(int(time.time()))
        data['valid_time'] = valid_time
        elapsed = round(int(data['resp_time'].replace('ms', '')) / 1000, 3)
        score = round(100 - 10 * (elapsed - 1), 2)
        if collected:
            try:
                _one_data = self.db.select({'ip':ip,'port':port})[0]
            except Exception as e:
                return
        else:
            _one_data = data
        if _one_data:
            _score = _one_data['score']
            if int(_score) < 0:
                logger.warning('Deleting unstable proxy: %s ' % proxy)
                self.db.delete({'ip': ip, 'port': port})
                return
            _count = _one_data['test_count']
            _f_count = _one_data['fail_count']
            _address = _one_data['address']
            _combo_success = _one_data['combo_success']
            _created_time = _one_data['createdTime']
            _success_rate = round(float(_one_data['success_rate'].replace('%',''))/100,4)
            score = round((score+_score*_count)/(_count+1)+SUCCESS_BASIC*(_combo_success+1)*_success_rate,2)
            address = get_ip_addr_03(ip)
            address = _address if address == 'unknown' else address
            success_rate = round(1-(_f_count/(_count+1)),3)
            stability = round(score*(_count+1)*success_rate/PRECISION,4)
            data['fail_count'] = _f_count
            data['createdTime'] = _created_time
            data['combo_fail'] = 0
            data['address'] = address
            data['score'] = score
            data['test_count'] = _count+1
            data['combo_success'] = _combo_success+1
            data['success_rate'] = str(success_rate*100)+'%'
            data['stability'] = stability
            if data.get('_id',False):del data['_id']
            self.db.update({'ip':ip,'port':port},data)
