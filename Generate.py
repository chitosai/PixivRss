# -*- coding: utf-8 -*-
import urllib2, re, datetime, platform, os, sys

# 分隔符
if platform.system() == 'Windows': SLASH = '\\'
else: SLASH = '/'

CONFIG = {
	'page_title'         : 'ただ一人の楽園', # 静态页面标题
	'animation_duration' : 1,               # 动画持续时间
	'animation_delay'    : 3,               # 图片更换间隔
	'cube_size'          : 100              # 区块大小
}

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


# 抓pixiv页面
def FetchPixiv(mode):
    # 获取排行
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.31 (KHTML, like Gecko) Chrome/26.0.1410.64 Safari/537.31')]
    urllib2.install_opener( opener )

    html = urllib2.urlopen('http://www.pixiv.net/ranking.php?mode=' + mode).read()

    # 查找图片地址
    m = re.findall('<a class="image-thumbnail" href="[^"]+"><img class="ui-scroll-view" data-filter="lazy-image" data-src="([^"]+)" src="http://source.pixiv.net/source/images/common/transparent.gif"></a><div class="data"><h2><a href="member_illust\.php\?mode=medium&amp;illust_id=(\d+)&amp;ref=[\w\d\-]+">(.+?)</a></h2><a href="member\.php\?id=\d+&amp;ref=[\w\d\-]+" class="user-container"><img class="user-icon ui-scroll-view" data-filter="lazy-image" data-src="[^"]+" src="[^"]+" height="32">(.+?)</a><dl class="stat"><dt class="view">Views</dt><dd>(\d+)</dd><dt class="score">Total</dt><dd>(\d+)</dd></dl><dl class="meta"><dt class="date">Date submitted</dt><dd>(.+?)</dd></dl>', html)
    
    # 检查一下匹配结果
    if not len(m):
        print 'ERROR'
        return

    # 生成rss
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

    RSS = '''<rss version="2.0" encoding="utf-8" xmlns:content="http://purl.org/rss/1.0/modules/content/">
    <channel><title>Pixiv%s排行</title>
　　<link>http://rakuen.thec.me/PixivWall/</link>
　　<description>就算是排行也要订阅啊混蛋！</description>
　　<copyright>Under WTFPL</copyright>
　　<language>zh-CN</language>
　　<lastBuildDate>%s</lastBuildDate>
　　<generator>PixivWall by TheC</generator>''' % (title, datetime.datetime.now())

    
    for image in m:
        desc = '<![CDATA[<p>画师：' + image[3] + ' - 上传于：' + image[6] + ' - 阅览数：' + image[4] + ' - 总评分：' + image[5] + '</p>';
        desc += '<p><img src="%s"></p>]]>' % image[0]
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

    RSS += '''</channel></rss>'''

    # 输出RSS
    RSS_PATH = sys.path[0] + SLASH + 'rss' + SLASH
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

