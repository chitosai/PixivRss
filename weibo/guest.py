import requests

from utils.http import configure_retries
from utils.log import log


class WeiboGuestClient:
    ''' 这个类用于以访客身份访问微博，主要用于获取微博用户昵称等，避免和pchan使用的带cookie的会话冲突 '''

    def __init__(self):
        # 访客身份在首次查询时获取，仅保留在内存中
        self.guest_session = requests.Session()
        configure_retries(self.guest_session)
        self.guest_session.headers.update({
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.1.128 Safari/537.36',
            'referer': 'https://weibo.com/',
            'accept-language': 'zh-CN,zh;q=0.8',
        })

    # weibo_uid 兼容数字 UID 和英文字母的个性域名
    def get_user_info(self, weibo_uid):
        weibo_uid = str(weibo_uid)
        if weibo_uid.startswith('u/'):
            weibo_uid = weibo_uid[2:]

        try:
            if not self.guest_session.cookies.get('SUB'):
                response = self.guest_session.post(
                    'https://passport.weibo.com/visitor/genvisitor2',
                    data = {
                        'cb': 'visitor_gray_callback', 'ver': '20250916', 'tid': '',
                        'from': 'weibo', 'webdriver': 'false', 'return_url': 'https://weibo.com/',
                    },
                    timeout = 10,
                )
                response.raise_for_status()

            response = self.guest_session.get(
                'https://weibo.com/ajax/profile/info',
                params = {'custom': weibo_uid},
                timeout = 10,
            )
            response.raise_for_status()
            data = response.json()
            if data['ok'] != 1:
                log(weibo_uid, 'Weibo user profile request failed')
                return None
            user_info = data['data']['user']

        except Exception as err:
            log(weibo_uid, f'Weibo user profile request failed: {type(err).__name__}')
            return None

        return user_info


weibo_guest_client = WeiboGuestClient()
