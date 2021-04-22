from config import *
from utility import *

from math import floor

# load local cookies
f = open(WEIBO_COOKIE_FILE, 'r')
cookies = json.load(f)
f.close()

originalCookieStr = json.dumps(cookies)

# prepare requests, fill in the previous cookies
s = requests.Session()
s.cookies.update(cookies)

# heartbeat
def heartbeat():
    global cookies, originalCookieStr, s
    # prepare headers
    headers = {
        'mweibo-pwa': "1",
        'referer': 'https://m.weibo.cn/sw.js',
        'x-requested-with': 'XMLHttpRequest',
        'x-xsrf-token': cookies['XSRF-TOKEN'],
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
    }
    s.headers = headers

    # get current timestamp, to ms as weibo implements
    ts = floor(time.time() * 1000)

    # send request
    r = s.get('https://m.weibo.cn/api/remind/unread?t=' + str(ts))

    # check if return is ok
    data = r.json()
    if data['ok'] != 1:
        log('Weibo heartbeat refresh faild!')
        log('--- Sent cookie')
        log(originalCookieStr)
        log('--- Response:')
        log(r.text)
        log('--- Return Cookie:')
        log(r.cookies)
    else:
        # save updated cookies
        f = open(WEIBO_COOKIE_FILE, 'w')
        cookies = json.dumps(s.cookies.get_dict())
        f.write(cookies)
        f.close()
        debug('Weibo heartbeat refresh succeed')

# when invoked from terminal, call heartbeat
if __name__ == '__main__':
    heartbeat()