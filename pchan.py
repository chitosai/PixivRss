# -*- coding: utf-8 -*-
from utility import *
from weibo import *

def post(message, filepath):
    # init
    c = APIClient(WEIBO_APP_KEY, WEIBO_APP_SECRET)
    c.set_access_token(WEIBO_ACCESS_TOKEN, 157679999)
    
    # upload
    try:
        f = open(filepath, 'rb')

        r = c.statuses.upload.post(status=message, pic=f)
        if 'error' in r:
            log(filepath, r)
        else:
            pass
    except Exception, err:
        log(filepath, err)
        pass
    finally:
        f.close()