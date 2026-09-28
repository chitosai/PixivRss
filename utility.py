# -*- coding: utf-8 -*-
import requests

from config import *
from utils.log import debug, log


def get(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.8',
        'Accept-Charset': 'UTF-8,*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, sdch',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36'
    }
    # 防止海外访问weibo变英文版
    cookies = {
        'lang': 'zh-cn',
        'SUB': 'Af3TZPWScES9bnItTjr2Ahd5zd6Niw2rzxab0hB4mX3uLwL2MikEk1FZIrAi5RvgAfCWhPyBL4jbuHRggucLT4hUQowTTAZ0ta7TYSBaNttSmZr6c7UIFYgtxRirRyJ6Ww%3D%3D',
        'UV5PAGE': 'usr512_114',
        'UV5': 'usrmdins311164'
    }
    debug('[Network] new http request: get ' + url)
    try:
        r = requests.get(url, headers = headers, cookies = cookies, timeout = 6)
        debug('[Network] response status code: %s' % r.status_code)
    except Exception as e:
        log('unable to get %s, error message:' % url)
        log(e)
        return False
    # 判断返回内容是不是纯文本
    if 'text/html' in r.headers['Content-Type']:
        return r.text
    else:
        return r.content
