import re
from os import path

import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem


class AAAISpider(BaseSpider):
    name = 'aaai'
    allowed_domains = ['aaai.org/', 'ojs.aaai.org/']
    start_urls = ['https://aaai.org/aaai-publications/aaai-conference-proceedings/']

    def __init__(self, conference: str = '', year: str = '', new_style: bool = True, subpage: bool = True):
        BaseSpider.__init__(self, conference, year)
        self.regex = re.compile(rf'{conference}-[\d]+-{year}')

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f'Start scraping {url} for {self.year}')
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        # https://aaai.org/proceeding/aaai-36-2022/
        for link in response.xpath('//a[@href]'):
            link_str = link.xpath('@href').get()
            if self.regex.search(link_str) is not None:
                yield scrapy.Request(
                    url=link_str,
                    callback=self.parse_proceedings,
                    dont_filter=True,
                )

    def parse_proceedings(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        for link in response.xpath('//*[@id="genesis-content"]/ul/li/a/@href').getall():
            yield scrapy.Request(
                url=link,
                callback=self.parse_papers,
                dont_filter=True,
            )

    def parse_papers(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        links = response.xpath('//*[@id="genesis-content"]/div/ul/li/h5/a')
        authors_line = response.xpath('//*[@id="genesis-content"]/div/ul/li/span/p[1]/text()').getall()

        for link, authors in zip(links, authors_line):
            title = link.xpath('text()').get().strip()
            abstract_link = link.xpath('@href').get()

            item = PdfFilesItem()
            item['abstract_url'] = abstract_link.split('/')[-2]
            item['title'] = title
            item['authors'] = authors.strip()

            self.logger.debug(f'Found {abstract_link} for {title}')
            yield scrapy.Request(
                url=abstract_link,
                callback=self.parse_abstract,
                dont_filter=True,
                meta={'item': item}
            )

    def parse_abstract(self, response: scrapy.http.TextResponse):
        item = response.meta['item']
        abstract = response.xpath('//*[@id="genesis-content"]/article/div[2]/div[1]/div/p/text()').get()
        file_url = response.xpath('//*[@id="genesis-content"]/article/div[1]/a[1]/@href').get()

        splitted_link = file_url.split('/')
        pdf_url = '/'.join(splitted_link[-2:])[:-4]

        abstract = self.clean_html_tags(abstract)
        abstract = self.clean_extra_whitespaces(abstract)
        while (abstract.startswith('"') and abstract.endswith('"')) or (abstract.startswith("'") and abstract.endswith("'")):
            abstract = abstract[1:-1].strip()

        self.logger.debug(f'Abstract text: {abstract}')
        # might contain \r in abstract text, like \rightarrow
        item['abstract'] = repr(abstract)
        item['file_urls'] = [file_url]  # used to download pdf
        item['pdf_url'] = pdf_url
        item['title'] = self.clean_html_tags(item['title'])
        item['title'] = self.clean_extra_whitespaces(item['title'])
        while (item['title'].startswith('"') and item['title'].endswith('"')) or (item['title'].startswith("'") and item['title'].endswith("'")):
            item['title'] = item['title'][1:-1].strip()

        yield item
