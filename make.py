# -*- coding: utf-8 -*-

from utility import *
import pchan

# 抓pixiv页面
def FetchPixiv(mode):
    debug('[Processing] get ranking page')
    global DEBUG, TEMP_PATH, MODE

    # 不知道为什么pixivpy的ranking关键字和p站本身不一样，转换一下
    ppyName = MODE[mode]['ppyName']

    # 获取排行
    r = aapi.illust_ranking(ppyName)
    if 'error' in r:
        log('Failed to get %s ranking list, will exit' % mode)
        log(json.dumps(r))
        raise RuntimeError()

    # 筛选出我们需要的数据
    def filter(obj):
        return {
            'id': obj.id,
            'title': obj.title,
            'author': obj.user.name,
            'date': obj.create_date,
            'view': obj.total_view,
            'bookmarks': obj.total_bookmarks,
            'preview': obj.id if obj.page_count == 1 else '%s-1' % obj.id
        }
    data = map(filter, r.illusts)

    # 丢给rss生成
    GenerateRss(mode, data)


# 输出rss文件
def GenerateRss(mode, data):
    debug('[Processing] generating rss')
    global CONFIG, RSS_PATH, MODE
    title = MODE[mode]['title']

    for total in CONFIG['totals']:

        RSS = u'''<rss version="2.0" encoding="utf-8">
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

            desc  = u'<p>画师：' + image['author']
            desc += u' - 上传于：' + FormatTime(image['date'], '%Y-%m-%d %H:%M:%S')
            desc += u' - 阅览数：' + str(image['view'])
            desc += u' - 收藏数：' + str(image['bookmarks'])
            desc += u'</p>'
            desc += u'<p><img src="https://pixiv.cat/%s.jpg"></p>' % image['preview']

            RSS += u'''<item>
                    <title><![CDATA[%s]]></title>
                    <link>%s</link>
                    <description><![CDATA[%s]]></description>
                    <pubDate>%s</pubDate>
                </item>''' % (
                                image['title'], 
                                'http://www.pixiv.net/member_illust.php?mode=medium&amp;illust_id=' + str(image['id']), 
                                desc,
                                FormatTime(image['date'])
                            )

        RSS += u'''</channel></rss>'''

        # 输出到文件
        f = open(os.path.join(RSS_PATH, '%s-%s.xml' % (mode, total)), 'w')
        f.write(RSS.encode('utf-8'))
        f.close

    debug('[Processing] RSS file created')


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


if __name__ == '__main__':
    if len(sys.argv) < 1:
        raise RuntimeError('Specify ranking mode')
        
    mode = sys.argv[1]
    global MODE, aapi

    if mode not in MODE:
        raise RuntimeError('Unknown Mode')
    
    aapi = ExtendedPixivPy()
    FetchPixiv(mode)
        
