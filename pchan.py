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
def get_weibo_nickname(uid):
    # 首先从weibo.json中查找
    id_map = LoadMap()
    uid = str(uid)

    # 有
    if uid in id_map:
        weibo_id = id_map[uid]

    # 没有
    else:
        pixiv_user_page = Get('http://www.pixiv.net/member.php?id=' + uid)
        # 先剔除掉pixiv自己的weibo链接
        pixiv_user_page = pixiv_user_page.replace('http://weibo.com/2230227495', '')
        # 直接从整个网页代码里匹配
        m = re.search('http://weibo\.com/(.+?)<', pixiv_user_page, re.S)
        if m:
            weibo_id = m.group(1)
        else:
            debug('Processing: can\'t find WEIBO_URL')
            return ''

    # 去weibo查昵称
    weibo_user_page = Get('http://weibo.com/' + weibo_id)
    m = re.search('Hi， 我是(.+?)！赶快注册微博粉我吧', weibo_user_page)
    if m:
        return u' @%s' % m.group(1).decode('utf-8')
    else:
        log('uid:' + uid, 'can\'t find WEIBO_NICKNAME - weibo: ' + 'http://weibo.com/' + weibo_id)
        return ''

