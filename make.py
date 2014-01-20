# -*- coding: utf-8 -*-
import urllib2, re, platform, os, sys, time, datetime
from cookielib import MozillaCookieJar
from pyquery import PyQuery as J
from config import *

import _qiniu

# 分隔符
if platform.system() == 'Windows': SLASH = '\\'
else: SLASH = '/'

ABS_PATH = sys.path[0] + SLASH
IMAGE_PATH = ABS_PATH + 'images' + SLASH 
LOG_PATH = ABS_PATH + 'log' + SLASH

ITEMS = []

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
        print 'unable to get ' + url
        return



def LoginToPixiv():
    debug('Processing: LoginToPixiv')
    data = 'pixiv_id=%s&pass=%s&skip=1&mode=login' % ( CONFIG['PIXIV_USER'], CONFIG['PIXIV_PASS'] )
    return Get( 'http://www.pixiv.net/login.php', data )



# 输出文件
def download(fname, url, refer = 'http://www.pixiv.net/ranking.php'):
    # 检查文件是否存在
    if os.path.exists(fname) : 
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


# 抓pixiv页面
def FetchPixiv(mode):
    debug('Processing: FetchPixiv')
    global ITEMS, DEBUG

    # 获取排行
    html = Get('http://www.pixiv.net/ranking.php?lang=zh&mode=' + mode, refer = '')

    # 查找所需信息
    data = ParseHTML(html.decode('utf-8'))
    
    # 检查一下匹配结果
    if not len(data):
        print 'failed to get ranking list info'
        return

    count = 0
    for image in data:
        count += 1
        pixiv_id = image['id']

        # DEBUG模式下只处理3个条目就输出
        if DEBUG and count > 3 : return

        # 生成RSS中的item
        desc  = u'<![CDATA['
        desc += u'<p>画师：' + image['author']
        desc += u' - 上传于：' + image['date']
        desc += u' - 阅览数：' + image['view']
        desc += u' - 总评分：' + image['score']
        desc += u'</p>'
        desc += u'<p><img src="http://rakuen.thec.me/PixivRss/previews/%s.jpg"></p>' % pixiv_id
        # 量子统计的图片
        desc += u'<p><img src="http://img.tongji.linezing.com/3205125/tongji.gif"></p>'
        desc += u']]>' 

        ITEMS.append(u'''<item>
                    <title>%s</title>
                    <link>%s</link>
                    <description>%s</description>
                    <pubDate>%s</pubDate>
        　　       </item>''' % (
            image['title'], 
            'http://www.pixiv.net/member_illust.php?mode=medium&amp;illust_id=' + pixiv_id, 
            desc,
            image['date']
            )
        )

        debug('Starting: ' + str(count))
        debug('processing: pixiv_id: ' + str(pixiv_id))

        # 下载大图
        img_page = Get('http://www.pixiv.net/member_illust.php?mode=big&illust_id=' + pixiv_id,
                                 refer = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + pixiv_id)
        img_m = re.search('<img src="([^"]+)" onclick="\(window.open\(\'\', \'_self\'\)\)\.close\(\)">', img_page)

        if not img_m:
            print 'Can\'t find big image url'
            return
        else:
            img_url = img_m.group(1)
        
        f = IMAGE_PATH + pixiv_id + '.jpg'

        # 保存大图
        debug('Processing: downloading fullsize image')
        download( f, img_url, refer = 'http://www.pixiv.net/member_illust.php?mode=big&illust_id=' + pixiv_id )

        # 上传到七牛
        debug('Processing: uploading to qiniu')
        r = _qiniu.upload(f)
        if r != True:
            log(pixiv_id, r)

        # 删除大图
        debug('Processing: delete fullsize image')
        # os.remove(f)

        # 暂停一下试试
        debug('Waiting: ---\n')
        time.sleep(1)


# 解析网页
def ParseHTML(html):
    debug('Processing: ParseHTML')
    doc = J(html)
    sections = doc('section.ranking-item')

    if not len(sections):
        print 'CAN\'T FIND SECTION'
        return False

    data = []

    for section in sections:
        item = {}
        item['ranking'] = J(section).attr('data-rank')
        item['title'] = J(section).attr('data-title')
        item['author'] = J(section).attr('data-user-name')
        item['date'] = J(section).attr('data-date')
        item['view'] = J(section).attr('data-view-count')
        item['score'] = J(section).attr('data-total-score')
        item['preview'] = J(section).find('img._thumbnail').attr('data-src')

        m = re.search('&illust_id=(\d+)&', J(section).children('a.work').attr['href'])
        item['id'] = m.group(1)

        data.append(item)

    return data



# 输出rss文件
def GenerateRSS(mode, title):
    debug('Processing: GenerateRSS')
    global CONFIG, ITEMS

    for total in CONFIG['totals']:
        # 有时候因为pixiv那边的bug(?)会少几个条目，这时候只能以实际输出的数量为准了
        if total > len(ITEMS) : 
            real_total = len(ITEMS)
        else:
            real_total = total

        RSS = u'''<rss version="2.0" encoding="utf-8">
        <channel><title>Pixiv%s排行 - 前%s</title>
    　　<link>http://rakuen.thec.me/PixivRss/</link>
    　　<description>就算是排行也要订阅啊混蛋！</description>
    　　<copyright>Under WTFPL</copyright>
    　　<language>zh-CN</language>
    　　<lastBuildDate>%s</lastBuildDate>
    　　<generator>PixivRss by TheC</generator>''' % (title, total, GetCurrentTime())

        # 只输出指定个条目
        for i in range(real_total):
            RSS += ITEMS[i]

        RSS += u'''</channel></rss>'''

        # 输出到文件
        RSS_PATH = ABS_PATH + 'rss' + SLASH
        f = open(RSS_PATH + mode + '-' + str(total) + '.xml', 'w')
        f.write(RSS.encode('utf-8'))
        f.close


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
        f.write( time.strftime('[%H:%M:%S] ',time.localtime(time.time())) + pixiv_id + ', ' + str(message) + '\n' )
        f.close()


    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        param = sys.argv[1]
        if param == 'update-rss':
            mode = sys.argv[2]

            # 验证分类
            if mode == 'daily' : title = u'每日'
            elif mode == 'weekly' : title = u'每周'
            elif mode == 'monthly' : title = u'每月'
            elif mode == 'rookie' : title = u'新人'
            elif mode == 'original' : title = u'原创'
            elif mode == 'male' : title = u'男性向作品'
            elif mode == 'female' : title = u'女性向作品'

            # r18
            elif mode == 'daily_r18' : title = u'每日R-18'
            elif mode == 'weekly_r18' : title = u'每周R-18'
            elif mode == 'male_r18' : title = u'男性向R-18'
            elif mode == 'female_r18' : title = u'女性向R-18'
            elif mode == 'r18g' : title = u'每日R-18G'

            else:
                print 'Unknown Mode'
                exit(1)

            
            # LoginToPixiv()
            FetchPixiv(mode)
            GenerateRSS(mode, title)
    else:
        print 'No params specified'