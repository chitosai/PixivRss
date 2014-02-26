# -*- coding: utf-8 -*-

from utility import *

# 清理超过15天的exist条目
def ClearExistItem():
    threshold = long(time.time() - 3600 * 24 * 15)

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
        

# 清理超过60天的preview图片
def clearPreviewImage():
    threshold = long(time.time() - 3600 * 24 * 60)

    # 读取所有exist list
    EXIST = []
    for mode in MODE:
        _exist = ReadExist(mode)
        EXIST += _exist
        EXIST = list(set(EXIST)) # 去重

    # 开始读取
    FILES = os.listdir(PREVIEW_PATH)
    FILES.remove('.gitignore') # 去掉.gitignore
    
    for fname in FILES:
        # 查pixiv_id
        pixiv_id = fname.split('.')[0]
        if pixiv_id not in EXIST:
            f = PREVIEW_PATH + fname
            os.remove(f)

ClearExistItem()
clearPreviewImage()