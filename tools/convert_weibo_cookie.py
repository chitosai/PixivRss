# 从项目根目录以模块方式运行：python3 -m tools.convert_weibo_cookie xsrf 或 python3 -m tools.convert_weibo_cookie sso
# 以便代码定位到 config.py；不要直接运行 python3 tools/convert_weibo_cookie.py

# 两份 original 文件都是浏览器导出的 Cookie，经过这个脚本转换后才可以被 weibo.client 使用
# sso 导出自 .sina.com.cn，xsrf 导出自 .weibo.cn
import argparse, json

from config import OUTPUTED_WEIBO_SSO_COOKIES_FILE, OUTPUTED_WEIBO_XSRF_COOKIES_FILE, WEIBO_SSO_COOKIES_FILE, WEIBO_XSRF_COOKIES_FILE


def main():
    parser = argparse.ArgumentParser(description = '转换浏览器导出的微博或新浪登录中心 Cookie')
    parser.add_argument('cookie_type', choices = ('xsrf', 'sso'), help = '指定要转换的 Cookie 类型')
    args = parser.parse_args()

    if args.cookie_type == 'xsrf':
        source, target = OUTPUTED_WEIBO_XSRF_COOKIES_FILE, WEIBO_XSRF_COOKIES_FILE
    else:
        source, target = OUTPUTED_WEIBO_SSO_COOKIES_FILE, WEIBO_SSO_COOKIES_FILE

    with open(source, 'r', encoding = 'utf-8') as file:
        exported_cookies = json.load(file)

    if args.cookie_type == 'xsrf':
        cookies = {item['name']: item['value'] for item in exported_cookies}
    else:
        cookies = [
            {
                **{name: item[name] for name in ('name', 'value', 'domain', 'path', 'secure')},
                'expires': int(item['expirationDate']) if item.get('expirationDate') is not None and not item.get('session', False) else None,
            }
            for item in exported_cookies
            if item['domain'].lstrip('.') == 'sina.com.cn' or item['domain'].endswith('.sina.com.cn')
        ]
        if not cookies:
            raise ValueError('No Sina SSO cookies found in the browser export')

    with open(target, 'w', encoding = 'utf-8') as file:
        json.dump(cookies, file, indent = 2 if args.cookie_type == 'sso' else None)


if __name__ == '__main__':
    main()

