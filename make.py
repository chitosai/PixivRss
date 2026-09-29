# -*- coding: utf-8 -*-
import sys

from config import MODE
from pixiv.client import PixivClient
from pixiv.rss import generate_rss


if __name__ == '__main__':
    if len(sys.argv) <= 1:
        raise RuntimeError('Specify ranking name')

    mode = sys.argv[1]

    if mode not in MODE:
        raise RuntimeError('Unknown ranking name')

    client = PixivClient()
    data = client.fetch(mode)
    generate_rss(mode, data)
