# -*- coding: utf-8 -*-
import scrapy
from scrapy_redis.spiders import RedisSpider
from copy import deepcopy
import urllib
class BookSpider(RedisSpider):
    name = 'book'
    allowed_domains = ['dangdang.com']
    # start_urls = ['http://book.dangdang.com']
    redis_key = "dangdang"

    def parse(self, response):
        div_list = response.xpath("//div[@class='con flq_body']/div[position()>2]")
        print(len(div_list))
        for div in div_list:
            item = {}
            item["b_cate"] = div.xpath("./dl/dt//text()").extract()
            item["b_cate"] = [i.strip() for i in item["b_cate"] if len(i.strip()) > 0]
            dl_list = div.xpath("./div//dl[@class='inner_dl']")
            for dl in dl_list:
                item["m_cate"] = dl.xpath("./dt//text()").extract()
                item["m_cate"] = [i.strip() for i in item["m_cate"] if len(i.strip()) > 0][0]
                # 小分类分组
                a_list = dl.xpath("./dd/a")
                for a in a_list:
                    item["s_href"] = a.xpath("./@href").extract_first()
                    item["s_cate"] = a.xpath("./@title").extract_first()
                    if item["s_href"] is not None:
                        yield scrapy.Request(
                            item["s_href"],
                            callback=self.parse_book_list,
                            meta={"item":deepcopy(item)}
                        )


    def parse_book_list(self,response):
        item = response.meta["item"]
        li_list = response.xpath("//ul[@class='bigimg']/li")
        for li in li_list:
            item["book_img"] = li.xpath("./a/img/@src").extract_first()
            if item["book_img"] == "images/model/guan/url_none.png":
                item["book_img"] = li.xpath("./a/img/@data-original").extract_first()
            item["book_name"] = li.xpath("./a/@title").extract_first()
            item["book_desc"] = li.xpath("./p[@class='detail']/text()").extract_first()
            item["book_price"] = li.xpath("./p[@class='price']/span/text()").extract_first().strip('¥')
            item["book_author"] = li.xpath("./p[@class='search_book_author']/span[1]/a/text()").extract()
            item["book_publish_data"] = li.xpath("./p[@class='search_book_author']/span[2]/text()").extract_first().replace('/','')
            item["book_press"] = li.xpath("./p[@class='search_book_author']/span[3]/a/text()").extract_first()

            yield item

        next_url = item["next_page"] = response.xpath("//li[@class='next']/a/@href").extract_first()

        # next_url = "http://category.dangdang.com" + next_url
        if next_url is not None:
            next_url = urllib.parse.urljoin(response.url,next_url)
            yield scrapy.Request(
                next_url,
                callback=self.parse_book_list,
                meta={"item":item}
            )