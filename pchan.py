# -*- coding: utf-8 -*-
import json, os, re, time

from PIL import Image
from config import BLACKLIST, TEMP_PATH, WEIBO_PER_HOUR, WEIBO_PER_HOUR_DEBUG
from env import DEBUG
from pixiv.client import PixivClient
from utility import get
from utils.db import db
from utils.log import debug, log, set_log_level
from weibo import Weibo

weibo = Weibo()


def post_weibo(pixiv_id, image, file_path):
    debug('Processing: get WEIBO_NICKNAME')

    # 从pixiv获取作品标签
    tags = get_first_three_tags(image['tags'])

    # 获取微博昵称
    weibo_nickname = get_weibo_nickname(image['uid'])

    # 先传图
    debug('Uploading image to Weibo')
    pic_id = do_upload_image_to_weibo(file_path)
    if not pic_id:
        return False

    # 排行发微博
    debug('Posting weibo')
    weibo_text = u'#P站每日排行速报# 第%s位，来自画师 %s 的 %s。Pid: %s。%s %s' \
                    % (image['ranking'], image['author'], image['title'], str(pixiv_id), tags,
                     weibo_nickname)

    is_posted = do_post_weibo(pixiv_id, weibo_text, pic_id)
    if not is_posted:
        log(pixiv_id, 'Failed to post weibo')
        return False

    # 成功
    debug('Post success')
    # 记录一下
    db.insert_post_weibo_history(pixiv_id)
    # 记录用户上榜
    if weibo_nickname != '':
        db.award_log(image['uid'])


def get_first_three_tags(_tags):
    # 获取每个作品的前3个tag，拼成#xxx的字符串返回
    tags = _tags[0:3]
    tags = map(lambda x : (u'#%s#' % x['name']), tags)
    return ' '.join(tags)


def do_upload_image_to_weibo(filepath):
    global weibo
    filename = os.path.basename(filepath)
    pixiv_id = filename.split('.')[0]
    extension = filename.split('.')[1]
    # 准备返回值，默认为False，上传完毕修改为图片url
    r = False
    # upload
    try:
        f = open(filepath, 'rb')
        data = {
            'type': 'json',
            '_spr': 'screen:1920x1080',
            'st': weibo.cookies['XSRF-TOKEN']
        }
        # 这里文件必须要用[()]的形式写，这样封装出来的form才是multipart，发出的请求会带上
        # 'Content-Type': 'multipart/form-data; boundary=xxxxxx' 的头
        files = [
            ('pic', ('1.' + extension, f, 'image/' + extension))
        ]
        weibo.s.headers['x-xsrf-token'] = weibo.cookies['XSRF-TOKEN']
        weibo.s.headers['referer'] = 'https://m.weibo.cn/compose/'
        r2 = weibo.s.post('https://m.weibo.cn/api/statuses/uploadPic', data = data, files = files, timeout = 60)
        debug('upload image to weibo returns: ')
        debug(r2.text)
        data = r2.json()
        if 'pic_id' in data:
            r = data['pic_id']
        else:
            log(pixiv_id, 'post weibo failed')
            log(pixiv_id, r2.text)
    except Exception as err:
        log(pixiv_id, 'Weibo post failed with error')
        log(pixiv_id, err)
    finally:
        f.close()
        os.remove(filepath)
        return r


def do_post_weibo(pixiv_id, message, pic_id):
    global weibo
    try:
        data = {
            'content': message,
            'visible': (1 if DEBUG else 0),                       # 0 = 全部可见，1 = 仅自己可见，10 = 粉丝
            '_spr': 'screen:1920x1080',
            'st': weibo.cookies['XSRF-TOKEN'],
            'picId': pic_id                     # 这是提前上传的图片的id
        }
        weibo.s.headers['x-xsrf-token'] = weibo.cookies['XSRF-TOKEN']
        weibo.s.headers['referer'] = 'https://m.weibo.cn/compose/'
        r2 = weibo.s.post('https://m.weibo.cn/api/statuses/update', data = data, timeout = 60)
        debug('post weibo returns:')
        debug(r2.text)
        data = r2.json()
        if data['ok'] == 1:
            return True
        else:
            log(pixiv_id, 'post weibo failed')
            set_log_level(+2)
            log(pixiv_id, 'Payload sent:')
            log(pixiv_id, json.dumps(data))
            log(pixiv_id, 'Return:')
            log(pixiv_id, r2.text)
            set_log_level(-2)
            return False
    except Exception as err:
        log(pixiv_id, 'Weibo post failed with error')
        log(pixiv_id, err)
        return False


# 下载原图
def download_image(illust):
    debug('Download image')
    filename = '%s.jpg' % illust['id']
    filepath = os.path.join(TEMP_PATH, filename)
    # 原本似乎是抓original尺寸的，但是还是不要发原图了吧，现在自己模拟m.weibo的请求怕一张2m/3m/4m的图太大了容易出问题
    # 还是试试看original先吧。。可以的话还是传清晰的图好
    picpath = illust['images']['original'] or illust['images']['large'] or illust['images']['medium']
    if not picpath:
        log('Image url not found!')
        log(json.dumps(illust))
        raise RuntimeError()
    aapi.download(picpath, path = TEMP_PATH, name = filename)
    debug('Download finished, saved to %s' % filepath)
    # 自己拯救一下试试，检查文件尺寸，如果超过2M就用Pillow压缩一遍
    original_size = os.path.getsize(filepath)
    if original_size > 2000000:
        set_log_level(+2)
        debug('%s: File size %s, will run a compress' % (illust['id'], original_size))
        image = Image.open(filepath)
        # 直接覆盖原图，抛弃Alpha通道，优化文件尺寸，质量85
        image = image.convert('RGB')
        image.save(filepath, 'JPEG', optimize = True, quality = 85)
        debug('%s: Compressed size: %s' % (illust['id'], os.path.getsize(filepath)))
        set_log_level(-2)
    return filepath


# 根据pixiv_user_id查找微博昵称
def get_weibo_nickname(pixiv_uid):
    pixiv_uid = str(pixiv_uid)
    set_log_level(+1)
    # 首先从数据库中查找
    r = db.get_weibo_uid_by(pixiv_uid)

    # 没有
    if not len(r):
        user_profile = aapi.user_detail(pixiv_uid)
        if not user_profile or 'error' in user_profile:
            log(pixiv_uid, 'Failed to get pixiv user profile')
            set_log_level(-1)
            return ''
        # 从签名里匹配
        signature = user_profile.user.comment
        m = re.search('https://(?:www\.)?weibo\.com/(.+?)[\r\n\s]', signature, re.S)
        if m:
            weibo_uid = m.group(1)
            # 保存
            db.insert_id_map(pixiv_uid, weibo_uid)
        else:
            debug('Weibo not found')
            set_log_level(-1)
            return ''
    # 有
    else:
        weibo_uid = r[0]['weibo_uid']


    debug('Weibo found: %s' % weibo_uid)
    set_log_level(-1)
    # 去weibo查昵称
    weibo_user_page = get('https://weibo.com/' + weibo_uid)

    if not weibo_user_page:
        log(pixiv_uid, 'Error: failed to open weibo profile page')
        return ''

    m = re.search(u'Hi， 我是(.+?)！赶快注册微博粉我吧', weibo_user_page)
    if not m:
        # pixiv_id: 3892088 && weibo.com/u/1764793942 的情况，不需要登录就能浏览的微博账号
        m = re.search(u'<title>(.+?)的微博_微博', weibo_user_page)

    if m:
        return u' @%s' % m.group(1)
    else:
        log(pixiv_uid, 'can\'t find WEIBO_NICKNAME - weibo: ' + weibo_uid)
        return ''


if __name__ == '__main__':
    global aapi
    # 现在只有daily一个微博了，就不要多余的判断了
    aapi = PixivClient()
    data = aapi.fetch('daily')

    # 开始遍历
    count = 0 # 遍历了几次，用这个变量来确保每小时不会发布超过WEIBO_PER_HOUR
    debug('Begin to iter daily ranking list')
    for illust in data:
        pixiv_id = illust['id']
        debug('* Itering no.%s' % illust['ranking'])
        set_log_level(+2)
        # 如果作者在黑名单里直接跳过
        if illust['uid'] in BLACKLIST:
            debug('Author %s in Blacklist, will skip' % illust['uid'])
            continue
        # 检查有没有发过
        r = db.check_if_posted(pixiv_id)
        if r and len(r):
            debug('Posted, will skip')
            set_log_level(-2)
            continue
        # 下载medium尺寸图到本地
        filepath = download_image(illust)
        # 上传
        post_weibo(pixiv_id, illust, filepath)
        count += 1
        if count >= WEIBO_PER_HOUR or ( DEBUG and count >= WEIBO_PER_HOUR_DEBUG ):
            set_log_level(-2)
            debug('Reached WEIBO_PER_HOUR: %s' % (WEIBO_PER_HOUR if not DEBUG else WEIBO_PER_HOUR_DEBUG))
            break
        set_log_level(-2)
        # +10s，现在是自己模拟请求发图了，为了安全还是把间隔拉大一点
        time.sleep(10)
    debug('All job done, processed %s item(s)' % count)
