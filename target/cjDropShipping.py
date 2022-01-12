import datetime
import time
import requests
import config
import pluginBase

from loguru import logger
from retry import retry


class SubPlugin(pluginBase.Plugin):
    def __init__(self):
        super().__init__()
        self.id = 'cjDropShipping'

    def run_job(self, product, lock):
        logger.info(f"Crawl: {product[0]} - {product[4]}")

        self.crawl(product, lock)

    def crawl(self, product, lock):
        url = 'https://cjdropshipping.com/storehousecj/areaInventory/getAreaInventoryInfo'

        post_data = {
            'pid': product[1]
        }

        for i in range(0, 20):
            try:
                r = self.post(url, post_data)

                if r.status_code != 200:
                    raise Exception(f'Status {r.status_code}')

                json_data = r.json()

                logger.debug(f'{product[1]} - ok')

                real_num, num = self.extract_inventory(json_data)  # cjDropShipping 有 realNum 和 num 两个库存数值

                if self.save_inventory(real_num, num, product[0], lock):
                    self.calculate_change(product_id=product[0], lock=lock)

                return

            except Exception as e:
                if 'json invalid' in str(e) or 'cannot unpack' in str(e):
                    logger.warning(f'{product[1]} json invalid - retry')
                    time.sleep(5)
                    continue

                logger.error(f'{product[1]} err: {e}')
                return

    def calculate_change(self, product_id, lock):
        """计算两天的变化"""
        sql = f"select id from changes where product_id={product_id} AND check_time >= date('now','localtime')"
        if config.DB_OBJ.select_exist(sql, lock=lock):
            return
        # 检查今天的库存变化，先获取最近两天的库存
        sql = f"select amount1, amount2 from inventory_daily where product_id={product_id} ORDER by scan_time DESC LIMIT 2"
        # sql = f"select amount from inventory_daily where product_id={p[0]} AND scan_time > date('now','-1 days', 'localtime') ORDER by scan_time DESC LIMIT 2"
        # sql = f"select * from inventory_daily where product_id={p[0]} AND scan_time > date('now','-3 days') AND scan_time <= date('now','0 days')"
        # sql = f"select amount from inventory_daily where product_id={p[0]} AND scan_time > '2021-12-12' AND scan_time < '2021-12-14'"

        two_days = config.DB_OBJ.select_many(sql=sql, lock=lock)
        if len(two_days) < 2:
            # 数据不足两天
            return

        diff1 = two_days[0][0] - two_days[1][0]  # 计算 realNum 库存变化
        diff2 = two_days[0][1] - two_days[1][1]  # 计算 num 库存变化

        # 记录到数据库
        sql = '''INSERT INTO CHANGES(product_id, diff1, diff2, check_time) VALUES(?, ?, ?, ?)'''
        param = (product_id, diff1, diff2, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),)

        config.DB_OBJ.add(lock, sql=sql, param=param)

    def extract_inventory(self, json_data):
        """提取库存"""
        if not json_data['data']:
            return

        if json_data['data'][0]['realNum'] is None or json_data['data'][0]['num'] is None:
            raise Exception('json invalid')

        return int(json_data['data'][0]['realNum']), int(json_data['data'][0]['num'])

    def save_inventory(self, real_num, num, product_id, lock):
        """保存本次库存记录"""
        sql = '''INSERT INTO INVENTORY_DAILY(product_id, amount1, amount2, scan_time) VALUES(?, ?, ?, ?)'''
        param = (product_id, real_num, num, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),)
        return config.DB_OBJ.add(lock=lock, sql=sql, param=param)

    @retry(tries=15, delay=5, backoff=2, max_delay=60)
    def post(self, url, post_data):
        header = {
            'accept': 'application/json,text/plain,*/*',
            'accept-encoding': 'gzip,deflate',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'content-length': '62',
            'content-type': 'application/json;charset=UTF-8',
            'origin': 'https://cjdropshipping.com',
            'referer': 'https://cjdropshipping.com',
            'sec-ch-ua': '"GoogleChrome";v="95","Chromium";v="95",";NotABrand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0(WindowsNT10.0;Win64;x64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/95.0.4638.69Safari/537.36',
            'Connection': 'close',
        }

        logger.debug(f"Fetching: {url}")

        r = requests.post(url, headers=header, json=post_data, timeout=30, allow_redirects=False)
        r.close()

        return r
