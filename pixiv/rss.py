import datetime, html, os, xml.etree.ElementTree as ET

from email.utils import formatdate, format_datetime
from config import CONFIG, MODE, RSS_PATH
from utils.log import debug


def generate_rss(mode, data):
    debug('[Processing] generating rss')
    title = MODE[mode]['title']

    for total in CONFIG['totals']:
        rss = ET.Element('rss', version = '2.0')
        channel = ET.SubElement(rss, 'channel')
        ET.SubElement(channel, 'title').text = 'Pixiv%s排行 - 前%s' % (title, total)
        ET.SubElement(channel, 'link').text = 'https://rakuen.thec.me/PixivRss/'
        ET.SubElement(channel, 'description').text = '就算是排行也要订阅啊混蛋！'
        ET.SubElement(channel, 'copyright').text = 'Under WTFPL'
        ET.SubElement(channel, 'language').text = 'zh-CN'
        ET.SubElement(channel, 'lastBuildDate').text = formatdate(localtime = True)
        ET.SubElement(channel, 'generator').text = 'PixivRss by TheC'

        for image in data[:total]:
            item = ET.SubElement(channel, 'item')

            # Python 3.6 的 %z 不接受 +09:00，去掉冒号后再解析
            # 输出的 pub_date 格式为： Sat, 26 Sep 2026 00:00:29 +0900
            pub_date = datetime.datetime.strptime(image['date'].replace(':', ''), '%Y-%m-%dT%H%M%S%z')

            desc = (
                '<p>第 %s 位</p>'
                '<p>画师：%s - 上传于：%s - 阅览数：%s - 收藏数：%s</p>'
                '<p><img src="https://pixiv.cat/%s.jpg"></p>'
            ) % (
                image['ranking'],
                html.escape(image['author'], quote = True),
                pub_date.strftime('%Y-%m-%d %H:%M:%S'), # eg. 2026-09-26 00:00:29
                image['view'],
                image['bookmarks'],
                image['preview']
            )

            ET.SubElement(item, 'title').text = image['title']
            ET.SubElement(item, 'guid', isPermaLink = 'false').text = str(image['id'])
            ET.SubElement(item, 'link').text = 'https://www.pixiv.net/artworks/' + str(image['id'])
            ET.SubElement(item, 'description').text = desc
            ET.SubElement(item, 'pubDate').text = format_datetime(pub_date)

        # 输出到文件
        path = os.path.join(RSS_PATH, '%s-%s.xml' % (mode, total))
        ET.ElementTree(rss).write(path, encoding = 'utf-8', xml_declaration = True)

    debug('[Processing] RSS file created')
