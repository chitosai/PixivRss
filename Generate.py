# -*- coding: utf-8 -*-
import urllib2, re, datetime, platform, os, sys, time
from config import *
from cookielib import MozillaCookieJar

# 分隔符
if platform.system() == 'Windows': SLASH = '\\'
else: SLASH = '/'

ABS_PATH = sys.path[0] + SLASH
PHP_SESSION_ID = 0

HTML = '''
<!doctype html>
<html lang="cn">
<head>
    <meta charset="UTF-8">
    <title>%s</title>
    <link rel="stylesheet" href="inc/pixivwall.css">
</head>
<body>
    <div id="wall-wrapper"></div>
    <div id="origins">%s</div>
    <script src="inc/jquery-1.9.1.min.js"></script>
    <script src="inc/jquery.transit.min.js"></script>
    <script src="inc/pixivwall.animations.js"></script>
    <script src="inc/pixivwall.js"></script>
    <script>
        DURATION = %s;
        DELAY = %s;
        CUBE_SIZE = %s;
    </script>
</body>
</html>
'''

# 生成静态页面
def GenerateHTML():
    # 获取图片列表
    IMAGE_PATH = sys.path[0] + SLASH + 'images' + SLASH
    IMAGE_LIST = os.listdir(IMAGE_PATH)

    IMAGES = '\n'
    for image in IMAGE_LIST:
        if image == '.gitignore' : continue
        IMAGES += '\t\t<img class="origin" src="images/' + image + '" />\n'
    IMAGES += '\t'
    # 生成新静态页面
    f = open('index.html', 'w')
    f.write( HTML % (
        CONFIG['page_title'], 
        IMAGES, 
        CONFIG['animation_duration'],
        CONFIG['animation_delay'], 
        CONFIG['cube_size']
    ))
    f.close()



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

        return res.read()

    except:
        print 'unable to fetch ' + url
        return

def LoginToPixiv():
    # 然后登录
    data = 'pixiv_id=%s&pass=%s&skip=1&mode=login' % (PIXIV_USER, PIXIV_PASS)
    return Get( 'http://www.pixiv.net/login.php', data )


# 抓pixiv页面
def FetchPixiv(mode):
    # 验证分类
    if mode == 'daily' : title = '总'
    elif mode == 'weekly' : title = '本周'
    elif mode == 'monthly' : title = '本月'
    elif mode == 'rookie' : title = '新人'
    elif mode == 'original' : title = '原创'
    elif mode == 'male' : title = '男性'
    elif mode == 'female' : title = '女性'
    else:
        print 'Unknown Mode'
        return

    # 先登录
    LoginToPixiv()

    # 获取排行
    html = Get('http://www.pixiv.net/ranking.php?mode=' + mode, refer = '')

    # 查找所需信息
    m = re.findall('<a class="image-thumbnail" href="[^"]+"><img class="ui-scroll-view" data-filter="lazy-image" data-src="([^"]+)" src="http://source\.pixiv\.net/source/images/common/transparent\.gif"></a><div class="data"><h2><a href="member_illust\.php\?mode=medium&amp;illust_id=(\d+)&amp;ref=[\w\d\-]+">(.+?)</a></h2><a href="member\.php\?id=\d+&amp;ref=[\w\d\-]+" class="user-container"><img class="user-icon ui-scroll-view" data-filter="lazy-image" data-src="[^"]+" src="[^"]+" height="32">(.+?)</a><dl class="stat"><dt class="view">閱覽數</dt><dd>(\d+)</dd><dt class="score">總分</dt><dd>(\d+)</dd></dl><dl class="meta"><dt class="date">投稿日期</dt><dd>(.+?)</dd></dl>', html)
    
    # 检查一下匹配结果
    if not len(m):
        print 'failed to get ranking list info'
        return

    RSS = '''<rss version="2.0" encoding="utf-8" xmlns:content="http://purl.org/rss/1.0/modules/content/">
    <channel><title>Pixiv%s排行</title>
　　<link>http://rakuen.thec.me/PixivWall/</link>
　　<description>就算是排行也要订阅啊混蛋！</description>
　　<copyright>Under WTFPL</copyright>
　　<language>zh-CN</language>
　　<lastBuildDate>%s</lastBuildDate>
　　<generator>PixivWall by TheC</generator>''' % (title, datetime.datetime.now())

    # 准备下载图
    PREVIEW_PATH = ABS_PATH + 'previews' + SLASH
    IMAGE_PATH = ABS_PATH + 'images' + SLASH

    # 清理现有大图
    if mode == 'male' : 
        image_list = os.listdir(IMAGE_PATH)
        for image in image_list:
            if image == '.gitignore' : continue
            os.remove( IMAGE_PATH + image )

    for image in m:
        # 生成RSS中的item
        desc = '<![CDATA[<p>画师：' + image[3] + ' - 上传于：' + image[6] + ' - 阅览数：' + image[4] + ' - 总评分：' + image[5] + '</p>';
        desc += '<p><img src="http://rakuen.thec.me/PixivWall/previews/%s.jpg"></p>]]>' % image[1]
        RSS += '''<item>
                    <title>%s</title>
                    <link>%s</link>
                    <description>%s</description>
                    <content:encoded>%s</content:encoded>
                    <pubDate>%s</pubDate>
        　　       </item>''' % (
            image[2], 
            'http://www.pixiv.net/member_illust.php?mode=medium&amp;illust_id=' + image[1], 
            desc,
            desc,
            image[6])

        # 下载预览图...
        preview = Get(image[0], refer = 'http://www.pixiv.net/ranking.php')
        f = open(PREVIEW_PATH + image[1] + '.jpg', 'wb')
        f.write(preview)
        f.close()

        # 只有男性排行抓图大图回来
        if mode != 'male': continue

        # 和大图
        img_page = Get('http://www.pixiv.net/member_illust.php?mode=big&illust_id=' + image[1],
                                 refer = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + image[1])
        img_m = re.search('<img src="([^"]+)" onclick="\(window.open\(\'\', \'_self\'\)\)\.close\(\)">', img_page)

        if not img_m:
            print 'Can\'t find big image url'
            return
        else:
            img_url = img_m.group(1)
        
        # 保存大图
        img = Get(img_url)
        if img != None:
            f = open(IMAGE_PATH + image[1] + '.jpg', 'wb')
            f.write(img)
            f.close()

        # 暂停一下试试
        time.sleep(1)

    RSS += '''</channel></rss>'''

    # 输出RSS
    RSS_PATH = ABS_PATH + 'rss' + SLASH
    f = open(RSS_PATH + mode + '.xml', 'w')
    f.write(RSS)
    f.close

    
if __name__ == '__main__':
    if len(sys.argv) > 1:
        param = sys.argv[1]
        if param == 'update-rss':
            FetchPixiv(sys.argv[2])
    else:
        print 'No params specified'

