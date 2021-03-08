# -*- coding: utf-8 -*-
from utility import *
from make import FetchPixiv

db = DB()

def post_weibo(pixiv_id, image, file_path):
    debug('Processing: get WEIBO_NICKNAME')
    # 获取微博昵称
    weibo_nickname = get_weibo_nickname(image['uid'])

    # 排行发微博
    debug('Posting weibo')
    weibo_text = u'#pixiv# 每日排行速报：第%s位，来自画师 %s 的 %s。Pid: %s。 %s' \
                    % (image['ranking'], image['author'], image['title'], str(pixiv_id),
                     weibo_nickname)

    sina_url = do_post_weibo(weibo_text, file_path)
    # 通过是否获取到了渣浪图片地址来判断是否上传成功
    if not sina_url:
        log(pixiv_id, 'Failed to get image url from sina')
        return False
    # 成功
    debug('Post success, image url: ' + sina_url)
    # 记录一下
    insert_post_weibo_history(pixiv_id)
    # 记录用户上榜
    if weibo_nickname != '':
        award_log(image['uid'])


def do_post_weibo(message, filepath):
    # 准备返回值，默认为False，上传完毕修改为图片url
    r = False
    # upload
    try:
        f = open(filepath, 'rb')
        data = {
            'status': message,
            'rip': '61.133.235.27', # 发微博接口更新后要传发微博者的真实ip，搞个青海的ip凑凑数
            'access_token': WEIBO['prod']['ACCESS_TOKEN'] if not DEBUG else WEIBO['test']['ACCESS_TOKEN']
        }
        files = {
            'pic': f
        }
        res = requests.post('https://api.weibo.com/2/statuses/share.json', data = data, files = files)
        if res.status_code != 200:
            log('Weibo responsed with code != 200, code: %s' % res.status_code)
            if '20053' in res.text:
                # {"error":"Your Weibo has been successfully released and needs manual review for 3 minutes. Please be patient.\nIf you have any questions, please contact the exclusive customer service, or call 4000960960, more help please enter the customer service center.","error_code":20053,"request":"/2/statuses/share.json"}
                # 微博新增了这样一种情况，本身是作为失败返回的，并且也确实拿不到大图地址，但是微博却成功发出去了，所以也算是成功吧
                r = 'WEIBO_MANUAL_REVIEW'
            else:
                log(filepath, res.text)
        else:
            r = res.json()['original_pic']
    except Exception as err:
        log('Weibo post failed')
        log(filepath, err)
    finally:
        f.close()
        os.remove(filepath)
        return r


# 下载原图
def download_image(illust):
    debug('Download image')
    filename = '%s.jpg' % illust['id']
    filepath = os.path.join(TEMP_PATH, filename)
    # 突然开始出现original字段为空的情况，总之处理一下吧 id=85217944
    picpath = illust['images']['original'] or illust['images']['large'] or illust['images']['medium']
    if not picpath:
        log('Image url not found!')
        log(json.dumps(illust))
        raise RuntimeError()
    aapi.download(picpath, path = TEMP_PATH, name = filename)
    debug('Download finished, saved to %s' % filepath)
    return filepath


# 根据pixiv_user_id查找微博昵称
def get_weibo_nickname(pixiv_uid):
    pixiv_uid = str(pixiv_uid)
    SetLogLevel(+1)
    # 首先从数据库中查找
    r = get_weibo_uid_by_(pixiv_uid)

    # 没有
    if not len(r):
        user_profile = aapi.user_detail(pixiv_uid)
        if not user_profile or 'error' in user_profile:
            log('Failed to get pixiv user profile')
            SetLogLevel(-1)
            return ''
        # 从签名里匹配
        signature = user_profile.user.comment
        m = re.search('https://(?:www\.)?weibo\.com/(.+?)[\r\n\s]', signature, re.S)
        if m:
            weibo_uid = m.group(1)
            # 保存
            insert_id_map(pixiv_uid, weibo_uid)
        else:
            debug('Weibo not found')
            SetLogLevel(-1)
            return ''
    # 有
    else:
        weibo_uid = r[0]['weibo_uid']
    
    
    debug('Weibo found: %s' % weibo_uid)
    SetLogLevel(-1)
    # 去weibo查昵称
    weibo_user_page = Get('https://weibo.com/' + weibo_uid)

    if not weibo_user_page:
        log(pixiv_uid, 'Error: failed to open weibo profile page')
        return ''

    m = re.search(u'Hi， 我是(.+?)！赶快注册微博粉我吧', weibo_user_page)
    if m:
        return u' @%s' % m.group(1)
    else:
        # pixiv_id: 3892088 && weibo.com/u/1764793942 的情况，不需要登录就能浏览的微博账号
        m = re.search(u'<title>(.+?)的微博_微博', weibo_user_page)
        if m:
            return u' @%s' % m.group(1)
        else:
            log(pixiv_uid, 'can\'t find WEIBO_NICKNAME - weibo: ' + weibo_uid)
            return ''


# 根据pixiv_user_id从数据库查找微博昵称
def get_weibo_uid_by_(pixiv_uid):
    sql = 'SELECT `weibo_uid` FROM `pixiv_weibo_id_map` WHERE `pixiv_uid` = %s'
    return db.Query(sql, (pixiv_id,))


# 插入pixiv_user_id到weibo_user_id的映射
def insert_id_map(pixiv_uid, weibo_uid):
    sql = 'INSERT INTO `pixiv_weibo_id_map` ( `pixiv_uid`, `weibo_uid` ) VALUES ( %s, %s )'
    return db.Run(sql, (pixiv_uid, weibo_uid))


# 记录用户上榜
def award_log(pixiv_uid):
    # type字段原本是用来表示上了哪个排行的，但是由于现在只剩下日榜了，所以就直接硬编码为1了
    # 数据库里原本的记录就暂且不处理了，反正到现在5年了也只有15000行
    sql = 'INSERT INTO `award_log` ( `type`, `uid` ) VALUES ( %s, %s )'
    return db.Run(sql, (1, pixiv_uid))


# 检查有没有发过
def check_if_posted(pixiv_id):
    sql = 'SELECT `pixiv_id` FROM `weibo_post_history` WHERE `pixiv_id` = %s'
    return db.Query(sql, (pixiv_id,))


# 记录微博已发
def insert_post_weibo_history(pixiv_id):
    sql = 'INSERT INTO `weibo_post_history` ( `pixiv_id` ) VALUES ( %s )'
    return db.Run(sql, (pixiv_id,))

if __name__ == '__main__':
    global aapi
    # 现在只有daily一个微博了，就不要多余的判断了
    aapi = ExtendedPixivPy()
    data = FetchPixiv(aapi, 'daily')

    # 开始遍历
    count   = 0 # 遍历了几次，用这个变量来确保每小时不会发布超过WEIBO_PER_HOUR
    debug('Begin to iter daily ranking list')
    for illust in data:
        pixiv_id = illust['id']
        debug('* Itering no.%s' % illust['ranking'])
        SetLogLevel(+2)
        # 检查有没有发过
        r = check_if_posted(pixiv_id)
        if r and len(r):
            debug('Posted, will skip')
            SetLogLevel(-2)
            continue
        # 下载medium尺寸图到本地
        filepath = download_image(illust)
        # 上传
        post_weibo(pixiv_id, illust, filepath)
        count += 1
        if count >= WEIBO_PER_HOUR or ( DEBUG and count >= WEIBO_PER_HOUR_DEBUG ):
            SetLogLevel(-2)
            debug('Reached WEIBO_PER_HOUR: %s' % (WEIBO_PER_HOUR if not DEBUG else WEIBO_PER_HOUR_DEBUG))
            break
        SetLogLevel(-2)
        # +1s
        time.sleep(1)
    debug('All job done, processed %s item(s)' % count)