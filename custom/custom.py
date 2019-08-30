#coding:utf-8

import requests
from bs4 import BeautifulSoup

# def some_crawler_func():
#     """
#     自己定义的一个采集爬虫
#     约定：
#         1.无参数传入
#         2.返回格式是：['<ip>:<port>','<ip>:<port>',...]
#         3.写完把函数名加入下面的my_crawlers列表中，如
#           my_crawlers = [some_crawler_func,...]
#     """
#     pass
#
#


def crawlProxy01():

    url = 'https://github.com/dxxzst/free-proxy-list'
    headers = {
        'User-Agent': "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50"}
    try:
        r = requests.get(url, headers=headers)
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find_all('table')[1]

    except :
        pass

    else:
        res = []
        for tr in table.find_all('tr')[1:]:
            a = tr.text.split("\n")
            if a[4] == 'high':
                res.append("{}:{}".format(a[1], a[2]))
        print('======crawlProxy01======')
        print(res)
        return res


import re
from my_tools_add.WebRequest import WebRequest
from my_tools_add.utilFunction import getHtmlTree


def crawlProxy02():
    """
    https://proxy.coderbusy.com/
    """
    try:
        urls = ['https://proxy.coderbusy.com/']
        res = []
        for url in urls:
            tree = getHtmlTree(url)
            proxy_list = tree.xpath('.//table//tr')
            for tr in proxy_list[1:]:
                i = ':'.join(tr.xpath('./td/text()')[0:2])
                res.append(i)
        print('======crawlProxy02======')
        print(res)
        return res
    except:
        pass


def crawlProxy03():
    """
    http://www.ip3366.net/free/
    """
    try:
        urls = ['http://www.ip3366.net/free/?stype=1',
                'http://www.ip3366.net/free/?stype=2']
        res = []
        request = WebRequest()
        for url in urls:
            r = request.get(url, timeout=10)
            proxies = re.findall(r'<td>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})</td>[\s\S]*?<td>(\d+)</td>', r.text)
            for proxy in proxies:
                res.append(':'.join(proxy))
        print('======crawlProxy03======')
        print(res)
        return res

    except:
        pass


def crawlProxy04():
    """
    http://www.iphai.com/free/ng
    """
    try:
        urls = [
            'http://www.iphai.com/free/ng',
            'http://www.iphai.com/free/np',
            'http://www.iphai.com/free/wg',
            'http://www.iphai.com/free/wp'
        ]
        res = []
        request = WebRequest()
        for url in urls:
            r = request.get(url, timeout=10)
            proxies = re.findall(r'<td>\s*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s*?</td>[\s\S]*?<td>\s*?(\d+)\s*?</td>',
                                 r.text)
            for proxy in proxies:
                res.append(":".join(proxy))
        print('======crawlProxy04======')
        print(res)
        return res

    except:
        pass


def crawlProxy05():
    """
    http://ip.jiangxianli.com/?page=
    """
    try:
        res = []
        for i in range(1, 2 + 1):
            url = 'http://ip.jiangxianli.com/?page={}'.format(i)
            html_tree = getHtmlTree(url)
            tr_list = html_tree.xpath("/html/body/div[1]/div/div[1]/div[2]/table/tbody/tr")
            if len(tr_list) == 0:
                continue
            for tr in tr_list:
                i = tr.xpath("./td[2]/text()")[0] + ":" + tr.xpath("./td[3]/text()")[0]
                res.append(i)
        print('======crawlProxy05======')
        print(res)
        return res

    except:
        pass



my_crawlers = [crawlProxy01,
               crawlProxy02,
               crawlProxy03,
               crawlProxy04,
               crawlProxy05,]