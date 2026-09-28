import os, time
import requests
from config import DEBUG, LOG_PATH, PUSHOVER_API, PUSHOVER_APP, PUSHOVER_USER

__LOG_LEVEL = 0

def SetLogLevel(delta):
    global __LOG_LEVEL
    __LOG_LEVEL += delta

# DEBUG
def debug(message):
    global DEBUG
    if DEBUG:
        print(__LOG_LEVEL * '  ' + str(message))

# 把最终写入log文件单独拆分出来，这样notify超时时也可以留下日志而不会和log()里的Notify互相调用死循环
def _write_log(pixiv_id, message):
    log_content = '%s %s, %s\n' % (time.strftime('[%H:%M:%S] ', time.localtime(time.time())), pixiv_id, message)
    with open(os.path.join(LOG_PATH, time.strftime('%Y-%m-%d.log', time.localtime(time.time()))), 'a', encoding = 'utf-8') as f:
        f.write(log_content)

def log(pixiv_id, message = None):
    if message is None:
        message = pixiv_id
        pixiv_id = -1

    message = str(message)
    debug(message)
    notify(message)
    _write_log(pixiv_id, message)

# 有报错时发一个提醒给我，不然这玩意儿挂了真是注意不到
def notify(message):
    try:
        response = requests.post(PUSHOVER_API, data = {
            'token': PUSHOVER_APP,
            'user': PUSHOVER_USER,
            'message': message,
        }, timeout = 10)
        response.raise_for_status()
    except requests.exceptions.RequestException as err:
        _write_log(-1, 'Pushover request failed: %s' % err)
