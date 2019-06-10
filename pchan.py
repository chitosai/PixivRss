# -*- coding: utf-8 -*-
from utility import *

# 上传到新浪图床
def upload(pixiv_id, image, file_path, mode, title, count):
    debug('Processing: get WEIBO_NICKNAME')
    # 获取微博昵称
    weibo_nickname = get_weibo_nickname(image['uid'])

    # 记录用户上榜
    if weibo_nickname != '':
        award_log(mode, image['uid'])

    # 排行发微博
    debug('Processing: posting weibo')
    weibo_text = u'#pixiv# %s排行速报：第%s位，来自画师 %s 的 %s。大图请戳 %s %s' \
                    % (title, count, image['author'], image['title'], \
                     'http://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + pixiv_id,
                     weibo_nickname)

    # 补充动态图说明
    if image['isAnimated']:
        weibo_text += u' [原图为动图]'

    sina_url = post(mode, weibo_text, file_path)

    # 渣浪图片地址
    if sina_url == WEIBO_MANUAL_REVIEW:
        log(pixiv_id, 'sina in manual review mode')
        return WEIBO_MANUAL_REVIEW
    elif sina_url == False:
        log(pixiv_id, 'failed to get image url from sina')
        return False

    debug('Processing: post success, image url:' + sina_url)

    return sina_url

# 发微博
def post(mode, message, filepath):
    # 准备返回值，默认为False，上传完毕修改为图片url
    r = False
    
    # upload
    try:
        f = open(filepath, 'rb')
        data = {
            'status': message,
            'rip': '61.133.235.27', # 发微博接口更新后要传发微博者的真实ip，搞个青海的ip凑凑数
            'access_token': WEIBO[mode]['ACCESS_TOKEN']
        }
        files = {
            'pic': f
        }
        res = requests.post('https://api.weibo.com/2/statuses/share.json', data = data, files = files)
        if res.status_code != 200:
            if '20053' in res.text:
                # {"error":"Your Weibo has been successfully released and needs manual review for 3 minutes. Please be patient.\nIf you have any questions, please contact the exclusive customer service, or call 4000960960, more help please enter the customer service center.","error_code":20053,"request":"/2/statuses/share.json"}
                # 微博新增了这样一种情况，本身是作为失败返回的，并且也确实拿不到大图地址，但是微博却成功发出去了
                # 所以这里返回个特殊字符串，通知最外层的make直接放原始小图url
                r = WEIBO_MANUAL_REVIEW
            else:
                log('-70421195', '')
                log(filepath, res.text)
        else:
            r = res.json()['original_pic']

    except Exception, err:
        log('-70421196', '')
        log(filepath, err)
    finally:
        f.close()
        return r

# 根据pixiv_user_id查找微博昵称
def get_weibo_nickname(pixiv_uid):
    pixiv_uid = str(pixiv_uid)
    # 首先从数据库中查找
    r = get_weibo_uid_by_(pixiv_uid)

    # 没有
    if not len(r):
        pixiv_user_page = Get('http://www.pixiv.net/member.php?id=' + pixiv_uid)

        if not pixiv_user_page:
            debug('Error: failed to open pixiv member profile page')
            return ''

        # 先剔除掉pixiv自己的weibo链接
        pixiv_user_page = pixiv_user_page.replace('http://weibo.com/2230227495', '')
        # download('a.html', 'http://www.pixiv.net/member.php?id=' + pixiv_uid)
        # 直接从整个网页代码里匹配
        m = re.search('http://(?:www\.)?weibo\.com/(.+?)<', pixiv_user_page, re.S)
        if m:
            weibo_uid = m.group(1)
            # 保存
            insert_id_map(pixiv_uid, weibo_uid)
        else:
            debug('Processing: no WEIBO_URL')
            return ''
    # 有
    else:
        weibo_uid = r[0]['weibo_uid']

    # 去weibo查昵称
    weibo_user_page = Get('http://weibo.com/' + weibo_uid)

    if not weibo_user_page:
        log(pixiv_uid, 'Error: failed to open weibo profile page')
        return '';

    m = re.search(u'Hi， 我是(.+?)！赶快注册微博粉我吧', weibo_user_page)
    if m:
        return u' @%s' % m.group(1)
    else:
        # pixiv_id: 3892088 && weibo.com/u/1764793942 的情况，不需要登录就能浏览的微博账号
        m = re.search(u'<title>(.+?)的微博_微博', weibo_user_page)
        if m:
            return u' @%s' % m.group(1)
        else:
            log(pixiv_uid, 'can\'t find WEIBO_NICKNAME - weibo: ' + 'http://weibo.com/' + weibo_uid)
            return ''

# 根据pixiv_user_id从数据库查找微博昵称
def get_weibo_uid_by_(pixiv_uid):
    db = DB()
    sql = 'SELECT `weibo_uid` FROM `pixiv_weibo_id_map` WHERE `pixiv_uid` = %s' % pixiv_uid
    return db.Query(sql)

# 插入pixiv_user_id到weibo_user_id的映射
def insert_id_map(pixiv_uid, weibo_uid):
    db = DB()
    sql = 'INSERT INTO `pixiv_weibo_id_map` ( `pixiv_uid`, `weibo_uid` ) VALUES ( %s, %s )'
    return db.Run(sql, (pixiv_uid, weibo_uid))

# 记录用户上榜
def award_log(mode, pixiv_uid):
    global MODE_ID
    type = MODE_ID[mode]

    db = DB()
    sql = 'INSERT INTO `award_log` ( `type`, `uid` ) VALUES ( %s, %s )'
    return db.Run(sql, (type, pixiv_uid))
