# -*- coding: utf-8 -*-
import re, time, datetime, json, logging, MySQLdb
import requests
from pixivpy3 import *
from config import *


if DEBUG and DEBUG_SHOW_REQUEST_DETAIL:
    import httplib as http_client
    http_client.HTTPConnection.debuglevel = 1
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True


def FormatTime(time_original, format_new = '%a, %d %b %Y %H:%M:%S +9000'):
    date = datetime.datetime.strptime(time_original, '%Y-%m-%dT%H:%M:%S+09:00')
    return date.strftime(format_new)


def GetCurrentTime():
    return time.strftime('%a, %d %b %Y %H:%M:%S +8000', time.localtime(time.time()))


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
    except Exception, e:
        log('unable to get %s, error message:' % url)
        log(e)
        return False
    # 判断返回内容是不是纯文本
    if 'text/html' in r.headers['Content-Type']:
        return r.text
    else:
        return r.content


__LOG_LEVEL = 0
def SetLogLevel(delta):
    global __LOG_LEVEL
    __LOG_LEVEL += delta

# DEBUG
def debug(message):
    global DEBUG
    if DEBUG:
        print __LOG_LEVEL * '  ' + message


def log(pixiv_id, message = None):
    if not message:
        message = pixiv_id
        pixiv_id = -1
    try:
        f = open(os.path.join(LOG_PATH, time.strftime('%Y-%m-%d.log', time.localtime(time.time()))), 'a+')
    except:
        f = open(os.path.join(LOG_PATH, time.strftime('%Y-%m-%d.log', time.localtime(time.time()))), 'w+')
    finally:
        debug(message)
        f.write('%s %s, %s\n' % (time.strftime('[%H:%M:%S] ',time.localtime(time.time())), pixiv_id, message))
        f.close()


# 数据库操作
class DB:
    # 构造函数时连接数据库
    def __init__(self):
        try:
            self._ = MySQLdb.connect( CONFIG['DB_HOST'], CONFIG['DB_USER'], CONFIG['DB_PASS'], CONFIG['DB_NAME'], charset="utf8" )
            self.c  = self._.cursor( MySQLdb.cursors.DictCursor ) # 使fetchall的返回值为带key的字典形式
        except Exception, e:
            log(-1, '数据库连接出错 : %s' % e)
            exit(1)

    # 析构时关闭数据库
    def __del__(self):
        self.c.close()
        self._.close()

    # 查询
    def Query(self, sql, data = None):
        try:
            if data: 
                self.c.execute(sql, data)
            else : 
                self.c.execute(sql)
            return self.c.fetchall()
        except Exception, e:
            log('Error in DB Query')
            log(str(e))
            return False

    # 执行
    def Run(self, sql, data):
        try:
            self.c.execute(sql, data)
            return self._.insert_id()
        except Exception, e:
            log('Error in DB execute')
            log(str(e))
            return False


class ExtendedPixivPy(AppPixivAPI):
    '''扩展ppy'''

    # 实例化的时候自动从本地文件读取token
    def __init__(self):
        debug('Init ppy class')
        super(self.__class__, self).__init__()
        try:
            f = open(TOKEN_FILE, 'r')
            tokens = json.load(f)
            f.close()
            self.access_token = tokens['access_token']
            self.refresh_token = tokens['refresh_token']
            debug('Local token loaded, will verify it')
        except:
            debug('Local token empty, try login')
            self.login(CONFIG['PIXIV_USER'], CONFIG['PIXIV_PASS'])
            debug('After login, will verify token')
        finally:
            self.verifyToken()
    
    # 验证token
    def verifyToken(self, retry = False):
        try:
            r = self.user_detail(100)
            if 'error' in r:
                if not retry:
                    debug('Token expired, try refresh')
                    self.auth()
                    debug('Refreshed, will verify it')
                    self.verifyToken(True)
                else:
                    # 已经尝试refresh过一次token，还是报错，可能是有问题
                    log('Token verify failed again, will exit')
                    log(json.dumps(r))
                    raise RuntimeError('Token verify failed again, will exit')
            else:
                debug('Token OK')
                self.saveToken()
        except PixivError as err:
            log('Error in login')
            log(str(err))
            raise RuntimeError('Error in login')
    
    # 保存token
    def saveToken(self):
        f = open(TOKEN_FILE, 'w')
        f.write(json.dumps({
            'access_token': self.access_token,
            'refresh_token': self.refresh_token
        }))
        f.close()

    # 不知道为什么ppy用的ranking name和p站原生的不一致，在illust_ranking里自动转一下
    def illust_ranking(self, rank_name):
        ppyName = MODE[rank_name]['ppyName']
        return super(self.__class__, self).illust_ranking(ppyName)


def FetchPixiv(aapi, mode):
    # 获取排行
    debug('Get %s ranking page' % mode)
    r = aapi.illust_ranking(mode)
    if 'error' in r:
        log('Failed to get %s ranking list, will exit' % mode)
        log(json.dumps(r))
        raise RuntimeError()

    # 筛选出我们需要的数据
    tmp = {
        'ranking': 0 # 这个ranking直接作为int传入filter会造成无法修改，所以稿一个dict，用修改attr的方式实现
    }
    def filter(obj):
        tmp['ranking'] += 1
        return {
            'id': obj.id,
            'title': obj.title,
            'author': obj.user.name,
            'uid': obj.user.id,
            'date': obj.create_date,
            'view': obj.total_view,
            'bookmarks': obj.total_bookmarks,
            'preview': obj.id if obj.page_count == 1 else '%s-1' % obj.id,
            'ranking': tmp['ranking'], # 这幅图在榜上排第几，好像暂时只能靠这样自己加
            'images': {
                'medium': obj.image_urls.medium,
                'large': obj.image_urls.large
            }
        }
    data = map(filter, r.illusts)
    return data