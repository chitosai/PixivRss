from weibo.client import WeiboClient


if __name__ == '__main__':
    weibo_client = WeiboClient()
    weibo_client.heartbeat()
