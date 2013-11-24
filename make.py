# -*- coding: utf-8 -*-
import urllib2, re, platform, os, sys, time, datetime
from cookielib import MozillaCookieJar
from pyquery import PyQuery as J

# 输出的条目类型
CONFIG = {
    'totals' : [10, 20, 30, 40, 50],
    'PIXIV_USER' : 'pixivrss@sina.com',
    'PIXIV_PASS' : '111000'
}

# 是否开启DEBUG模式
DEBUG = False

# 分隔符
if platform.system() == 'Windows': SLASH = '\\'
else: SLASH = '/'

ABS_PATH = sys.path[0] + SLASH

ITEMS = []

def FormatTime( time_original, format_original = '%Y年%m月%d日 %H:%M' ):
    date = datetime.datetime.strptime(time_original, format_original)
    return date.strftime('%a, %d %b %Y %H:%M:%S +8000')

def GetCurrentTime():
    return time.strftime('%a, %d %b %Y %H:%M:%S +8000', time.localtime(time.time()))


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
    f = open(fname, 'wb')
    f.write(data)
    f.close()


# 抓pixiv页面
def FetchPixiv(mode):
    debug('Processing: FetchPixiv')
    global ITEMS

    # 获取排行
    html = Get('http://www.pixiv.net/ranking.php?lang=zh&mode=' + mode, refer = '')
    # download('a.html', 'http://www.pixiv.net/ranking.php?lang=zh&mode=' + mode, refer = '')

    # 查找所需信息
    data = ParseHTML(html)
    
    # 检查一下匹配结果
    if not len(data):
        print 'failed to get ranking list info'
        return

    # 准备下载图
    PREVIEW_PATH = ABS_PATH + 'previews' + SLASH
    # IMAGE_PATH = ABS_PATH + 'images' + SLASH

    # 清理现有大图
    # if mode == 'male' : 
    #     image_list = os.listdir(IMAGE_PATH)
    #     for image in image_list:
    #         if image == '.gitignore' : continue
    #         os.remove( IMAGE_PATH + image )

    count = 0
    for image in data:
        # 生成RSS中的item
        desc  = '<![CDATA['
        desc += '<p>画师：%s - 上传于：%s - 阅览数：%s - 总评分：%s</p>' % ( image['author'], image['date'], image['view'], image['score'] );
        desc += '<p><img src="http://rakuen.thec.me/PixivRss/previews/%s.jpg"></p>' % image['id']
        # 量子统计的图片
        desc += '<p><img src="http://img.tongji.linezing.com/3205125/tongji.gif"></p>'
        desc += ']]>' 
        ITEMS.append('''<item>
                    <title>%s</title>
                    <link>%s</link>
                    <description>%s</description>
                    <pubDate>%s</pubDate>
        　　       </item>''' % (
            image['title'], 
            'http://www.pixiv.net/member_illust.php?mode=medium&amp;illust_id=' + image['id'], 
            desc,
            image['date']
            )
        )

        debug('processing: ' + str(count))
        count += 1

        # 下载预览图...
        download( PREVIEW_PATH + image['id'] + '.jpg', image['preview'] )

        # # 只有男性排行抓图大图回来
        # if mode != 'male': continue

        # # 和大图
        # img_page = Get('http://www.pixiv.net/member_illust.php?mode=big&illust_id=' + image[1],
        #                          refer = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + image[1])
        # img_m = re.search('<img src="([^"]+)" onclick="\(window.open\(\'\', \'_self\'\)\)\.close\(\)">', img_page)

        # if not img_m:
        #     print 'Can\'t find big image url'
        #     return
        # else:
        #     img_url = img_m.group(1)
        
        # # 保存大图
        # download( IMAGE_PATH + image[1] + '.jpg', img_url, refer = 'http://www.pixiv.net/member_illust.php?mode=big&illust_id=' + image[1] )

        # 暂停一下试试
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
        item['ranking'] = J(section).attr['data-rank'].encode('utf-8')
        item['title'] = J(section).attr['data-title'].encode('utf-8')
        item['author'] = J(section).attr['data-user-name'].encode('utf-8')
        item['date'] = J(section).attr['data-date'].encode('utf-8')
        item['view'] = J(section).attr['data-view-count'].encode('utf-8')
        item['score'] = J(section).attr['data-total-score'].encode('utf-8')
        item['preview'] = J(section).find('img._thumbnail').attr['data-src']

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

        RSS = '''<rss version="2.0" encoding="utf-8">
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

        RSS += '''</channel></rss>'''

        # 输出到文件
        RSS_PATH = ABS_PATH + 'rss' + SLASH
        f = open(RSS_PATH + mode + '-' + str(total) + '.xml', 'w')
        f.write(RSS)
        f.close


# DEBUG
def debug(message):
    if not DEBUG : return
    print message


    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        param = sys.argv[1]
        if param == 'update-rss':
            mode = sys.argv[2]

            # 验证分类
            if mode == 'daily' : title = '每日'
            elif mode == 'weekly' : title = '每周'
            elif mode == 'monthly' : title = '每月'
            elif mode == 'rookie' : title = '新人'
            elif mode == 'original' : title = '原创'
            elif mode == 'male' : title = '男性向作品'
            elif mode == 'female' : title = '女性向作品'

            # r18
            elif mode == 'daily_r18' : title = '每日R-18'
            elif mode == 'weekly_r18' : title = '每周R-18'
            elif mode == 'male_r18' : title = '男性向R-18'
            elif mode == 'female_r18' : title = '女性向R-18'
            elif mode == 'r18g' : title = '每日R-18G'

            else:
                print 'Unknown Mode'
                exit(1)

            # r18排行需要登录
            if 'r18' in mode:
                LoginToPixiv()

            FetchPixiv(mode)
            GenerateRSS(mode, title)
    else:
        print 'No params specified'


