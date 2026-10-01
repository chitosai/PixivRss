# 从项目根目录以模块方式运行：python3 -m tools.convert_weibo_cookie
# 以便代码定位到 config.py；不要直接运行 python3 tools/convert_weibo_cookie.py。
import json

from config import OUTPUTED_WEIBO_COOKIE_FILE, WEIBO_COOKIE_FILE


def main():
    with open(OUTPUTED_WEIBO_COOKIE_FILE, 'r', encoding = 'utf-8') as file:
        exported_cookies = json.load(file)

    cookies = {item['name']: item['value'] for item in exported_cookies}

    with open(WEIBO_COOKIE_FILE, 'w', encoding = 'utf-8') as file:
        json.dump(cookies, file)


if __name__ == '__main__':
    main()

