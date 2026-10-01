import json

from pathlib import Path
from urllib.parse import urlparse
from pixivpy3 import AppPixivAPI
from pixiv import auth
from config import MODE, TEMP_PATH, TOKEN_FILE
from utils.log import debug, log, set_log_level


class PixivClient(AppPixivAPI):
    '''扩展PixivPy3的AppPixivAPI类，增加了从本地文件读取token的功能，以及对illust_ranking的自动转换'''

    # 实例化的时候自动从本地文件读取token
    def __init__(self):
        debug('Init PixivClient')
        super().__init__(timeout = (10, 30))

        try:
            with open(TOKEN_FILE, 'r', encoding = 'utf-8') as f:
                tokens = json.load(f)
            if not isinstance(tokens, dict):
                raise ValueError('Token file does not contain a valid JSON object')
            self.access_token = tokens['access_token']
            self.refresh_token = tokens['refresh_token']
            debug('Local token loaded')
        except Exception as err:
            log('Failed to load access_token from file')
            log(str(err))
            raise

    # 这个方法负责定时 refresh token 并写入_pixiv.token.json
    # client 初始化时只从 _pixiv.token.json 读取 token，调用 heartbeat 才执行更新
    def heartbeat(self):
        try:
            token_response = auth.refresh(self.refresh_token)
            if not token_response:
                raise ValueError('Pixiv returned empty token')
        except (Exception, SystemExit) as err:
            log('Heartbeat', 'Failed to refresh token: %s: %s' % (type(err).__name__, err))
            raise

        new_tokens = json.loads(token_response)
        self.access_token = new_tokens['access_token']
        self.refresh_token = new_tokens['refresh_token']

        try:
            with open(TOKEN_FILE, 'w', encoding = 'utf-8') as f:
                json.dump(new_tokens, f)
        except Exception as err:
            log('Heartbeat', 'Failed to write token: %s: %s' % (type(err).__name__, err))
            raise

    # 不知道为什么PixivPy3用的ranking name和p站原生的不一致，在illust_ranking里自动转一下
    def illust_ranking(self, rank_name):
        ppy_name = MODE[rank_name]['ppyName']
        return super().illust_ranking(ppy_name)

    # 获取排行
    def fetch(self, mode):
        debug('Get %s ranking page' % mode)
        r = self.illust_ranking(mode)
        if 'error' in r:
            log('Failed to get %s ranking list, will exit' % mode)
            log(json.dumps(r))
            raise RuntimeError()

        # 筛选出我们需要的数据，并提前加上作品排名和大图链接，方便pchan使用
        data = []
        for ranking, obj in enumerate(r.illusts, start = 1):
            data.append({
                'id': obj.id,
                'title': obj.title,
                'author': obj.user.name,
                'uid': obj.user.id,
                'date': obj.create_date,
                'view': obj.total_view,
                'bookmarks': obj.total_bookmarks,
                'preview': obj.id if obj.page_count == 1 else '%s-1' % obj.id,
                'ranking': ranking,  # 这幅图在榜上排第几
                'images': {
                    'medium': obj.image_urls.medium,
                    'large': obj.image_urls.large,
                    'original': (
                        obj['meta_single_page']['original_image_url']
                        if 'original_image_url' in obj['meta_single_page']
                        else obj['meta_pages'][0]['image_urls']['original']
                    )
                },
                'tags': obj.tags
            })
        return data
    
    # 下载 Pixiv 原图
    def download_image(self, illust):
        debug('Download image')
        pixiv_image_url = illust['images']['original'] or illust['images']['large'] or illust['images']['medium']

        if not pixiv_image_url:
            log('Image url not found!')
            log(json.dumps(illust))
            raise RuntimeError()
        
        extension = Path(urlparse(pixiv_image_url).path).suffix or '.jpg'
        local_image = Path(TEMP_PATH) / ('%s%s' % (illust['id'], extension))
        self.download(pixiv_image_url, path = str(local_image.parent), name = local_image.name, replace = True)
        debug('Download finished, saved to %s' % local_image)

        # 检查文件尺寸，如果超过 2M 就用 Pillow 压缩一遍
        original_size = local_image.stat().st_size
        if original_size > 2000000:
            from PIL import Image

            set_log_level(+2)
            try:
                debug('%s: File size %s, will run a compress' % (illust['id'], original_size))
                with Image.open(local_image) as image:
                    # 抛弃 Alpha 通道，优化文件尺寸，质量 80
                    with image.convert('RGB') as compressed_image:
                        output_path = local_image.with_suffix('.jpg')
                        compressed_image.save(output_path, 'JPEG', optimize = True, quality = 80)
                # 如果压缩后文件名和原文件名不一样 (.jpg/.png)，就删除原文件，避免占用空间
                if output_path != local_image:
                    local_image.unlink()
                local_image = output_path
                debug('%s: Compressed size: %s' % (illust['id'], local_image.stat().st_size))
            finally:
                set_log_level(-2)

        return str(local_image)


pixiv_client = PixivClient()
