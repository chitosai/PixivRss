# -*- coding: utf-8 -*-
import json, mimetypes, os, re, time

from config import BLACKLIST, DEBUG, WEIBO_PER_HOUR, WEIBO_PER_HOUR_DEBUG
from pixiv.client import PixivClient
from utils.db import db
from utils.log import debug, log, set_log_level
from weibo.client import weibo_client





if __name__ == '__main__':
    global aapi
    # 现在只有daily一个微博了，就不要多余的判断了
    aapi = PixivClient()
    data = aapi.fetch('daily')

    # 开始遍历
    count = 0 # 遍历了几次，用这个变量来确保每小时不会发布超过WEIBO_PER_HOUR
    debug('Begin to iter daily ranking list')
    for illust in data:
        pixiv_id = illust['id']
        debug('* Itering no.%s' % illust['ranking'])
        set_log_level(+2)
        # 如果作者在黑名单里直接跳过
        if illust['uid'] in BLACKLIST:
            debug('Author %s in Blacklist, will skip' % illust['uid'])
            continue
        # 检查有没有发过
        r = db.check_if_posted(pixiv_id)
        if r and len(r):
            debug('Posted, will skip')
            set_log_level(-2)
            continue
        # 下载medium尺寸图到本地
        filepath = aapi.download_image(illust)
        # 上传
        weibo_client.post(pixiv_id, illust, filepath)
        count += 1
        if count >= WEIBO_PER_HOUR or ( DEBUG and count >= WEIBO_PER_HOUR_DEBUG ):
            set_log_level(-2)
            debug('Reached WEIBO_PER_HOUR: %s' % (WEIBO_PER_HOUR if not DEBUG else WEIBO_PER_HOUR_DEBUG))
            break
        set_log_level(-2)
        # +10s，现在是自己模拟请求发图了，为了安全还是把间隔拉大一点
        time.sleep(10)
    debug('All job done, processed %s item(s)' % count)
