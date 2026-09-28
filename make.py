# -*- coding: utf-8 -*-
from pixiv.client import PixivClient
from config import *
from pixiv.rss import GenerateRss

if __name__ == '__main__':
    if len(sys.argv) <= 1:
        raise RuntimeError('Specify ranking name')
        
    mode = sys.argv[1]

    if mode not in MODE:
        raise RuntimeError('Unknown ranking name')
    
    client = PixivClient()
    data = client.fetch(mode)
    GenerateRss(mode, data)
