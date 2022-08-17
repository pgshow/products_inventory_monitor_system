import config
import fc
import datetime
from retry import retry
from loguru import logger


class Plugin:
    def __init__(self):
        self.lock = None

    def run_job(self, product, lock):
        """
        实际执行插件所执行的方法，该方法所有插件类都需要实现
        """
        raise NotImplementedError

    @retry(tries=5, delay=10, backoff=2, max_delay=120)
    def post(self, session, url, timeout, headers=None):
        if not isinstance(headers, dict):
            headers = dict()

        r = self.get(url, timeout, headers)
        headers['user-agent'] = self.useragent
        return session.get(url=url, headers=headers, timeout=timeout, allow_redirects=False)

    @retry(tries=5, delay=10, backoff=2, max_delay=120)
    def fetch(self, url, timeout, headers=None):
        """
        通用 get 和 post方法
        """
        if not isinstance(headers, dict):
            headers = dict()

        r = self.get(url, timeout, headers)
        return r

    def get(self, url, timeout, headers):
        """
        get 方法
        """
        headers['user-agent'] = self.useragent
        return self.r.get(url=url, headers=headers, timeout=timeout, allow_redirects=False)

    def save(self, unique_id, title='-', ref_no='-', description='-', ref_party='-', category='-', sourcing_type='-', start='-', end='-', where='-', other='-'):
        """
        保存数据到 Database
        """
        title = title.replace('\n', '').replace('\r', '')  # 删除换行符
        description = description.replace('\n', '').replace('\r', '')  # 删除换行符
        other = other.replace('\n', '').replace('\r', '')

        # title 和 description 不能一样，否则只保留一个
        if title == description:
            description = '-'

        # 时间统一格式
        start = self.time_format_convert(start)
        end = self.time_format_convert(end)

        add_time = fc.time2str2(datetime.datetime.now())  # 项目添加时间

        if self.item_expired(end):
            # 排除过期项目
            param = (unique_id,)
        else:
            param = (unique_id, ref_no, title, description, ref_party, start, end, where, category, sourcing_type, add_time, other,)

        config.DB_OBJ.add(lock=self.lock_db, param=param)
