# -*- coding: utf-8 -*-

from utility import *

import pchan

MAX_WEIBO_PER_HOUR = 6

# 抓pixiv页面
def FetchPixiv(mode, title):
    debug('[Processing] get ranking page')
    global DEBUG, PREVIEW_PATH, TEMP_PATH

    # 获取排行
    html = Get('http://www.pixiv.net/ranking.php?lang=zh&mode=' + mode, refer = '')

    # 检查
    if not html:
        log(-1, 'rank page is empty, what\'s wrong?')
        return

    # 解析排行
    data = ParseRankingPage(html)
    
    # 检查一下匹配结果
    if not len(data):
        log(-1, 'parse ranking page failed')
        return

    # 读取已下载的图片列表
    exist_list = ReadExist(mode)

    # 开始遍历
    count = 0
    count_real = 0
    posted_weibo_count = 0

    debug('[Processing] start to fetch images from ranking list')
    for image in data:
        count += 1

        pixiv_id = image['id']

        debug('[Processing] count: ' + str(count))
        debug('[processing] pixiv_id: ' + str(pixiv_id))

        # 检查是否已下载
        if pixiv_id in exist_list:
            exist_list[pixiv_id]['ranking'] = image['ranking']
            UpdateExist(mode, exist_list)
            debug('[Skip] duplicated: Image alreay exists')
            continue

        # DEBUG模式下最多运行次数
        count_real += 1
        if DEBUG and count_real > DEBUG_FETCH_MAX : return

        # 根据config中是否配置了weibo认证来决定是否发微博
        if mode in WEIBO:
            debug('[Processing] daily, will fetch medium size image')

            # 限制每小时最多发N条微博
            if posted_weibo_count >= MAX_WEIBO_PER_HOUR:
                return
            else:
                posted_weibo_count += 1

            # 先判断是否为动图，如果是动图只能抓preview
            if image['isAnimated']:
                debug('[Processing] is-animated, downloading thumbnail: ' + image['preview'])

                # 下载小尺寸预览图...
                r = download(os.path.join(TEMP_PATH, pixiv_id + '.jpg'), image['preview'])
                
                # 三次抓取失败就先跳过
                if not r:
                    log(pixiv_id, 'failed to get thumbnail')
                    continue
                else:
                    file_path = os.path.join(TEMP_PATH, pixiv_id + '.jpg')

            # 非动态图，可以抓中尺寸图
            else:
                # 抓medium尺寸图，成功返回file_path（本地文件名）
                file_path = FetchMediumSizeImage(pixiv_id)
                if not file_path:
                    continue

            # 发到图床，这里如果返回false应该是上传失败了
            # @失败不会返回false，但是会记录log
            sina_url = pchan.upload(pixiv_id, image, file_path, mode, title, count)
            if sina_url == WEIBO_MANUAL_REVIEW:
                # 遇到渣浪处在人工审核模式，无法通过post接口的返回值得到大图地址，则改为下载小尺寸预览图到本地
                r = download(os.path.join(PREVIEW_PATH, pixiv_id + '.jpg'), image['preview'])
                image['image'] = 'http://rakuen.thec.me/PixivRss/previews/' + pixiv_id + '.jpg'
            if not sina_url:
                continue
            else:
                image['image'] = sina_url
                # 删除大图
                debug('[Processing] upload completed, deleting temp image')
                os.remove(file_path)


        # 其他排行只下载小尺寸缩略图到rakuen.thec.me/PixivRss/previews/
        else:
            debug('[Processing] not daily, downloading thumbnail: ' + image['preview'])

            # 下载小尺寸预览图...
            r = download(os.path.join(PREVIEW_PATH, pixiv_id + '.jpg'), image['preview'])
            
            # 三次抓取失败就先跳过
            if not r:
                log(pixiv_id, 'failed to get thumbnail')
                continue
            else:
                image['image'] = 'http://rakuen.thec.me/PixivRss/previews/' + pixiv_id + '.jpg'
        
        # 记录抓取时间
        image['fetch_time'] = int(time.time())

        image.pop('preview')
        exist_list[pixiv_id] = image
        # 程序不知道什么时候会出错，所以每次有更新就写入到文件吧
        debug('[Processing] update exist file')
        UpdateExist(mode, exist_list)

        # 暂停一下试试
        debug('[Waiting] +1s\r\n')
        time.sleep(1)

# 抓中尺寸图
def FetchMediumSizeImage(pixiv_id):
    debug('[Processing] start to get medium size image')
    illust_url = 'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(pixiv_id)
    html = Get(illust_url)

    # 抓取失败
    if not html:
        log(pixiv_id, 'Failed to get ' + illust_url)
        return False

    # 解析图片地址
    m = re.search('"original":"([^"]+?)"', html)
    if not m:
        log(pixiv_id, 'Can\'t find image element in medium page')
        return False
    else:
        img_url = m.group(1).replace('\/', '/')

    debug('[Processing] medium size image url: ' + img_url)
    
    # 解析图片文件名
    file_name_m = re.search('[\w\d_]+\.(gif|jpg|jpeg|png)', img_url)
    if not file_name_m:
        log(pixiv_id, 'Can\'t parse file name of medium size image')
        return False
    else:
        file_name = file_name_m.group(0)
        file_ext = file_name_m.group(1)
        debug('[Processing] medium size image file name: ' + file_name)

    file_path = os.path.join(TEMP_PATH, file_name)

    # 保存大图
    debug('[Processing] downloading medium size image')
    r = download(file_path, img_url, refer = illust_url)

    # 三次抓取失败就先跳过
    if not r:
        log(pixiv_id, 'Failed to download medium size image')
        return False

    # 成功
    return file_path

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
            log(json.dumps(r.error))
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
            title = MODE[mode]
        else:
            print 'Unknown Mode'
            exit(1)

        CheckTokenStatus()

        FetchPixiv(mode, title)
        GenerateRss(mode, title)

    else:
        print 'No params specified'
