import pymysql

from config import CONFIG
from utils.log import log


# 数据库操作
class DB:
    # 构造函数时连接数据库
    def __init__(self):
        self.connection = None
        self.cursor = None

        try:
            self.connection = pymysql.connect(
                host = CONFIG['DB_HOST'],
                user = CONFIG['DB_USER'],
                password = CONFIG['DB_PASS'],
                database = CONFIG['DB_NAME'],
                charset = 'utf8',
                autocommit = True,
            )
            self.cursor = self.connection.cursor(pymysql.cursors.DictCursor) # 使fetchall的返回值为带key的字典形式
        except Exception as err:
            if self.connection is not None:
                self.connection.close()
            log(-1, '数据库连接出错 : %s' % err)
            raise

    # 析构时关闭数据库
    def __del__(self):
        self.cursor.close()
        self.connection.close()

    # 查询
    def query(self, sql, data = None):
        try:
            if data:
                self.cursor.execute(sql, data)
            else:
                self.cursor.execute(sql)
            return self.cursor.fetchall()
        except Exception as err:
            log('Error in DB Query')
            log(str(err))
            raise

    # 执行
    def run(self, sql, data):
        try:
            self.cursor.execute(sql, data)
            return self.connection.insert_id()
        except Exception as err:
            log('Error in DB execute')
            log(str(err))
            raise

    # 根据pixiv_user_id从数据库查找微博昵称
    def get_weibo_uid_by(self, pixiv_uid):
        sql = 'SELECT `weibo_uid` FROM `pixiv_weibo_id_map` WHERE `pixiv_uid` = %s'
        return self.query(sql, (pixiv_uid,))

    # 插入pixiv_user_id到weibo_user_id的映射
    def insert_id_map(self, pixiv_uid, weibo_uid):
        sql = 'INSERT INTO `pixiv_weibo_id_map` ( `pixiv_uid`, `weibo_uid` ) VALUES ( %s, %s )'
        return self.run(sql, (pixiv_uid, weibo_uid))

    # 记录用户上榜
    def award_log(self, pixiv_uid):
        # type字段原本是用来表示上了哪个排行的，但是由于现在只剩下日榜了，所以就直接硬编码为1了
        # 数据库里原本的记录就暂且不处理了，反正到现在5年了也只有15000行
        sql = 'INSERT INTO `award_log` ( `type`, `uid` ) VALUES ( %s, %s )'
        return self.run(sql, (1, pixiv_uid))

    # 检查有没有发过
    def check_if_posted(self, pixiv_id):
        sql = 'SELECT `pixiv_id` FROM `weibo_post_history` WHERE `pixiv_id` = %s'
        return self.query(sql, (pixiv_id,))

    # 记录微博已发
    def insert_post_weibo_history(self, pixiv_id):
        sql = 'INSERT INTO `weibo_post_history` ( `pixiv_id` ) VALUES ( %s )'
        return self.run(sql, (pixiv_id,))


# 其他脚本直接导入这个实例使用，不各自建立连接。
db = DB()
