import datetime

import config


class UI:
    def __init__(self):
        pass

    @staticmethod
    def get_items():
        """所有商品"""
        sql = f"SELECT * FROM PRODUCTS"
        products = config.DB_OBJ.select_many(sql=sql)
        if not isinstance(products, list):
            return 0
        else:
            return products

    @staticmethod
    def get_items_num():
        """商品总数"""
        sql = f"SELECT COUNT(*) FROM PRODUCTS"
        num = config.DB_OBJ.select_many(sql=sql)
        if not isinstance(num, list):
            return 0
        else:
            return num[0][0]

    @staticmethod
    def get_inventory_crawl_times():
        """库存采集数量"""
        sql = f"SELECT COUNT(*) FROM INVENTORY_DAILY"
        num = config.DB_OBJ.select_many(sql=sql)
        if not isinstance(num, list):
            return 0
        else:
            return num[0][0]

    @staticmethod
    def get_time_str():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")