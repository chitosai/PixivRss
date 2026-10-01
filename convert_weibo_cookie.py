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

