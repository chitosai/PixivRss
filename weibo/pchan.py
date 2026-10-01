import re

from pixiv.client import pixiv_client
from utils.db import db
from utils.log import debug, log, set_log_level
from weibo.client import weibo_client


# 根据 pixiv_user_id 查找微博昵称
def get_weibo_nickname(pixiv_uid):
    pixiv_uid = str(pixiv_uid)
    set_log_level(+1)

    # 先从数据库中查找
    mappings = db.get_weibo_uid_by(pixiv_uid)

    # 没有
    if not mappings:
        user_profile = pixiv_client.user_detail(pixiv_uid)
        if not user_profile or 'error' in user_profile:
            log(pixiv_uid, 'Failed to get pixiv user profile')
            set_log_level(-1)
            return ''
        
        # 从签名里匹配
        signature = user_profile.user.comment
        match = re.search(r'https://(?:www\.)?weibo\.com/(.+?)[\r\n\s]', signature, re.S)
        if match:
            weibo_uid = match.group(1)
            # 保存
            db.insert_id_map(pixiv_uid, weibo_uid)
        else:
            debug('Weibo not found')
            set_log_level(-1)
            return ''
    # 有
    else:
        weibo_uid = mappings[0]['weibo_uid']

    debug(f'Weibo found: {weibo_uid}')
    set_log_level(-1)
    
    # 去 m.weibo.cn，获取用户信息
    user_info = weibo_client.get_user_info(weibo_uid)

    if not user_info:
        log(pixiv_uid, 'Error: failed to open weibo profile page')
        return ''

    nickname = user_info.get('screen_name')
    if nickname:
        return f' @{nickname}'

    log(pixiv_uid, f"can't find WEIBO_NICKNAME - weibo: {weibo_uid}")
    return ''


def post(self, pixiv_id, image, file_path):
    # 获取每个作品的前3个tag，拼成 #xxx 的字符串
    tags_string = ' '.join(f"#{tag['name']}#" for tag in image['tags'][:3])

    # 获取微博昵称
    debug('Processing: get WEIBO_NICKNAME')
    weibo_nickname = get_weibo_nickname(image['uid'])

    # 先传图
    debug('Uploading image to Weibo')
    pic_id = do_upload_image_to_weibo(file_path)
    if not pic_id:
        return False

    # 排行发微博
    debug('Posting weibo')
    weibo_text = u'#P站每日排行速报# 第%s位，来自画师 %s 的 %s。Pid: %s。%s %s' \
                    % (image['ranking'], image['author'], image['title'], str(pixiv_id), tags_string,
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