# -*- coding: utf-8 -*-
from utility import *


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
                'large': obj.image_urls.large,
                'original': obj.meta_single_page.original_image_url if hasattr(obj.meta_single_page, 'original_image_url') else obj.meta_pages[0].image_urls.original
            }
        }
    data = list(map(filter, r.illusts))
    return data


def GenerateRss(mode, data):
    debug('[Processing] generating rss')
    global CONFIG, RSS_PATH, MODE
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
    　　<generator>PixivRss by TheC</generator>''' % (title, total, GetCurrentTime())

        # 下标不要越界了
        real_total = min(total, len(data))
        for i in range(real_total):
            image = data[i]
            image_link = 'https://www.pixiv.net/artworks/' + str(image['id'])

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
                                image['id'],
                                image_link,
                                desc,
                                FormatTime(image['date'])
                            )

        RSS += u'''</channel></rss>'''

        # 输出到文件
        f = open(os.path.join(RSS_PATH, '%s-%s.xml' % (mode, total)), 'w')
        f.write(RSS)
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