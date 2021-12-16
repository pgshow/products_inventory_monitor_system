import os
import time
import inspect
import pkgutil
import fc
import threading

from loguru import logger
from pluginBase import Plugin
from concurrent.futures import ThreadPoolExecutor, wait, ALL_COMPLETED
from total_cjdropshipping import CjdScraper


class PluginCollection:
    """
    该类会通过传入的package查找继承了Plugin类的插件类
    """

    def __init__(self, plugin_package):
        self.plugin_package = plugin_package
        self.reload_plugins()

    def reload_plugins(self):
        """
        重置plugins列表，遍历传入的package查询有效的插件
        """
        self.plugins = []
        self.seen_paths = []
        print()
        print(f">>> Find plugins in {self.plugin_package} package")
        print()
        self.walk_package(self.plugin_package)

    def get_all_plugins(self):
        return self.plugins

    def walk_package(self, package):
        """
        递归遍历包里获取所有的插件
        """
        imported_package = __import__(package, fromlist=['blah'])

        for _, pluginname, ispkg in pkgutil.iter_modules(imported_package.__path__, imported_package.__name__ + '.'):
            if not ispkg:
                plugin_module = __import__(pluginname, fromlist=['blah'])
                clsmembers = inspect.getmembers(plugin_module, inspect.isclass)
                for (_, c) in clsmembers:
                    # 仅加入Plugin类的子类，忽略掉Plugin本身
                    if issubclass(c, Plugin) and (c is not Plugin):
                        print(f'        {c.__module__}.{c.__name__}')
                        self.plugins.append(c())

        # 现在我们已经查找了当前package中的所有模块，现在我们递归查找子packages里的附件模块
        all_current_paths = []
        if isinstance(imported_package.__path__, str):
            all_current_paths.append(imported_package.__path__)
        else:
            all_current_paths.extend([x for x in imported_package.__path__])

        for pkg_path in all_current_paths:
            if pkg_path not in self.seen_paths:
                self.seen_paths.append(pkg_path)

                # 获取当前package中的子目录
                child_pkgs = [p for p in os.listdir(pkg_path) if os.path.isdir(os.path.join(pkg_path, p))]

                # 递归遍历子目录的package
                for child_pkg in child_pkgs:
                    self.walk_package(package + '.' + child_pkg)


def scraping(product, lock):
    if not product:
        return

    plugin = fc.choose_plugin(plugins, product[3])  # 选择采集插件
    plugin.run_job(product=product, lock=lock)


if __name__ == '__main__':
    # 线程锁
    lock = threading.Lock()

    # 爬 Cjdropshipping 全站商品
    # t = CjdScraper(lock)
    # t.start()

    # 获取各站插件
    my_plugins = PluginCollection('target')
    plugins = my_plugins.get_all_plugins()

    while 1:
        # 今天需要检查的商品
        need_check = fc.get_unchecked_today(lock)

        if not need_check:
            logger.warning('There has no product need to scan today')
            time.sleep(300)
            continue

        logger.info(f'There has {len(need_check)} products wait to scan today')

        time.sleep(5)

        with ThreadPoolExecutor(max_workers=2) as t:
            all_task = [t.submit(scraping, p, lock) for p in need_check]
            wait(all_task, return_when=ALL_COMPLETED)  # 等待所有任务完成在返回
