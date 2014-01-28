# -*- coding: utf-8 -*-
from utility import *
from weibo import *

def post(mode, message, filepath):
    # init
    c = APIClient(WEIBO[mode]['APP_KEY'], WEIBO[mode]['APP_SECRET'])
    c.set_access_token(WEIBO[mode]['ACCESS_TOKEN'], 157679999)
    
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