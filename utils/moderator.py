import base64, json, mimetypes, socket
import requests

from config import LOG_PATH, OPENAI_API_KEY
from datetime import datetime, timedelta
from pathlib import Path
from PIL import Image, ImageFilter
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError, ProtocolError, ProxyError, ReadTimeoutError
from urllib3.util import Retry
from utils.log import debug, log


_session = requests.Session()
_retries = Retry(total = 2, allowed_methods = None, respect_retry_after_header = False)
for _adapter in _session.adapters.values():
    _adapter.max_retries = _retries

# 借助 OpenAI 的图像审核模型来判断图片是否包含色情内容
def moderate(pixiv_id, filepath):
    try:
        if not OPENAI_API_KEY:
            raise ValueError('OPENAI_API_KEY is not configured')

        content_type = mimetypes.guess_type(str(filepath))[0]

        with open(filepath, 'rb') as image:
            image_data = base64.b64encode(image.read()).decode('ascii')

        response = _session.post(
            'https://api.openai.com/v1/moderations',
            headers = {'Authorization': 'Bearer %s' % OPENAI_API_KEY},
            json = {
                'model': 'omni-moderation-latest',
                'input': [{
                    'type': 'image_url',
                    'image_url': {'url': 'data:%s;base64,%s' % (content_type, image_data)},
                }],
            },
            timeout = (10, 30),
        )
        response.raise_for_status()
        result = response.json()['results'][0]
    except Exception as err:
        try:
            log(pixiv_id, 'Image moderation failed for %s: %s: %s' % (filepath, type(err).__name__, err))
        except OSError:
            pass
        return None

    try:
        _save_result(pixiv_id, result)
    except Exception as err:
        try:
            log(pixiv_id, 'Image moderation result save failed: %s: %s' % (type(err).__name__, err))
        except OSError:
            pass
    return result


# 将 OpenAI API 返回的审核结果保存到日志文件中，方便回头分析合适的阈值
def _save_result(pixiv_id, result):
    filepath = Path(LOG_PATH) / 'moderator.json'
    records = {}
    if filepath.exists():
        with filepath.open('r', encoding = 'utf-8') as file:
            records = json.load(file)

    # 每次更新 moderator.json 时都顺带清除 15 天以前的审核记录，避免文件积累过大
    completed_at = datetime.now().astimezone().replace(microsecond = 0)
    threshold = (completed_at - timedelta(days = 15)).isoformat(timespec = 'seconds')
    records = {
        record_id: record
        for record_id, record in records.items()
        if record['completed_at'] >= threshold
    }

    # 添加当前作品的结果
    records[str(pixiv_id)] = {
        'flagged': result['flagged'],
        'categories': result['categories'],
        'category_scores': result['category_scores'],
        'completed_at': completed_at.isoformat(timespec = 'seconds'),
    }
    with filepath.open('w', encoding = 'utf-8') as file:
        json.dump(records, file, ensure_ascii = False, indent = 2)


# 用 Pillow 的高斯模糊来给图片打码
def blur_image(pixiv_id, filepath, radius = 10):
    with Image.open(filepath) as image:
        # 调色板 PNG 需要先转换颜色模式，透明图片保留 Alpha 通道
        mode = 'RGBA' if 'A' in image.getbands() or 'transparency' in image.info else 'RGB'
        with image.convert(mode) as source_image:
            with source_image.filter(ImageFilter.GaussianBlur(radius = radius)) as blurred_image:
                blurred_image.save(filepath)
                
    log(pixiv_id, 'Sexual content detected, applying Gaussian blur (radius %d)' % radius)
    return filepath
