# -*- coding: utf-8 -*-
import urllib2, re, platform, os, sys, time, datetime, json, MySQLdb, zlib
from cookielib import MozillaCookieJar
from pyquery import PyQuery as J
from config import *

from StringIO import StringIO
from gzip import GzipFile

# 分隔符
if platform.system() == 'Windows': SLASH = '\\'
else: SLASH = '/'

ABS_PATH     = sys.path[0] + SLASH
TEMP_PATH    = ABS_PATH + 'temp' + SLASH 
PREVIEW_PATH = ABS_PATH + 'previews' + SLASH
RSS_PATH     = ABS_PATH + 'rss' + SLASH
LOG_PATH     = ABS_PATH + 'log' + SLASH

EXIST_FILE   = ABS_PATH + 'exist' + SLASH + '%s.json'

MODE = {
    'daily'     : u'每日',
    'weekly'    : u'每周',
    'monthly'   : u'每月',
    'rookie'    : u'新人',
    'original'  : u'原创',
    'male'      : u'男性向作品',
    'female'    : u'女性向作品',
    
    # r18
    'daily_r18' : u'每日R-18',
    'weekly_r18': u'每周R-18',
    'male_r18'  : u'男性向R-18',
    'female_r18': u'女性向R-18',
    'r18g'      : u'每日R-18G',
}

# 这个id是保存上榜log时用的
MODE_ID = {
    'daily'     : 1,
    'weekly'    : 2,
    'monthly'   : 3,
    'rookie'    : 4,
    'original'  : 5,
    'male'      : 6,
    'female'    : 7,
}


def FormatTime( time_original, format_original = '%Y年%m月%d日 %H:%M' ):
    date = datetime.datetime.strptime(time_original, format_original)
    return date.strftime('%a, %d %b %Y %H:%M:%S +8000')

def GetCurrentTime():
    return time.strftime('%a, %d %b %Y %H:%M:%S +8000', time.localtime(time.time()))

def escape( text ):
    return text.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")

def Get( url, data = '', refer = 'http://www.pixiv.net/', retry = 3 ):
    global ABS_PATH

    cj = MozillaCookieJar( ABS_PATH + 'pixiv.cookie.txt' )

    try :
        cj.load( ABS_PATH + 'pixiv.cookie.txt' )
    except:
        pass # 还没有cookie只好拉倒咯

    ckproc = urllib2.HTTPCookieProcessor( cj )

    opener = urllib2.build_opener( ckproc )
    opener.addheaders = [
        ('Accept', '*/*'),
        ('Accept-Language', 'zh-CN,zh;q=0.8'),
        ('Accept-Charset', 'UTF-8,*;q=0.5'),
        ('Accept-Encoding', 'gzip,deflate'),
        ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31'),
        ('Referer', refer)
    ]

    # 防止海外访问weibo变英文版
    if 'weibo.com' in url:
        opener.addheaders = [('Cookie', 'lang=zh-cn; SUB=Af3TZPWScES9bnItTjr2Ahd5zd6Niw2rzxab0hB4mX3uLwL2MikEk1FZIrAi5RvgAfCWhPyBL4jbuHRggucLT4hUQowTTAZ0ta7TYSBaNttSmZr6c7UIFYgtxRirRyJ6Ww%3D%3D; UV5PAGE=usr512_114; UV5=usrmdins311164')]

    debug('Network: url - ' + url)

    try:
        # 发出请求
        if data != '':
            debug('Network: post')
            debug(data)
            request = urllib2.Request( url = url, data = data )
            res = opener.open( request, timeout = 15 )
            cj.save() # 只有在post时才保存新获得的cookie
        else:
            debug('Network: get')
            res = opener.open( url, timeout = 15 )

        debug('Network: Status Code - ' + str(res.getcode()))

        return GetContent( res )

    except Exception, e:
        # 自动重试，每张图最多3次
        if retry > 0:
            return Get( url, data, refer, retry-1 )
        else:
            log(e, 'Error: unable to get %s [Timeout ?]' % url)
            return False

# 检查http返回的内容是否有压缩
def GetContent( res ):
    # 检查是否被GZIP
    if res.info().get('Content-Encoding') == 'gzip':
        buf = StringIO( res.read() )
        f = GzipFile( fileobj=buf )
        data = f.read()
    elif res.info().get('Content-Encoding') == 'deflate':
        try:
            temp = zlib.decompress( res.read(), -zlib.MAX_WBITS )
        except zlib.error:
            temp = zlib.decompress( res.read() )
        gz = StringIO( temp )
        _res = urllib2.addinfourl( gz, res.headers, res.url, res.code )
        _res.msg = res.msg
        data = _res.read()
    else:
        data = res.read()

    return data    

# 输出文件
def download(fname, url, refer = 'http://www.pixiv.net/ranking.php'):
    # 检查文件是否存在
    if os.path.exists(fname):
        # 检查是否为空
        if os.path.getsize(fname) != 0:
            # 不为空说明已存在，返回True
            return True
        else:
            # 为空说明文件有问题，需要重新下载
            os.remove(fname)

    # 下载
    data = Get(url, refer = refer)

    # 检查
    if not data:
        return False

    # 写入
    try:
        f = open(fname, 'w+')
        f.write(data)
        f.close()
        return True
    except Exception, err:
        log(url, err)
        return False

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
        f.write( time.strftime('[%H:%M:%S] ',time.localtime(time.time())) + str(pixiv_id) + ', ' + str(message) + '\n' )
        f.close()

# 读取exist.json
def ReadExist(mode):
    exist_file = open(EXIST_FILE % mode, 'r')
    exist_list = json.load(exist_file)
    exist_file.close()
    return exist_list

# 更新exist.json
def UpdateExist(mode, exist_list):
    exist_json = json.dumps(exist_list)
    exist_file = open(EXIST_FILE % mode, 'w')
    exist_file.write(exist_json)
    exist_file.close()

# 数据库操作
class DB:
    # 构造函数时连接数据库
    def __init__(self):
        try:
            self._ = MySQLdb.connect( CONFIG['DB_HOST'], CONFIG['DB_USER'], CONFIG['DB_PASS'], CONFIG['DB_NAME'], charset="utf8" )
            self.c  = self._.cursor( MySQLdb.cursors.DictCursor ) # 使fetchall的返回值为带key的字典形式
        except Exception, e:
            log(0, '数据库连接出错 : ' + str(e))
            exit(1)

    # 析构时关闭数据库
    def __del__(self):
        self.c.close()
        self._.close()

    # 查询
    def Query( self, sql, data = None):
        try:
            if data : 
                self.c.execute( sql, data )
            else : 
                self.c.execute( sql )

            return self.c.fetchall()
        except Exception, e:
            log(0,  str(e[0]) + ' : ' + e[1])
            return False

    # 执行
    def Run( self, sql, data ):
        try:
            self.c.execute( sql, data )
            return self._.insert_id()
        except Exception, e:
            log(0,  str(e[0]) + ' : ' + e[1])
            return False