import base64, mimetypes, socket
import requests

from config import OPENAI_API_KEY
from urllib3.exceptions import ConnectTimeoutError, NewConnectionError, ProtocolError, ProxyError, ReadTimeoutError
from urllib3.util import Retry
from utils.log import log


_session = requests.Session()
_retries = Retry(total = 2, allowed_methods = None, respect_retry_after_header = False)
for _adapter in _session.adapters.values():
    _adapter.max_retries = _retries

# 借助 OpenAI 的图像审核模型来判断图片是否包含色情内容，被微博发现夹图的话就要扣分了
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
        return response.json()['results'][0]
    except Exception as err:
        try:
            log(pixiv_id, 'Image moderation failed for %s: %s: %s' % (filepath, type(err).__name__, err))
        except OSError:
            pass
        return None
