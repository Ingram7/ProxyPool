#coding:utf-8
"""
    @author  : linkin
    @email   : yooleak@outlook.com
    @date    : 2018-11-07
"""
import asyncio
import datetime

async def send_async_http(session,method,url,*,
                             retries=1,
                             interval=1,
                             wait_factor=2,
                             timeout=30,
                             success_callback=None,
                             fail_callback=None,
                             **kwargs) -> dict:
    """
    发送一个异步请求至某个特定url，实现失败重试
    每一次失败后会延时一段时间再去重试，延时时间由
    interval和wait_factor决定
    :param session:请求的异步session
    :param method:请求方法
    :param url:请求url
    :param retries:失败重试次数
    :param interval:失败后的再次异步请求的延时时长
    :param wait_factor:每一次失败后延时乘以这个因子，延长重试等待时间,一般1<wf<2,即延时最多2^retries秒
    :param timeout:连接超时时长
    :param success_callback:成功回调函数
    :param fail_callback:失败回调函数
    :param kwargs:其他键值参数
    :return:返回字典结果
    """
    exception = None
    ret = {'cost':None,'code':0,'exception':exception,'tries':-1}
    wait_interval = interval
    if method.lower() not in ['get', 'head', 'post']:
        return ret
    if retries == -1:  # -1 表示无限次失败重试
        attempt = -1
    elif retries == 0:  # 0 表示不进行失败重试
        attempt = 1
    else:
        attempt = retries + 1
    while attempt != 0:
        try:
            start = datetime.datetime.now()
            async with getattr(session,method)(url,timeout=timeout,**kwargs) as response:
                end = datetime.datetime.now()
                t = (end - start).total_seconds()
                code = response.status
                ret = {'cost': t, 'code': code, 'tries': retries - attempt+1}
                if success_callback:
                    success_callback(ret)
                return ret
        except Exception as e:
            ret['exception'] = e
            ret['tries'] += 1
            await asyncio.sleep(wait_interval)
            wait_interval = wait_interval * wait_factor
        attempt-=1
    if fail_callback:
        fail_callback(ret)
    return ret