import datetime
import os

from email.utils import formatdate, format_datetime
from config import CONFIG, MODE, RSS_PATH
from utils.log import debug

def GenerateRss(mode, data):
    debug('[Processing] generating rss')
    title = MODE[mode]['title']

    for total in CONFIG['totals']:

        RSS = u'''<?xml version="1.0" encoding="utf-8" ?>
        <rss version="2.0">
        <channel><title>Pixiv%s排行 - 前%s</title>
    　　<link>https://rakuen.thec.me/PixivRss/</link>
    　　<description>就算是排行也要订阅啊混蛋！</description>
    　　<copyright>Under WTFPL</copyright>
    　　<language>zh-CN</language>
    　　<lastBuildDate>%s</lastBuildDate>
    　　<generator>PixivRss by TheC</generator>''' % (title, total, formatdate(localtime = True))

        # 下标不要越界了
        real_total = min(total, len(data))
        for i in range(real_total):
            image = data[i]
            image_link = 'https://www.pixiv.net/artworks/' + str(image['id'])

            # Python 3.6 的 %z 不接受 +09:00，去掉冒号后再解析
            published_at = datetime.datetime.strptime(image['date'].replace(':', ''), '%Y-%m-%dT%H%M%S%z')

            desc  = u'<p>第 %s 位</p>' % image['ranking']
            desc += u'<p>画师：' + image['author']
            desc += u' - 上传于：' + published_at.strftime('%Y-%m-%d %H:%M:%S')
            desc += u' - 阅览数：' + str(image['view'])
            desc += u' - 收藏数：' + str(image['bookmarks'])
            desc += u'</p>'
            desc += u'<p><img src="https://pixiv.cat/%s.jpg"></p>' % image['preview']

            RSS += u'''<item>
                    <title><![CDATA[%s]]></title>
                    <guid isPermaLink="false">%s</guid>
                    <link>%s</link>
                    <description><![CDATA[%s]]></description>
                    <pubDate>%s</pubDate>
                </item>''' % (
                                image['title'],
                                image['id'],
                                image_link,
                                desc,
                                format_datetime(published_at)
                            )

        RSS += u'''</channel></rss>'''

        # 输出到文件
        with open(os.path.join(RSS_PATH, '%s-%s.xml' % (mode, total)), 'w', encoding='utf-8') as f:
            f.write(RSS)

    debug('[Processing] RSS file created')
