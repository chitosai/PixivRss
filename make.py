# -*- coding: utf-8 -*-

from utility import *

import pchan

# 登录pixiv
def LoginToPixiv():
    debug('Processing: LoginToPixiv')
    data = 'pixiv_id=%s&pass=%s&skip=1&mode=login' % ( CONFIG['PIXIV_USER'], CONFIG['PIXIV_PASS'] )
    return Get( 'http://www.pixiv.net/login.php', data )

# 解析排行页面
def ParseRankingPage(html):
    debug('Processing: ParseHTML')
    doc = J(html)
    sections = doc('section.ranking-item')

    if not len(sections):
        print 'CAN\'T FIND SECTION'
        exit(1)

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

        work_dom = J(section).children('a.work')

        # 检查是否为动态图
        if 'ugoku-illust' in work_dom.children('div').attr('class'):
            item['isAnimated'] = True
        else:
            item['isAnimated'] = False

        # pixiv id
        m = re.search('&illust_id=(\d+)&', work_dom.attr['href'])
        item['id'] = m.group(1)

        # user id
        m = re.search('member\.php\?id=(\d+)&', J(section).children('a.user-container').attr['href'])
        item['uid'] = m.group(1)

        data.append(item)

    return data

# 抓pixiv页面
def FetchPixiv(mode, title):
    debug('Processing: FetchPixiv')
    global DEBUG, PREVIEW_PATH, TEMP_PATH

    # 读取已下载的图片列表
    exist_list = ReadExist(mode)

    # 获取排行
    html = Get('http://www.pixiv.net/ranking.php?lang=zh&mode=' + mode, refer = '')

    # 检查
    if not html:
        return

    # 解析排行
    data = ParseRankingPage(html.decode('utf-8'))
    
    # 检查一下匹配结果
    if not len(data):
        log(0, 'failed to get ranking list info')
        return

    # 开始遍历
    count = 0
    posted_weibo_count = 0

    for image in data:
        count += 1

        # DEBUG模式下最多运行次数
        if DEBUG and count > DEBUG_FETCH_MAX : return

        pixiv_id = image['id']

        debug('Starting: ' + str(count))
        debug('processing: pixiv_id: ' + str(pixiv_id))

        # 检查是否已下载
        if pixiv_id in exist_list:
            debug('Duplicated: Image alreay exists')
            continue

        # 全年龄向的图抓大图并传到微博
        if 'r18' not in mode:
            debug('Processing: NOT R18, will fetch medium size image')

            # 限制每小时最多发N条微博
            if posted_weibo_count > 5:
                return
            else:
                posted_weibo_count += 1

            # 先判断是否为动图，如果是动图只能抓preview
            if image['isAnimated']:
                debug('Processing: is-animated, downloading thumbnail: ' + image['preview'])

                # 下载小尺寸预览图...
                r = download(TEMP_PATH + pixiv_id + '.jpg', image['preview'])
                
                # 三次抓取失败就先跳过
                if not r:
                    log(pixiv_id, 'failed to get thumbnail')
                    continue
                else:
                    file_path = TEMP_PATH + pixiv_id + '.jpg'

            # 非动态图，可以抓中尺寸图
            else:
                # 抓medium尺寸图，成功返回file_path（本地文件名）
                file_path = FetchMediumSizeImage(pixiv_id)
                if not file_path:
                    continue

            # 发到图床，这里如果返回false应该是上传失败了
            # @失败不会返回false，但是会记录log
            sina_url = pchan.upload(pixiv_id, image, file_path, mode, title, count)
            if not sina_url:
                continue

            # 删除大图
            debug('Processing: upload completed, deleting temp image')
            os.remove(file_path)

        # r18图下载小尺寸缩略图到rakuen.thec.me/PixivRss/previews/
        else:
            debug('Processing: R18, downloading thumbnail: ' + image['preview'])

            # 下载小尺寸预览图...
            r = download(PREVIEW_PATH + pixiv_id + '.jpg', image['preview'])
            
            # 三次抓取失败就先跳过
            if not r:
                log(pixiv_id, 'failed to get thumbnail')
                continue
        
        # 写入list
        item_info = {'fetch_time' : int(time.time())}
        if 'r18' not in mode:
            item_info['image'] = sina_url
        else:
            item_info['image'] = 'http://rakuen.thec.me/PixivRss/previews/' + pixiv_id + '.jpg'

        item_info.update(image)
        item_info.pop('preview')
        exist_list[pixiv_id] = item_info
        # 程序不知道什么时候会出错，所以每次有更新就写入到文件吧
        debug('Processing: update exist file')
        UpdateExist(mode, exist_list)

        # 暂停一下试试
        debug('Waiting: ---\r\n')
        time.sleep(1)

# 抓中尺寸图
def FetchMediumSizeImage(pixiv_id):
    debug('Processing: start to get medium size image')
    illust_url = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(pixiv_id)
    html = Get(illust_url)

    # 三次抓取失败
    if not html:
        log(pixiv_id, 'Failed to get ' + illust_url)
        return False

    # 解析图片地址
    doc = J(html)
    img = doc('.works_display img')

    if not len(img):
        log(pixiv_id, 'CAN\'T FIND IMAGE in medium page')
        return False

    img_url = J(img).attr('src')
    debug('Processing: medium size image url: ' + img_url)
    
    # 解析图片文件名
    file_name_m = re.search('[\w\d_]+\.(gif|jpg|jpeg|png)', img_url)
    if not file_name_m:
        log(pixiv_id, 'Can\'t parse file name')
        return False
    else:
        file_name = file_name_m.group(0)
        file_ext = file_name_m.group(1)
        debug('Processing: medium size image file name: ' + file_name)

    file_path = TEMP_PATH + file_name

    # 保存大图
    debug('Processing: downloading medium size image')
    r = download(file_path, img_url, refer = illust_url)

    # 三次抓取失败就先跳过
    if not r:
        log(pixiv_id, 'Failed to download medium size image')
        return False

    # 成功
    return file_path

# 输出rss文件
def GenerateRss(mode, title):
    debug('Processing: GenerateRSS')
    global CONFIG, RSS_PATH

    # 读取exist.json
    exist_list = ReadExist(mode)
    order = sorted(exist_list, key = lambda x: exist_list[x]['fetch_time'], reverse = True)

    for total in CONFIG['totals']:
        # 有时候因为pixiv那边的bug(?)会少几个条目，这时候只能以实际输出的数量为准了
        if total > len(order) : 
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
            image = exist_list[order[i]]
            # 生成RSS中的item
            desc  = u'<p>画师：' + image['author']
            desc += u' - 上传于：' + image['date']
            desc += u' - 阅览数：' + image['view']
            desc += u' - 总评分：' + image['score']
            desc += u'</p>'

            # 插入动图提示
            if image.get('isAnimated', False): desc += u'<p>** 原图为动图 **</p>'

            desc += u'<p><img src="%s"></p>' % image['image']
            # 量子统计的图片
            desc += u'<p><img src="http://img.tongji.linezing.com/3205125/tongji.gif"></p>'

            RSS += u'''<item>
                        <title><![CDATA[%s]]></title>
                        <link>%s</link>
                        <description><![CDATA[%s]]></description>
                        <pubDate>%s</pubDate>
            　　       </item>''' % (
                    image['title'], 
                    'http://www.pixiv.net/member_illust.php?mode=medium&amp;illust_id=' + order[i], 
                    desc,
                    image['date']
                    )

        RSS += u'''</channel></rss>'''

        # 输出到文件
        f = open(RSS_PATH + mode + '-' + str(total) + '.xml', 'w')
        f.write(RSS.encode('utf-8'))
        f.close

if __name__ == '__main__':
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        global MODE

        # 验证分类
        if mode in MODE:
            title = MODE[mode]
        else:
            print 'Unknown Mode'
            exit(1)

        if 'r18' in mode:
            LoginToPixiv()

        FetchPixiv(mode, title)
        GenerateRss(mode, title)

    else:
        print 'No params specified'
