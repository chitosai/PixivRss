# -*- coding: utf-8 -*-

from utility import *

# 清理超过7天的图片
threshold = long(time.time() - 3600 * 24 * 7)

for mode in MODE:
    # load json
    current = ReadExist(mode)
    new = {}

    # 遍历
    for pid in current:
        if current[pid]['fetch_time'] > threshold:
            new[pid] = current[pid]

    # save
    UpdateExist(mode, new)
        