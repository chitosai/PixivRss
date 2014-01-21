# -*- coding: utf-8 -*-

from utility import *

import _qiniu

ITEMS = []

def LoginToPixiv():
    debug('Processing: LoginToPixiv')
    data = 'pixiv_id=%s&pass=%s&skip=1&mode=login' % ( CONFIG['PIXIV_USER'], CONFIG['PIXIV_PASS'] )
    return Get( 'http://www.pixiv.net/login.php', data )

# 抓pixiv页面
def FetchPixiv(mode):
    debug('Processing: FetchPixiv')
    global ITEMS, DEBUG

    # 读取已下载的图片列表
    exist_file = open(EXIST_FILE, 'r')
    exist_list = json.load(exist_file)
    exist_file.close()

    # 获取排行
    html = Get('http://www.pixiv.net/ranking.php?lang=zh&mode=' + mode, refer = '')

    # 查找所需信息
    data = ParseRankingPage(html.decode('utf-8'))
    
    # 检查一下匹配结果
    if not len(data):
        print 'failed to get ranking list info'
        return

    count = 0
    for image in data:
        count += 1

        # DEBUG模式下只处理3个条目就退出
        if DEBUG and count > 3 : return

        pixiv_id = image['id']

        debug('Starting: ' + str(count))
        debug('processing: pixiv_id: ' + str(pixiv_id))

        # 检查是否已存在
        # 不存在，需要下载：
        if pixiv_id not in exist_list:

            # 直接下载medium页面的图
            html = Get('http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + pixiv_id)

            # 解析图片地址
            doc = J(html)
            img = doc('.works_display img')

            if not len(img):
                log(pixiv_id, 'ERROR: CAN\'T FIND IMAGE in medium page')
                continue

            img_url = J(img).attr('src')
            debug('Processing: find image url: ' + img_url)

            # # 访问medium页面，查找大图页面地址
            # medium_page = Get('http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + pixiv_id)
            # large_page = re.search('member_illust\.php\?mode=(manga|big)&amp;illust_id=\d+', medium_page)
            # if not large_page:
            #     log(pixiv_id, 'Can\'t find big_page url')
            #     continue
            # else:
            #     large_type = large_page.group(1)

            # # 下载大图
            # img_page = Get('http://www.pixiv.net/member_illust.php?mode=%s&illust_id=%s' % (large_type, pixiv_id),
            #                          refer = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + pixiv_id)
            # img_m = re.search('<img src="([^"]+)" onclick="\(window.open\(\'\', \'_self\'\)\)\.close\(\)">', img_page)

            # # 解析大图地址
            # if not img_m:
            #     log(pixiv_id, 'Can\'t find fullsize image url')
            #     continue
            # else:
            #     img_url = img_m.group(1)
            
            # 解析图片文件名
            file_name_m = re.search('\d+\_m.(?:gif|jpg|jpeg|png)', img_url)
            if not file_name_m:
                log(pixiv_id, 'Can\'t parse file name')
                continue
            else:
                file_name = file_name_m.group(0)
                debug('Processing: file name: ' + file_name)

            file_path = TEMP_PATH + file_name

            # 保存大图
            debug('Processing: downloading temp image')
            download(file_path, img_url, refer = 'http://www.pixiv.net/member_illust.php?mode=big&illust_id=' + pixiv_id)

            # 上传到七牛
            debug('Processing: uploading to qiniu')
            r = _qiniu.upload(file_name, file_path)
            if r != True:
                log(pixiv_id, r)

            # 删除大图
            debug('Processing: delete temp image')
            os.remove(file_path)
            
            # 写入list
            exist_list[pixiv_id] = int(time.time())
            # 程序不知道什么时候会出错，所以每次有更新就写入到文件吧
            debug('Processing: update exist file')
            exist_json = json.dumps(exist_list)
            exist_file = open(EXIST_FILE, 'w')
            exist_file.write(exist_json)
            exist_file.close()
        
        # 已存在
        else:
            debug('Duplicated: Image alreay exists')
        
        # 生成RSS中的item
        desc  = u'<![CDATA['
        desc += u'<p>画师：' + image['author']
        desc += u' - 上传于：' + image['date']
        desc += u' - 阅览数：' + image['view']
        desc += u' - 总评分：' + image['score']
        desc += u'</p>'
        desc += u'<p><img src="http://pixiv.qiniudn.com/%s"></p>' % file_name
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

        # 暂停一下试试
        debug('Waiting: ---\r\n')
        time.sleep(1)

# 解析排行页面
def ParseRankingPage(html):
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

            if 'r18' in mode:
                LoginToPixiv()

            FetchPixiv(mode)
            GenerateRSS(mode, title)
    else:
        print 'No params specified'