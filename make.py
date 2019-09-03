# -*- coding: utf-8 -*-

from utility import *
import pchan

MAX_WEIBO_PER_HOUR = 6

# 抓pixiv页面
def FetchPixiv(mode):
    debug('[Processing] get ranking page')
    global DEBUG, PREVIEW_PATH, TEMP_PATH, MODE

    # 不知道为什么pixivpy的ranking关键字和p站本身不一样，转换一下
    ppyName = MODE[mode]['ppyName']

    # 获取排行
    r = aapi.illust_ranking(ppyName)
    if 'error' in r:
        log('Failed to get %s ranking list, will exit' % mode)
        log(json.dumps(r))
        raise RuntimeError()

    # 把获取到的list处理成我们需要的形式
    def filter(obj):
        return {
            'id': obj.id,
            'title': obj.title,
            'author': obj.user.name,
            'date': obj.create_date,
            'view': obj.total_view,
            'bookmarks': obj.total_bookmarks
        }
    
    data = map(filter, r.illusts)


# 输出rss文件
def GenerateRss(mode, title):
    debug('[Processing] generating rss')
    global CONFIG, RSS_PATH

    # 读取exist.json
    exist_list = ReadExist(mode)
    order = sorted(exist_list.items(), key = lambda item: item[1]['ranking'])

    for total in CONFIG['totals']:
        # 有时候因为pixiv那边的bug(?)会少几个条目，这时候只能以实际输出的数量为准了
        if total > len(order):
            real_total = len(order)
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
            image = order[i][1]
            # 生成RSS中的item
            desc  = u'<p>画师：' + image['author']
            desc += u' - 上传于：' + image['date']
            desc += u' - 阅览数：' + image['view']
            desc += u' - 点赞数：' + image['score']
            desc += u'</p>'

            # 插入动图提示
            if image.get('isAnimated', False): desc += u'<p>** 原图为动图 **</p>'

            desc += u'<p><img src="%s"></p>' % image['image']
            # 量子统计的图片
            # desc += u'<p><img src="http://img.tongji.linezing.com/3205125/tongji.gif"></p>'

            RSS += u'''<item>
                        <title><![CDATA[%s]]></title>
                        <link>%s</link>
                        <description><![CDATA[%s]]></description>
                        <pubDate>%s</pubDate>
            　　       </item>''' % (
                    image['title'], 
                    'http://www.pixiv.net/member_illust.php?mode=medium&amp;illust_id=' + image['id'], 
                    desc,
                    image['date']
                    )

        RSS += u'''</channel></rss>'''

        # 输出到文件
        f = open(os.path.join(RSS_PATH, '%s-%s.xml' % (mode, total)), 'w')
        f.write(RSS.encode('utf-8'))
        f.close

    debug('[Processing] All work done, exit.')

def CheckTokenStatus():
    tokens = ReadToken()
    if not tokens:
        log('Token file empty, getting new token')
        UpdateToken()
    else:
        debug('Token file loaded')
        aapi.set_auth(tokens['response']['access_token'])
    try:
        debug('Verifying token')
        r = aapi.illust_ranking('day_r18')
        if 'error' in r:
            log('Token error? check it, will try to get a new token now')
            log(json.dumps(r))
            UpdateToken()
        else:
            debug('Token OK')
    except PixivError as err:
        if 'Authentication require' in str(err):
            log('Token expired, getting new token')
            UpdateToken()

__TOKEN_GENERATED = False
def UpdateToken():
    global __TOKEN_GENERATED
    if __TOKEN_GENERATED:
        log('Already tried to get token once, this method shouldn\'t be called twice!')
        raise RuntimeError('Already tried to get token once, this method shouldn\'t be called twice!') # end the process
    else:
        log('Getting new token')
        tokens = aapi.login(CONFIG['PIXIV_USER'], CONFIG['PIXIV_PASS'])
        aapi.set_auth(tokens.response.access_token)
        SaveToken(tokens)
        log('New token saved')
        __TOKEN_GENERATED = True
        return tokens


if __name__ == '__main__':
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        global MODE

        # 验证分类
        if mode in MODE:
            CheckTokenStatus()
            FetchPixiv(mode)
        else:
            print 'Unknown Mode'
            Raise RuntimeError('Unknown Mode')
    else:
        print 'No params specified'
