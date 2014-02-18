# -*- coding: utf-8 -*-
from utility import *
from weibo import *

# 发微博
def post(mode, message, filepath):
    # init
    c = APIClient(WEIBO[mode]['APP_KEY'], WEIBO[mode]['APP_SECRET'])
    c.set_access_token(WEIBO[mode]['ACCESS_TOKEN'], 157679999)
    
    # upload
    try:
        f = open(filepath, 'rb')

        r = c.statuses.upload.post(status = message, pic = f)
        if 'error' in r:
            log(filepath, r)
            return False
        else:
            return r['original_pic']

    except Exception, err:
        log(filepath, err)
        return False
        
    finally:
        f.close()

# 根据pixiv_user_id查找微博昵称
def get_weibo_nickname(pixiv_uid):
    pixiv_uid = str(pixiv_uid)
    # 首先从数据库中查找
    r = get_weibo_uid_by_(pixiv_uid)

    # 没有
    if not len(r):
        pixiv_user_page = Get('http://www.pixiv.net/member.php?id=' + pixiv_uid)
        # 先剔除掉pixiv自己的weibo链接
        pixiv_user_page = pixiv_user_page.replace('http://weibo.com/2230227495', '')
        download('a.html', 'http://www.pixiv.net/member.php?id=' + pixiv_uid)
        # 直接从整个网页代码里匹配
        m = re.search('http://(?:www\.)?weibo\.com/(.+?)<', pixiv_user_page, re.S)
        if m:
            weibo_uid = m.group(1)
            # 保存
            insert_id_map(pixiv_uid, weibo_uid)
        else:
            debug('Processing: can\'t find WEIBO_URL')
            return ''
    # 有
    else:
        weibo_uid = r[0]['weibo_uid']

    # 去weibo查昵称
    weibo_user_page = Get('http://weibo.com/' + weibo_uid)
    m = re.search('Hi， 我是(.+?)！赶快注册微博粉我吧', weibo_user_page)
    if m:
        return u' @%s' % m.group(1).decode('utf-8')
    else:
        log('pixiv_uid:' + pixiv_uid, 'can\'t find WEIBO_NICKNAME - weibo: ' + 'http://weibo.com/' + weibo_uid)
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