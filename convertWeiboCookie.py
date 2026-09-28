import json

from config import OUTPUTED_WEIBO_COOKIE_FILE, WEIBO_COOKIE_FILE

def main():
    f = open(OUTPUTED_WEIBO_COOKIE_FILE, 'r')
    cookieFull = json.load(f)
    f.close()
    cookies = {}

    for item in cookieFull:
        cookies[item['name']] = item['value']

    f = open(WEIBO_COOKIE_FILE, 'w')
    json.dump(cookies, f)
    f.close()

main()

