import json

from config import TOKEN_FILE
from pixiv import auth
from utils.log import log

# token 保存在 _pixiv.token.json 中，仅由 heartbeat.py 定时 refresh
# client每次运行时只从 _pixiv.token.json 读取 access_token，不会修改
tokens = None
try:
    f = open(TOKEN_FILE, 'r')
    tokens = json.load(f)
    f.close()
except BaseException as err:
    log('Heartbeat', 'Failed to load access_token')
    log(str(err))

new_tokens = None
try:
    new_tokens = auth.refresh(tokens['refresh_token'])
except BaseException as err:
    log('Heartbeat', 'Error when trying to refresh token')
    log(str(err))

if new_tokens:
    f = open(TOKEN_FILE, 'w')
    f.write(new_tokens)
    f.close()
else:
    log('Heartbeat', 'Failed to refresh token!')
