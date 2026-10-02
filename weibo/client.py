import json
import re
import requests

from config import WEIBO_COOKIE_FILE
from utils import db
from utils.log import _write_log, debug, log, set_log_level


class WeiboClient:
    def __init__(self):
        # 读取本地 cookie
        with open(WEIBO_COOKIE_FILE, 'r', encoding = 'utf-8') as file:
            self.cookies = json.load(file)

        self.session = requests.Session()
        self.session.cookies.update(self.cookies)

        # 拼接请求头，xsrf-token 需要从 cookie 中获取
        self.session.headers.update({
            'accept-language': 'zh-CN,zh;q=0.8', # 防止海外服务器访问 weibo 变英文版
            'mweibo-pwa': "1",
            'origin': 'https://m.weibo.cn',
            'referer': 'https://m.weibo.cn/sw.js',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.1.128 Safari/537.36',
            'x-xsrf-token': self.cookies['XSRF-TOKEN']
        })

    def save_cookies(self):
        self.cookies = self.session.cookies.get_dict()
        # 本地字典不保留域信息，统一回填以免新旧同名 cookie 重复发送
        self.session.cookies.clear()
        self.session.cookies.update(self.cookies)
        # 立即更新 session 中的 xsrf-token，这样如果当前 session 还需要继续发送请求不会过期
        self.session.headers['x-xsrf-token'] = self.cookies['XSRF-TOKEN']

        # 保存更新的 cookie
        try:
            with open(WEIBO_COOKIE_FILE, 'w', encoding = 'utf-8') as file:
                json.dump(self.cookies, file)
        except Exception as err:
            log('Weibo cookie write failed: %s' % type(err).__name__)
            raise

    def heartbeat(self):
        try:
            response = self.session.get('https://m.weibo.cn/api/config', timeout = 10)
            response.raise_for_status()

            data = response.json()
            if data['ok'] != 1 or data['data']['login'] is not True:
                log('Weibo heartbeat request failed. [[[Request details saved to error log for debugging]]].')
                _write_log(
                    'Weibo heartbeat',
                    f'--- Request Headers:\n{response.request.headers}\n'
                    f'--- Response:\n{response.text}\n'
                    f'--- Return Cookie:\n{response.cookies}'
                )
                # 返回值不正确时提前返回，避免把错误的 cookie 写入本地
                return False
        except Exception as err:
            log('Weibo heartbeat request failed: %s' % type(err).__name__)
            raise

        self.save_cookies()
        debug('Weibo heartbeat refresh succeeded')
        return True

    def get_user_info(self, weibo_uid):
        weibo_uid = str(weibo_uid)
        if weibo_uid.startswith('u/'):
            weibo_uid = weibo_uid[2:]

        try:
            response = self.session.get(
                'https://m.weibo.cn/api/container/getIndex',
                params = {'type': 'uid', 'value': weibo_uid},
                timeout = 10,
            )
            response.raise_for_status()
            data = response.json()
            if data['ok'] != 1:
                log(weibo_uid, 'Weibo user profile request failed')
                return None
            user_info = data['data']['userInfo']
        except Exception as err:
            log(weibo_uid, f'Weibo user profile request failed: {type(err).__name__}')
            return None

        self.save_cookies()
        return user_info

    
    # 根据 pixiv_user_id 查找微博昵称
    def get_weibo_nickname(self, pixiv_uid):
        pixiv_uid = str(pixiv_uid)
        set_log_level(+1)

        # 先从数据库中查找
        mappings = db.get_weibo_uid_by(pixiv_uid)

        # 没有
        if not mappings:
            user_profile = self.user_detail(pixiv_uid)
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
                ('pic', ('1.' + extension, f, mimetypes.guess_type(filename)[0] or 'application/octet-stream'))
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
    
    def post(self, pixiv_id, image, file_path):
        # 获取每个作品的前3个tag，拼成 #xxx 的字符串
        tags_string = ' '.join(f"#{tag['name']}#" for tag in image['tags'][:3])

        # 获取微博昵称
        debug('Processing: get WEIBO_NICKNAME')
        weibo_nickname = self.get_weibo_nickname(image['uid'])

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


weibo_client = WeiboClient()