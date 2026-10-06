from urllib3.util import Retry


def configure_retries(session):
    # 每个请求最多重试两次
    retries = Retry(
        total = 2,
        allowed_methods = None,
        backoff_factor = 1,
        status_forcelist = (429, 500, 502, 503, 504),
        raise_on_status = False,
    )
    # 保留现有 Adapter，尤其是 PixivPy / CloudScraper 的 TLS 配置。
    for adapter in session.adapters.values():
        adapter.max_retries = retries
