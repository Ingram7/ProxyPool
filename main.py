#coding:utf-8

"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-10-04
"""
import logging.config
from const.settings         import LOG_CONF
from components.workstation import Workstation

logging.config.fileConfig(LOG_CONF)

if __name__ == '__main__' :
    workstation = Workstation()
    workstation.work()




