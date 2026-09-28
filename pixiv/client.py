import json

from pixivpy3 import AppPixivAPI
from config import MODE, TOKEN_FILE
from utils.log import debug, log


class PixivClient(AppPixivAPI):
    '''扩展PixivPy3的AppPixivAPI类，增加了从本地文件读取token的功能，以及对illust_ranking的自动转换'''

    # 实例化的时候自动从本地文件读取token
    def __init__(self):
        debug('Init ppy class')
        super(self.__class__, self).__init__(timeout = (10, 30))
        # load token
        try:
            with open(TOKEN_FILE, 'r', encoding = 'utf-8') as f:
                tokens = json.load(f)
            if not isinstance(tokens, dict):
                raise ValueError('Token file does not contain a valid JSON object')
            for field in ('access_token', 'refresh_token'):
                value = tokens.get(field)
                if not isinstance(value, str) or not value.strip():
                    raise ValueError('Missing or invalid token field: %s' % field)
            self.access_token = tokens['access_token']
            self.refresh_token = tokens['refresh_token']
            debug('Local token loaded')
        except Exception as err:
            log('Failed to load access_token from file')
            log(str(err))
            raise

    # 不知道为什么ppy用的ranking name和p站原生的不一致，在illust_ranking里自动转一下
    def illust_ranking(self, rank_name):
        ppy_name = MODE[rank_name]['ppyName']
        return super(self.__class__, self).illust_ranking(ppy_name)

    # 获取排行
    def fetch(self, mode):
        debug('Get %s ranking page' % mode)
        r = self.illust_ranking(mode)
        if 'error' in r:
            log('Failed to get %s ranking list, will exit' % mode)
            log(json.dumps(r))
            raise RuntimeError()

        # 筛选出我们需要的数据
        tmp = {
            'ranking': 0 # 这个ranking直接作为int传入filter会造成无法修改，所以稿一个dict，用修改attr的方式实现
        }

        def filter(obj):
            tmp['ranking'] += 1
            return {
                'id': obj.id,
                'title': obj.title,
                'author': obj.user.name,
                'uid': obj.user.id,
                'date': obj.create_date,
                'view': obj.total_view,
                'bookmarks': obj.total_bookmarks,
                'preview': obj.id if obj.page_count == 1 else '%s-1' % obj.id,
                'ranking': tmp['ranking'], # 这幅图在榜上排第几，好像暂时只能靠这样自己加
                'images': {
                    'medium': obj.image_urls.medium,
                    'large': obj.image_urls.large,
                    'original': obj['meta_single_page']['original_image_url'] if ( 'original_image_url' in obj['meta_single_page'] ) else obj['meta_pages'][0]['image_urls']['original']
                },
                'tags': obj.tags
            }
        data = list(map(filter, r.illusts))
        return data
