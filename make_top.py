import config
from loguru import logger
from datetime import datetime


class TopMaker:
    def clear(self):
        """清空表"""
        sql = 'delete from top'
        return config.DB_OBJ.delete(sql)

    def make_data(self, start, end):
        """根据查询条件生成新数据"""
        sql = f"select product_id from products"
        products = config.DB_OBJ.select_many(sql=sql)

        for p in products:
            # 计算每个产品库存变化
            sql = f"select diff2 from changes where product_id={p[0]} AND check_time > '{start} 00:00:00' AND check_time < '{end} 24:00:00'"
            changes = config.DB_OBJ.select_many(sql)

            if len(changes) <= 0:
                continue

            change = 0  # 该时间内总的数量变化
            for i in changes:
                change = change + abs(i[0])

            # sql = f"select amount from inventory_daily where product_id={p[0]} AND scan_time > '{start} 00:00:00' AND scan_time < '{end} 24:00:00' ORDER by scan_time DESC LIMIT 1"
            # inventory = config.DB_OBJ.select_one(sql)  # 当前库存情况

            self.save(p[0], change, start, end)

    def save(self, product_id, change, start, end):
        sql = '''INSERT INTO TOP(product_id, period_change, start2end_date) VALUES(?, ?, ?)'''
        param = (product_id, change, f'{start} to {end}',)

        config.DB_OBJ.web_add(sql=sql, param=param)
