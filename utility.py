# -*- coding: utf-8 -*-
import re, time, datetime, json, logging
import requests
from pixivpy3 import *
from config import *
from utils.log import debug, log


if DEBUG and DEBUG_SHOW_REQUEST_DETAIL:
    import http.client as http_client
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def FormatTime(time_original, format_new = '%a, %d %b %Y %H:%M:%S +0900'):
    date = datetime.datetime.strptime(time_original, '%Y-%m-%dT%H:%M:%S+09:00')
    return date.strftime(format_new)


def GetCurrentTime():
    return time.strftime('%a, %d %b %Y %H:%M:%S +0800', time.localtime(time.time()))


def Get(url):
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


class ExtendedPixivPy(AppPixivAPI):
    '''扩展ppy'''

    # 实例化的时候自动从本地文件读取token
    def __init__(self):
        debug('Init ppy class')
        super(self.__class__, self).__init__(timeout=(10, 30))
        # load token
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                tokens = json.load(f)
            if not isinstance(tokens, dict):
                raise ValueError('Token file does not contain a valid JSON object')
            for field in ('access_token', 'refresh_token'):
                value = tokens.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError('Missing or invalid token field: %s' % field)
            self.access_token = tokens['access_token']
            self.refresh_token = tokens['refresh_token']
            debug('Local token loaded')
        except Exception as err:
            log('Failed to load access_token from file')
            log(str(err))
            raise

    # 不知道为什么ppy用的ranking name和p站原生的不一致，在illust_ranking里自动转一下
    def illust_ranking(self, rank_name):
        ppyName = MODE[rank_name]['ppyName']
        return super(self.__class__, self).illust_ranking(ppyName)
