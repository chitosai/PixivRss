# -*- coding: utf-8 -*-

# 生成静态页面
CONFIG = {
	'page_title'         : 'ただ一人の楽園', # 静态页面标题
	'animation_duration' : 1,               # 动画持续时间
	'animation_delay'    : 3,               # 图片更换间隔
	'cube_size'          : 100              # 区块大小
}

HTML = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>%s</title>
    <link rel="stylesheet" href="inc/pixivwall.css">
</head>
<body>
    <div id="wall-wrapper"></div>
    <div id="origins">%s</div>
    <script src="inc/jquery-1.9.1.min.js"></script>
    <script src="inc/jquery.transit.min.js"></script>
    <script src="inc/pixivwall.animations.js"></script>
    <script src="inc/pixivwall.js"></script>
    <script>
        DURATION = %s;
        DELAY = %s;
        CUBE_SIZE = %s;
    </script>
</body>
</html>
'''

# 读取目录下的图片
import os, platform, sys

# 分隔符
if platform.system() == 'Windows': SLASH = '\\'
else: SLASH = '/'

# 获取图片列表
IMAGE_PATH = sys.path[0] + SLASH + 'images' + SLASH
IMAGE_LIST = os.listdir(IMAGE_PATH)

IMAGES = '\n'
for image in IMAGE_LIST:
    if image == '.gitignore' : continue
    IMAGES += '\t\t<img class="origin" src="images/' + image + '" />\n'
IMAGES += '\t'
# 生成新静态页面
f = open('index.html', 'w')
f.write( HTML % (
    CONFIG['page_title'], 
    IMAGES, 
    CONFIG['animation_duration'],
    CONFIG['animation_delay'], 
    CONFIG['cube_size']
))
f.close()