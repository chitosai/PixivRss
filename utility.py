# -*- coding: utf-8 -*-
import urllib2, re, platform, os, sys, time, datetime, json
from cookielib import MozillaCookieJar
from pyquery import PyQuery as J
from config import *

# 分隔符
if platform.system() == 'Windows': SLASH = '\\'
else: SLASH = '/'

ABS_PATH = sys.path[0] + SLASH
TEMP_PATH = ABS_PATH + 'temp' + SLASH 
LOG_PATH = ABS_PATH + 'log' + SLASH
EXIST_FILE = ABS_PATH + 'exist.json'


def FormatTime( time_original, format_original = '%Y年%m月%d日 %H:%M' ):
    date = datetime.datetime.strptime(time_original, format_original)
    return date.strftime('%a, %d %b %Y %H:%M:%S +8000')

def GetCurrentTime():
    return time.strftime('%a, %d %b %Y %H:%M:%S +8000', time.localtime(time.time()))

def escape( text ):
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

def Get( url, data = '', refer = 'http://www.pixiv.net/' ):
    global ABS_PATH
    try:
        cj = MozillaCookieJar( ABS_PATH + 'pixiv.cookie.txt' )

        try :
            cj.load( ABS_PATH + 'pixiv.cookie.txt' )
        except:
            pass # 还没有cookie只好拉倒咯

        ckproc = urllib2.HTTPCookieProcessor( cj )

        opener = urllib2.build_opener( ckproc )
        opener.addheaders = [
            ('Accept-Language', 'zh-CN,zh;q=0.8'),
            ('Accept-Charset', 'UTF-8,*;q=0.5'),
            ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31'),
            ('Referer', refer)
        ]

        if data != '':
            request = urllib2.Request( url = url, data = data )
            res = opener.open( request )
            cj.save() # 只有在post时才保存新获得的cookie
        else:
            res = opener.open( url )

        res = opener.open(url)
        return res.read()

    except:
        print 'Error: unable to get ' + url
        return

# 输出文件
def download(fname, url, refer = 'http://www.pixiv.net/ranking.php'):
    # 检查文件是否存在
    if os.path.exists(fname):
        return

    # 下载
    data = Get(url, refer = refer)

    # 写入
    try:
        f = open(fname, 'w+')
        f.write(data)
        f.close()
    except Exception, err:
        log(url, err)

# DEBUG
def debug(message):
    global DEBUG
    if not DEBUG : return
    print message

def log(pixiv_id, message):
    try:
        f = open( LOG_PATH + time.strftime('%Y-%m-%d.log', time.localtime(time.time())), 'a+')
    except:
        f = open( LOG_PATH + time.strftime('%Y-%m-%d.log', time.localtime(time.time())), 'w+')
    finally:
        debug('DEBUG: ' + str(message))
        f.write( time.strftime('[%H:%M:%S] ',time.localtime(time.time())) + pixiv_id + ', ' + str(message) + '\n' )
        f.close()