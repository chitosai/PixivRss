import json

from config import OUTPUTED_WEIBO_COOKIE_FILE, WEIBO_COOKIE_FILE


def main():
    f = open(OUTPUTED_WEIBO_COOKIE_FILE, 'r')
    cookie_full = json.load(f)
    f.close()
    cookies = {}

    for item in cookie_full:
        cookies[item['name']] = item['value']

    f = open(WEIBO_COOKIE_FILE, 'w')
    json.dump(cookies, f)
    f.close()


main()

