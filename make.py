# -*- coding: utf-8 -*-
from utility import *


def GenerateRss(mode, data):
    debug('[Processing] generating rss')
    global CONFIG, RSS_PATH, MODE
    title = MODE[mode]['title']

    for total in CONFIG['totals']:

        RSS = u'''<rss version="2.0">
        <channel><title>Pixiv%s排行 - 前%s</title>
    　　<link>http://rakuen.thec.me/PixivRss/</link>
    　　<description>就算是排行也要订阅啊混蛋！</description>
    　　<copyright>Under WTFPL</copyright>
    　　<language>zh-CN</language>
    　　<lastBuildDate>%s</lastBuildDate>
    　　<generator>PixivRss by TheC</generator>''' % (title, total, GetCurrentTime())

        # 下标不要越界了
        real_total = min(total, len(data))
        for i in range(real_total):
            image = data[i]
            image_link = 'http://www.pixiv.net/member_illust.php?mode=medium&amp;illust_id=' + str(image['id'])

            desc  = u'<p>第 %s 位</p>' % image['ranking']
            desc += u'<p>画师：' + image['author']
            desc += u' - 上传于：' + FormatTime(image['date'], '%Y-%m-%d %H:%M:%S')
            desc += u' - 阅览数：' + str(image['view'])
            desc += u' - 收藏数：' + str(image['bookmarks'])
            desc += u'</p>'
            desc += u'<p><img src="https://pixiv.cat/%s.jpg"></p>' % image['preview']

            RSS += u'''<item>
                    <title><![CDATA[%s]]></title>
                    <guid>%s</guid>
                    <link>%s</link>
                    <description><![CDATA[%s]]></description>
                    <pubDate>%s</pubDate>
                </item>''' % (
                                image['title'],
                                image_link,
                                image_link,
                                desc,
                                FormatTime(image['date'])
                            )

        RSS += u'''</channel></rss>'''

        # 输出到文件
        f = open(os.path.join(RSS_PATH, '%s-%s.xml' % (mode, total)), 'w')
        f.write(RSS.encode('utf-8'))
        f.close

    debug('[Processing] RSS file created')


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        raise RuntimeError('Specify ranking name')
        
    mode = sys.argv[1]
    global MODE

    if mode not in MODE:
        raise RuntimeError('Unknown ranking name')
    
    aapi = ExtendedPixivPy()
    data = FetchPixiv(aapi, mode)
    GenerateRss(mode, data)