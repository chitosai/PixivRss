# -*- coding: utf-8 -*-
from utility import *
from weibo import *

def post(mode, message, filepath):
    # init
    c = APIClient(WEIBO_APP_KEY, WEIBO_APP_SECRET)
    c.set_access_token(WEIBO_ACCESS_TOKEN[mode], 157679999)
    
    # upload
    try:
        f = open(filepath, 'rb')

        r = c.statuses.upload.post(status = message, pic = f)
        if 'error' in r:
            log(filepath, r)
            return False
        else:
            return r['original_pic']

    except Exception, err:
        log(filepath, err)
        return False
        
    finally:
        f.close()