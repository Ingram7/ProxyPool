# coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-05
"""

#代理连接数据库
_DB_SETTINGS = {
    'backend'	: 'mongodb',         #数据库类型选择 (MongoDB)
    'host'		: 'localhost',       #数据库主机
    'port'		: 27017,             #数据库主机服务端口
    'user'		: '',                #数据库用户
    'passwd'	: '',                #密码
    'database'  : 'ProxyPool'        #使用数据库名
}
#存储代理数据的数据表，值可以自己命名，键不动
_TABLE = {
    'standby'   :'standby',     #经过验证器验证后，存放有效代理的数据表
    'stable'    :'stable',      #经过检测器循环检测后，存放高分稳定代理的数据表
}
