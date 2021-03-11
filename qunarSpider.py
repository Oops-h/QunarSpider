import requests
import os
from bs4 import BeautifulSoup
import re
import json
import lxml
from pyquery import PyQuery as pq
import pandas as pd


class QunarSpider:
    def __init__(self):
        self.get_config()
        self.headers = {"user-agent":"Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.58 Safari/537.36"}

    # 配置文件
    def get_config(self):
        with open("qunar_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        self.maxpage = config["maxpage"]
        self.trytime = config["trytime"]
        self.excelfile = config["excelfile"]

    # 爬虫
    def crawl(self):
        for i in range(1, self.maxpage + 1):
            self.index_page(i)

    # 爬取页面详细的内容
    def index_page(self, index):
        print("正在爬取第", index, "页")
        try:
            url = "https://tuan.qunar.com/vc/index.php?category=all&limit={}%2C30".format(index * 30)
            res = requests.get(url, headers=self.headers, verify=False)
            soup = BeautifulSoup(res.text, 'lxml')
            # 去哪网的团购数据加载在最后一个 script 中
            sc = soup.find_all('script')
            # 使用正则将script标签中的{html:  ......} 内容匹配
            pattern = re.compile(r'{.*}')
            match = pattern.search(sc[-1].string)
            result = json.loads(match.group())
            # 将html内容加载到pyquery对象中
            doc = pq(result['html'])
            items = doc("ul.cf li").items()
            # print(items)
            self.format_data(items)

        except Exception:
            self.trytime += 1
            if self.trytime >= 5:
                if (index < self.maxpage):
                    self.index_page(index + 1)
                    self.trytime = 0

    def format_data(self, items):
        item_list = [item for item in items]
        dfs = []

        for index in range(len(item_list)):
            item = item_list[index]
            product = {
                'title': item.find("div.nm").attr("title"),
                'detial': item.find("div.sm").attr("title"),
                "buyers": item.find("div.tip span.buy em").text(),
                'image': item.find('div.hand div.imgs img').attr('data-lazy'),
                'price': item.find('div.price span.cash em').text(),
                'detail_link': item.find('a').attr('href'),
                'vali_date': item.find('span.time').text(),
                'type': item.find('div.type_gt').text()
            }
            # print(product)
            # 保存数据
            df = pd.DataFrame(product, index=[1],
                              columns=['title', 'detial', 'buyers', 'image', 'price', 'detail_link', 'vali_date',
                                       'type'])
            dfs.append(df)
        # 将爬取内容保存到excel中
        print(dfs)
        self.save2excel(dfs)

    # 把每页的数据保存到excel中
    def save2excel(self, dfs):
        print('正在将结果保存到excel中')
        total_df = pd.concat(dfs, ignore_index=True)
        if os.path.exists(self.excelfile):
            before_df = pd.read_excel(self.excelfile)
            total_df = pd.concat([before_df, total_df], ignore_index=True).drop_duplicates()
        total_df.to_excel(self.excelfile, sheet_name='去哪网旅游项目团购%s情况', index=False)


if __name__ == "__main__":
    a = QunarSpider()
    a.crawl()
