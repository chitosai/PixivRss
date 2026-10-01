import json
import requests

from config import WEIBO_COOKIE_FILE
from utils.log import _write_log, debug, log


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


weibo_client = WeiboClient()