import re
import time
import requests
import brotli
import config

from retry import retry
from loguru import logger
from bs4 import BeautifulSoup, element, NavigableString
import threading


class CjdScraper(threading.Thread):
    def __init__(self, lock):
        super().__init__()
        self.lock = lock

    def run(self):
        while 1:
            self.scrape()
            time.sleep(120)

    def scrape(self):
        # 各主栏目页
        list_urls = [
            'https://cjdropshipping.com/list/wholesale-computer-office-l-1126E280-CB7D-418A-90AB-7118E2D97CCC.html',
            'https://cjdropshipping.com/list/wholesale-bags-shoes-l-2415A90C-5D7B-4CC7-BA8C-C0949F9FF5D8.html',
            'https://cjdropshipping.com/list/wholesale-jewelry-watches-l-2837816E-2FEA-4455-845C-6F40C6D70D1E.html',
            'https://cjdropshipping.com/list/wholesale-health-beauty-hair-l-2C7D4A0B-1AB2-41EC-8F9E-13DC31B1C902.html',
            'https://cjdropshipping.com/list/wholesale-womens-clothing-l-2FE8A083-5E7B-4179-896D-561EA116F730.html',
            'https://cjdropshipping.com/list/wholesale-sports-outdoors-l-4B397425-26C1-4D0E-B6D2-96B0B03689DB.html',
            'https://cjdropshipping.com/list/wholesale-home-garden-furniture-l-52FC6CA5-669B-4D0B-B1AC-415675931399.html',
            'https://cjdropshipping.com/list/wholesale-home-improvement-l-6A5D2EB4-13BD-462E-A627-78CFED11B2A2.html',
            'https://cjdropshipping.com/list/wholesale-automobiles-motorcycles-l-A2F799BE-FB59-428E-A953-296AA2673FCF.html',
            'https://cjdropshipping.com/list/wholesale-toys-kids-babies-l-A50A92FA-BCB3-4716-9BD9-BEC629BEE735.html',
            'https://cjdropshipping.com/list/wholesale-mens-clothing-l-B8302697-CF47-4211-9BD0-DFE8995AEB30.html',
            'https://cjdropshipping.com/list/wholesale-consumer-electronics-l-D9E66BF8-4E81-4CAB-A425-AEDEC5FBFBF2.html',
            'https://cjdropshipping.com/list/wholesale-phones-accessories-l-E9FDC79A-8365-4CA6-AC23-64D971F08B8B.html',
        ]

        for list_url in list_urls:
            try:
                body = self.fetch(list_url)

                soup = BeautifulSoup(body, 'lxml')

                if not soup:
                    return
            except Exception as e:
                logger.error(f'Category collect Err: {e}')
                continue

            max_page = self.extract_max_page(soup)

            if not max_page:
                return

            max_page = int(max_page)
            if max_page <= 0:
                return

            for i in range(1, max_page):
                time.sleep(60)
                # 爬取各分页，提取各产品
                url = f'{list_url}?pageNum={i}&pageSize=60'

                try:
                    body = self.fetch(url)
                    soup = BeautifulSoup(body, 'lxml')

                    products = self.extract_products(soup)

                    self.add_products(products)
                except Exception as e:
                    logger.error(f"Page's collector Err: {e}")

    def extract_max_page(self, soup):
        """最大页数"""
        page_tmp = soup.select('div.to-go span')
        if not len(page_tmp):
            return

        page = page_tmp[1].get_text().replace('of ', '')

        return page

    def extract_products(self, soup):
        """产品和ID"""
        products = []
        for item in soup.select('div.card-wrap div.move-box a'):
            try:
                product_name = item.get_text()
                href = item['href']
                product_code = re.search(r'-p-([0-9ABCDEF-]+?)\.html$', href).group(1)
                products.append({
                    'product_code': product_code,
                    'product_name': product_name,
                    'url': 'https://cjdropshipping.com' + href
                })
            except:
                logger.error('Extract product err')

        return products

    @retry(tries=3, delay=15, backoff=2, max_delay=60)
    def fetch(self, url):
        header = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'accept-encoding': 'gzip,deflate,br',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'max-age=0',
            'referer': 'https://cjdropshipping.com',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0(WindowsNT10.0;Win64;x64)AppleWebKit/537.36(KHTML,likeGecko)Chrome/92.0.4515.131Safari/537.36',
        }

        logger.debug(f"Fetching: {url}")

        r = requests.get(url, headers=header, timeout=30, allow_redirects=False)

        if r.status_code != 200:
            logger.error(F"status {r.status_code}")
        else:
            logger.debug(F"status {r.status_code}")
            r.encoding = "utf-8"
            if 'Content-Encoding' in r.headers and r.headers['Content-Encoding'] == 'br':
                text = brotli.decompress(r.content)
                return text
            else:
                return r.text

        return

    def add_products(self, products):
        """保存新爬到的产品"""
        new_num = 0
        for p in products:
            sql = f"SELECT product_id FROM PRODUCTS WHERE product_code = '{p['product_code']}'"
            if not config.DB_OBJ.select_exist(sql=sql, lock=self.lock):
                sql = '''INSERT INTO PRODUCTS(product_code, product_name, website, url) VALUES(?, ?, ?, ?)'''
                param = (p['product_code'], p['product_name'], 'cjDropShipping', p['url'], )
                config.DB_OBJ.add(lock=self.lock, sql=sql, param=param)
                new_num += 1

        logger.info(f'Add {new_num} new products')
