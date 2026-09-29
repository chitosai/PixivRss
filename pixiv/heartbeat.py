import json

from config import TOKEN_FILE
from pixiv import auth
from utils.log import log


# 这个方法负责定时 refresh token 并写入_pixiv.token.json
# client每次运行时只从 _pixiv.token.json 读取 access_token，不会执行更新
def main():
    try:
        with open(TOKEN_FILE, 'r', encoding = 'utf-8') as f:
            tokens = json.load(f)
        refresh_token = tokens['refresh_token']
    except Exception as err:
        log('Heartbeat', 'Failed to load token: %s: %s' % (type(err).__name__, err))
        raise

    try:
        new_tokens = auth.refresh(refresh_token)
        if not new_tokens:
            raise ValueError('Pixiv returned empty token')
    except (Exception, SystemExit) as err:
        log('Heartbeat', 'Failed to refresh token: %s: %s' % (type(err).__name__, err))
        raise

    try:
        with open(TOKEN_FILE, 'w', encoding = 'utf-8') as f:
            f.write(new_tokens)
    except Exception as err:
        log('Heartbeat', 'Failed to write token: %s: %s' % (type(err).__name__, err))
        raise


if __name__ == '__main__':
    main()
