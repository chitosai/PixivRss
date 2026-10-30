import json, mimetypes, re, time
import requests

from config import DEBUG, WEIBO_SSO_COOKIES_FILE, WEIBO_XSRF_COOKIES_FILE
from pathlib import Path
from utils.http import configure_retries
from utils.log import _write_log, debug, log, set_log_level
from weibo.guest import weibo_guest_client


class WeiboClient:
    def __init__(self):
        # 读取本地 cookie
        with open(WEIBO_XSRF_COOKIES_FILE, 'r', encoding = 'utf-8') as file:
            self.cookies = json.load(file)

        self.session = requests.Session()
        configure_retries(self.session)
        self.session.cookies.update(self.cookies)

        # 拼接请求头，xsrf-token 需要从 cookie 中获取
        self.session.headers.update({
            'accept-language': 'zh-CN,zh;q=0.8', # 防止海外服务器访问 weibo 变英文版
            'mweibo-pwa': '1',
            'origin': 'https://m.weibo.cn',
            'referer': 'https://m.weibo.cn/sw.js',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.1.128 Safari/537.36',
            'x-xsrf-token': self.cookies['XSRF-TOKEN']
        })

    def update_cookies(self, write_file = False):
        self.cookies = self.session.cookies.get_dict()
        # 本地字典不保留域信息，统一回填以免新旧同名 cookie 重复发送
        self.session.cookies.clear()
        self.session.cookies.update(self.cookies)
        # 立即更新 session 中的 xsrf-token，这样如果当前 session 还需要继续发送请求不会过期
        self.session.headers['x-xsrf-token'] = self.cookies['XSRF-TOKEN']

        # 默认只同步内存，heartbeat 才写回文件
        if not write_file:
            return

        # 保存更新的 cookie
        try:
            with open(WEIBO_XSRF_COOKIES_FILE, 'w', encoding = 'utf-8') as file:
                json.dump(self.cookies, file)
        except Exception as err:
            log('Weibo cookie write failed: %s' % type(err).__name__)
            raise

    # 刷新 .weibo.cn 域下的短期 XSRF-TOKEN，它依赖于 refresh_login 获取到的新浪 SSO cookie
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

        self.update_cookies(write_file = True)
        debug('Weibo heartbeat refresh succeeded')
        return True

    # 刷新新浪登录中心 （.sina.com.cn) 下发的 SSO cookie，之后 heartbeat 会用它换取新的微博 XSRF-TOKEN。这个方法每7天之内要执行一次，否则 XSRF-TOKEN 续期会失败
    def refresh_login(self):
        response = None

        try:
            with open(WEIBO_SSO_COOKIES_FILE, 'r', encoding = 'utf-8') as file:
                weibo_sso_cookies = json.load(file)
            if not isinstance(weibo_sso_cookies, list) or not weibo_sso_cookies:
                raise ValueError('SSO cookies must be a non-empty array')

            # SSO 必须保留域信息，避免新浪和微博的同名 SUB 相互覆盖
            with requests.Session() as sso_session:
                configure_retries(sso_session)
                sso_session.headers.update({
                    name: self.session.headers[name]
                    for name in ('user-agent', 'accept-language')
                })
                for cookie in weibo_sso_cookies:
                    sso_session.cookies.set(**cookie)

                # 只把微博 Cookie 发给微博域；也让重定向中的删除指令正常生效
                for name, value in self.cookies.items():
                    domain = '.m.weibo.cn' if name == 'XSRF-TOKEN' else '.weibo.cn'
                    sso_session.cookies.set(name, value, domain = domain, path = '/')

                response = sso_session.get(
                    'https://login.sina.com.cn/sso/login.php',
                    params = {
                        'url': 'https://m.weibo.cn/',
                        '_rand': time.time(),
                        'gateway': 1,
                        'service': 'sinawap',
                        'entry': 'sinawap',
                        'useticket': 1,
                        'returntype': 'META',
                        'sudaref': '',
                        '_client_version': '0.6.36',
                    },
                    timeout = 10
                )
                response.raise_for_status()

                # 必须是本次换票新下发的认证，不能拿原有登录状态冒充续期成功
                if not any(
                    cookie.name == 'SUB' and cookie.domain.lstrip('.') == 'weibo.cn'
                    for step in response.history + [response]
                    for cookie in step.cookies
                ):
                    raise ValueError('SSO did not issue a Weibo SUB cookie')

                weibo_xsrf_cookies = {
                    cookie.name: cookie.value
                    for cookie in sso_session.cookies
                    if cookie.domain.lstrip('.') in ('weibo.cn', 'm.weibo.cn')
                }
                self.session.cookies.clear()
                self.session.cookies.update(weibo_xsrf_cookies)
                self.session.headers['x-xsrf-token'] = weibo_xsrf_cookies.get('XSRF-TOKEN', '')

                # 复用原心跳校验登录、刷新 XSRF 并保存；校验失败不保存换票结果
                if not self.heartbeat():
                    raise ValueError('Weibo login verification failed after SSO')

                # 登录中心的凭据也会轮换，留给下一次换票；不混入微博域的 Cookie
                sso_session.cookies.clear_expired_cookies()
                weibo_sso_cookies = [
                    {name: getattr(cookie, name) for name in ('name', 'value', 'domain', 'path', 'secure', 'expires')}
                    for cookie in sso_session.cookies
                    if cookie.domain.lstrip('.') == 'sina.com.cn' or cookie.domain.endswith('.sina.com.cn')
                ]
                with open(WEIBO_SSO_COOKIES_FILE, 'w', encoding = 'utf-8') as file:
                    json.dump(weibo_sso_cookies, file, indent = 2)

            debug('Weibo SSO refresh succeeded')
            return True
        except Exception as err:
            log('Weibo SSO refresh failed: %s' % type(err).__name__)
            details = f'--- Error:\n{err}'
            if response is not None:
                details += (
                    f'\n--- Status: {response.status_code}\n--- URL: {response.url}'
                    f'\n--- Headers:\n{response.headers}\n--- Response:\n{response.text}'
                )
            _write_log('Weibo SSO refresh', details)
            raise

    # 根据 pixiv_user_id 查找微博昵称
    def get_weibo_nickname(self, pixiv_id, pixiv_uid):
        from utils.db import db

        pixiv_uid = str(pixiv_uid)
        set_log_level(+1)

        # 先从数据库中查找
        mappings = db.get_weibo_uid_by(pixiv_uid)

        # 没有
        if not mappings:
            from pixiv.client import pixiv_client

            user_profile = pixiv_client.user_detail(pixiv_uid)
            if not user_profile or 'error' in user_profile:
                log(pixiv_id, 'Failed to get pixiv user profile, pixiv_uid: %s' % pixiv_uid)
                set_log_level(-1)
                return ''
            
            # 从签名里匹配
            signature = user_profile.user.comment
            match = re.search(r'https://(?:www\.)?weibo\.com/((?:u/)?[A-Za-z0-9_]+)', signature)
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
        
        # 不登录，用访客身份尝试获取微博用户信息
        user_info = weibo_guest_client.get_user_info(weibo_uid)

        if not user_info:
            log(pixiv_id, 'Error: failed to open weibo profile page, weibo_uid: %s' % weibo_uid)
            return ''

        nickname = user_info.get('screen_name')
        if nickname:
            return f' @{nickname}'

        log(pixiv_id, f"can't find WEIBO_NICKNAME, weibo_uid: {weibo_uid}")
        return ''

    # 把图片上传到微博，成功返回图片id，失败返回 False
    def upload_image_to_weibo(self, filepath):
        local_image = Path(filepath)
        pixiv_id = local_image.stem

        try:
            data = {
                'type': 'json',
                '_spr': 'screen:1920x1080',
                'st': self.cookies['XSRF-TOKEN']
            }
            with local_image.open('rb') as file:
                # 这个接口要求 multipart type，eg. 'Content-Type': 'multipart/form-data; boundary=xxxxxx'
                files = {
                    'pic': (local_image.name, file, mimetypes.guess_type(local_image.name)[0] or 'application/octet-stream')
                }
                response = self.session.post(
                    'https://m.weibo.cn/api/statuses/uploadPic',
                    data = data,
                    files = files,
                    headers = {'referer': 'https://m.weibo.cn/compose/'},
                    timeout = 60
                )
            response.raise_for_status()
            debug('upload image to weibo returns: ')
            debug(response.text)
            pic_id = response.json().get('pic_id')
            if not pic_id:
                log(pixiv_id, 'Weibo image upload failed')
                log(pixiv_id, response.text)
                return False

            self.update_cookies()
            return pic_id
        except Exception as err:
            log(pixiv_id, f'Weibo image upload failed: {type(err).__name__}: {err}')
            return False

    def do_post_weibo(self, pixiv_id, message, pic_id):
        try:
            data = {
                'content': message,
                'visible': (1 if DEBUG else 0),   # 0 = 全部可见，1 = 仅自己可见，10 = 粉丝
                '_spr': 'screen:1920x1080',
                'st': self.cookies['XSRF-TOKEN'],
                'picId': pic_id                   # 这是提前上传的图片的id
            }
            response = self.session.post(
                'https://m.weibo.cn/api/statuses/update',
                data = data,
                headers = {'referer': 'https://m.weibo.cn/compose/'},
                timeout = 60
            )
            response.raise_for_status()
            debug('post weibo returns:')
            debug(response.text)
            if response.json().get('ok') != 1:
                log(pixiv_id, 'post weibo failed')
                _write_log(
                    pixiv_id,
                    f'Payload sent:\n{json.dumps(data, ensure_ascii = False)}\n'
                    f'Return:\n{response.text}'
                )
                return False
            self.update_cookies()
            return True
        except Exception as err:
            log(pixiv_id, f'Weibo post failed: {type(err).__name__}: {err}')
            if isinstance(err, requests.HTTPError) and err.response is not None:
                _write_log(pixiv_id, f'Weibo post api returned:\n{err.response.text}')
            return False

    def post(self, pixiv_id, image, pic_id):
        from utils.db import db

        # 获取每个作品的前3个tag，拼成 #xxx 的字符串
        tags_string = ' '.join(f"#{tag['name']}#" for tag in image['tags'][:3])

        # 获取微博昵称
        debug('Processing: get WEIBO_NICKNAME')
        weibo_nickname = self.get_weibo_nickname(pixiv_id, image['uid'])

        # 排行发微博
        debug('Posting weibo')
        weibo_text = (
            f"#P站每日排行速报# 第{image['ranking']}位，来自画师 {image['author']} 的 "
            f"{image['title']}。Pid: {pixiv_id}。{tags_string} {weibo_nickname}"
        )

        is_posted = self.do_post_weibo(pixiv_id, weibo_text, pic_id)
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

        return True


weibo_client = WeiboClient()
