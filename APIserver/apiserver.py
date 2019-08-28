# coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-04
"""
import random
import logging
import json
from flask                  import Flask
from components.dbhelper    import Database
from config.DBsettings      import _TABLE
from config.DBsettings      import _DB_SETTINGS

logger      = logging.getLogger('APIserver')
app         = Flask(__name__)
stable_db   = Database(_DB_SETTINGS)
standby_db  = Database(_DB_SETTINGS)
common_db   = Database(_DB_SETTINGS)

standby_db.table    = _TABLE['standby']
stable_db.table     = _TABLE['stable']
standby_db.connect()
stable_db.connect()
common_db.connect()

all_standby_proxy   = standby_db.all()
all_stable_proxy    = stable_db.all()
anony_standby       = [i for i in all_standby_proxy if i['anony_type']=='高匿' and i['combo_fail']==0]
anony_stable        = [i for i in all_stable_proxy if i['anony_type']=='高匿' and i['combo_fail']==0 ]
normal_standby      = [i for i in all_standby_proxy if i['anony_type']=='透明' and i['combo_fail']==0]
normal_stable       = [i for i in all_stable_proxy if i['anony_type']=='透明' and i['combo_fail']==0]

@app.route('/')
def index():
    return 'Welcome to the FooProxy API server homepage.'

@app.route('/proxy/<string:kind>/')
@app.route('/proxy/<string:kind>')
def get_proxy_of(kind='anony'):
    if kind=='anony':
        try:
            proxy = get_a_stable_anonymous()
        except Exception as e:
            logger.error('Error class : %s , msg : %s ' % (e.__class__, e))
            logger.error('No anonymous stable proxy offered.Getting a standby anonymous proxy instead.')
            try:
                proxy = get_a_standby_anonymous()
            except Exception as e:
                logger.error('Error class : %s , msg : %s ' % (e.__class__, e))
                logger.error('No anonymous standby proxy offered.Waiting for a while.')
                proxy = {}
        if proxy.get('_id',False): del proxy['_id']
        return json.dumps(proxy)
    elif kind == 'normal':
        try:
            proxy = get_a_stable_normal()
        except Exception as e:
            logger.error('Error class : %s , msg : %s ' % (e.__class__, e))
            logger.error('No normal stable proxy offered.Getting a standby normal proxy instead.')
            try:
                proxy = get_a_standby_normal()
            except Exception as e:
                logger.error('Error class : %s , msg : %s ' % (e.__class__, e))
                logger.error('No normal standby proxy offered.Waiting for a while.')
                proxy = {}
        if proxy.get('_id',False):del proxy['_id']
        return json.dumps(proxy)
    else:
        logger.error('No type named:%s in the proxy types.' % kind)
        return json.dumps({})

@app.route('/proxy')
@app.route('/proxy/')
def get_proxy():
    global  all_stable_proxy
    global  all_standby_proxy
    if all_stable_proxy:
        proxy = all_stable_proxy.pop()
    else:
        all_stable_proxy = stable_db.all()
        try:
            proxy = all_stable_proxy.pop()
        except Exception as e:
            logger.error('No data in stable database.Wait for a while.')
            logger.info('Popped a proxy from standby database instead.')
            if all_standby_proxy:
                proxy = all_standby_proxy.pop()
            else:
                all_standby_proxy = standby_db.all()
                try:
                    proxy = all_standby_proxy.pop()
                except Exception as e:
                    logger.error('No data in standby database.Wait for a while.')
                    proxy = {}
    if proxy.get('_id',False):del proxy['_id']
    return json.dumps(proxy)

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

def get_a_stable_anonymous():
    global anony_stable
    global all_stable_proxy
    if anony_stable:
        proxy = anony_stable.pop()
    else:
        all_stable_proxy = stable_db.all()
        anony_stable = [i for i in all_stable_proxy if i['anony_type'] == '高匿']
        proxy = anony_stable.pop()
    return proxy

def get_a_stable_normal():
    global normal_stable
    global all_stable_proxy
    if normal_stable:
        proxy = normal_stable.pop()
    else:
        all_stable_proxy = stable_db.all()
        normal_stable = [i for i in all_stable_proxy if i['anony_type'] == '透明']
        proxy = normal_stable.pop()
    return proxy

def get_a_standby_anonymous():
    global anony_standby
    global all_standby_proxy
    if anony_standby:
        proxy = anony_standby.pop()
    else:
        all_standby_proxy = standby_db.all()
        anony_standby = [i for i in all_standby_proxy if i['anony_type'] == '高匿']
        proxy = anony_standby.pop()
    return proxy

def get_a_standby_normal():
    global normal_standby
    global all_standby_proxy
    if normal_standby:
        proxy = normal_standby.pop()
    else:
        all_standby_proxy = standby_db.all()
        normal_standby = [i for i in all_standby_proxy if i['anony_type'] == '透明']
        proxy = normal_standby.pop()
    return proxy






