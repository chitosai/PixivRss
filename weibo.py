from config import *
from utility import *

class Weibo():
    def __init__(self):
        # load local cookies
        f = open(WEIBO_COOKIE_FILE, 'r')
        self.originalCookieStr = f.read()
        f.close()
        self.cookies = json.loads(self.originalCookieStr)

        # prepare requests, fill in the previous cookies
        self.s = requests.Session()
        self.s.cookies.update(self.cookies)

        # prepare headers
        self.s.headers = {
            'mweibo-pwa': "1",
            'origin': 'https://m.weibo.cn',
            'referer': 'https://m.weibo.cn/sw.js',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
        }

    def heartbeat(self):
        self.s.headers['x-xsrf-token'] = self.cookies['XSRF-TOKEN']

        # send request
        r = self.s.get('https://m.weibo.cn/api/config')

        # check if return is ok
        data = r.json()
        if data['ok'] != 1:
            log('Weibo heartbeat refresh faild!')
            log('--- Sent cookie')
            log(self.originalCookieStr)
            log('--- Response:')
            log(r.text)
            log('--- Return Cookie:')
            log(r.cookies)
        else:
            # save updated cookies
            cookies = json.dumps(self.s.cookies.get_dict())
            f = open(WEIBO_COOKIE_FILE, 'w')
            f.write(cookies)
            f.close()
            debug('Weibo heartbeat refresh succeed')

# when invoked from terminal, call heartbeat
if __name__ == '__main__':
    weibo = Weibo()
    weibo.heartbeat()