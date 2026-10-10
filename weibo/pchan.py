# -*- coding: utf-8 -*-
import time

from config import BLACKLIST, DEBUG, WEIBO_PER_HOUR, WEIBO_PER_HOUR_DEBUG
from pathlib import Path
from pixiv.client import pixiv_client
from utils.db import db
from utils.log import debug, log, set_log_level
from utils.moderator import blur_image, moderate
from weibo.client import weibo_client


def main():
    data = pixiv_client.fetch('daily')
    limit = min(WEIBO_PER_HOUR, WEIBO_PER_HOUR_DEBUG) if DEBUG else WEIBO_PER_HOUR

    count = 0        # 尝试了几次，仅用于 debug 计数
    posted_count = 0 # 发布了几条微博，用这个变量来确保每小时不会发布超过 WEIBO_PER_HOUR
    debug('Begin to iter daily ranking list')
    for illust in data:
        pixiv_id = illust['id']
        debug(f"* Itering no.{illust['ranking']}")
        set_log_level(+2)
        try:
            count += 1
            # 如果作者在黑名单里直接跳过
            if illust['uid'] in BLACKLIST:
                debug(f"Author {illust['uid']} in Blacklist, will skip")
                continue

            # 检查有没有发过
            if db.check_if_posted(pixiv_id):
                debug('Posted, will skip')
                continue

            # 下载原图到本地，原图 >2M 会在这个方法里直接压缩
            local_image = pixiv_client.download_image(illust)

            # 跑一下AI审核，发现色色就自己打一个薄码，免得被微博扣分
            moderation = moderate(pixiv_id, local_image)
            if moderation and moderation['categories']['sexual'] is True:
                local_image = blur_image(pixiv_id, local_image)

            # 上传处理好的图片到微博图床
            debug('Uploading image to Weibo')
            pic_id = weibo_client.upload_image_to_weibo(local_image)
            if pic_id:
                # 上传成功后删除本地文件，失败则保留
                try:
                    Path(local_image).unlink()
                except Exception as err:
                    log(pixiv_id, f'Temporary image deletion failed: {type(err).__name__}: {err}')
                else:
                    if weibo_client.post(pixiv_id, illust, pic_id):
                        posted_count += 1
        finally:
            set_log_level(-2)

        if posted_count >= limit:
            debug(f'Reached WEIBO_PER_HOUR: {limit}')
            break

        # +10s，现在是自己模拟请求发图了，为了安全还是把间隔拉大一点
        time.sleep(10)

    debug(f'All job done, processed {count} item(s), posted {posted_count} item(s)')


if __name__ == '__main__':
    main()
