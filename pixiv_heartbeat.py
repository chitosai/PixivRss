from utility import *
import pixiv_auth

# load current token
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
    new_tokens = pixiv_auth.refresh(tokens['refresh_token'])
except BaseException as err:
    log('Heartbeat', 'Error when trying to refresh token')
    log(str(err))

if new_tokens:
    f = open(TOKEN_FILE, 'w')
    f.write(new_tokens)
    f.close()
else:
    log('Heartbeat', 'Failed to refresh token!')