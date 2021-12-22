import config


def choose_plugin(plugins, website):
    """选择对应插件"""
    for plugin in plugins:
        if plugin.id == website:
            return plugin


def get_unchecked_today(lock):
    """获取今日需要检查的商品"""
    sql = "SELECT * FROM PRODUCTS WHERE active_time > date('now','-15 days')"
    all_products = config.DB_OBJ.select_many(sql=sql, lock=lock)

    unchecked_products = []
    for p in all_products:
        # 今天是否已经检查库存
        sql = f"select id from inventory_daily where product_id={p[0]} AND scan_time > date('now','localtime')"
        if config.DB_OBJ.select_exist(sql, lock=lock):
            continue

        unchecked_products.append(p)

    return unchecked_products
