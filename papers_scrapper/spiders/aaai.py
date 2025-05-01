import re

import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem


class AAAISpider(BaseSpider):
    name = 'aaai'
    # allowed_domains = ['aaai.org/', 'ojs.aaai.org/']
    start_urls = ['https://aaai.org/aaai-publications/aaai-conference-proceedings/']

    def __init__(self, conference: str = '', year: str = '', new_style: bool = True, subpage: bool = True):
        BaseSpider.__init__(self, conference, year)

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f'Start scraping {url} for {self.year}')
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        # https://aaai.org/proceeding/aaai-36-2022/
        for link in response.xpath('//*[@id="genesis-content"]/article/div/div[2]/div/div/div/div/div/div[2]/div/p/a'):
            link_str = link.xpath('text()').get().strip()
            # fix for 2024 links, since 2023 links don't currently have their own links
            if link_str == self.year:
                link_url = link.xpath('@href').get()
                self.logger.info(f'Scraping {link_url}')
                yield scrapy.Request(
                    url=link_url,
                    callback=self.parse_proceedings,
                    dont_filter=True,
                )
                break

    def parse_proceedings(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        year = int(self.year)
        if year <= 2022:
            for link in response.xpath('//*[@id="genesis-content"]/ul/li/a/@href').getall():
                yield scrapy.Request(
                    url=link,
                    callback=self.parse_papers,
                    dont_filter=True,
                )
        else:
            # new style
            for link in response.xpath('//*[@id="genesis-content"]/div[2]/p/a'):
                if f'aaai-{year - 2000}' in link.xpath('text()').get().strip().lower():
                    link_url = link.xpath('@href').get()
                    self.logger.info(f'Scraping proceeding {link_url}')
                    yield scrapy.Request(
                        url=link_url,
                        callback=self.parse_papers,
                        dont_filter=True,
                    )

    def parse_papers(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        year = int(self.year)
        if year <= 2022:
            links = response.xpath('//*[@id="genesis-content"]/div/ul/li/h5/a')
            authors_line = response.xpath('//*[@id="genesis-content"]/div/ul/li/span/p[1]/text()').getall()

        else:
            # new style
            links = response.xpath('/html/body/div/div[1]/div[1]/div/div/div[2]/div/ul/li/div/h3/a')
            authors_line = response.xpath('/html/body/div/div[1]/div[1]/div/div/div[2]/div/ul/li/div/div/div[1]/text()').getall()

        for link, authors in zip(links, authors_line):
            title = link.xpath('string(.)').get().strip()
            abstract_link = link.xpath('@href').get()

            item = PdfFilesItem()
            if not abstract_link.endswith('/'):
                item['abstract_url'] = abstract_link.split('/')[-1]
            else:
                item['abstract_url'] = abstract_link.split('/')[-2]
            item['title'] = title
            item['authors'] = authors.strip()

            if len(item['authors']) == 0:
                self.logger.debug(f'Could not find authors for {title}')
                continue

            self.logger.debug(f'Found {abstract_link} for {title}')
            yield scrapy.Request(
                url=abstract_link,
                callback=self.parse_abstract,
                dont_filter=True,
                meta={'item': item}
            )

    def parse_abstract(self, response: scrapy.http.TextResponse):
        year = int(self.year)
        item = response.meta['item']

        if year <= 2022:
            abstract = response.xpath('string(//*[@id="genesis-content"]/article/div/div[6]/div)').get()
            file_url = response.xpath('//div[@class="pdf-button"]/a/@href').get()
            pdf_url = '/'.join(file_url.split('/')[-2:])[:-4]

        else:
            abstract = response.xpath('/html/body/div/div[1]/div[1]/div/article/div/div[1]/section[4]/text()').getall()
            if len(abstract) == 0:
                abstract = response.xpath('/html/body/div/div[1]/div[1]/div/article/div/div[1]/section[3]/text()').getall()

                if len(abstract) == 0:
                    return

            abstract = abstract[-1]
            if len(abstract) == 0:
                # inspect_response(response, self)
                return

            file_url = response.xpath('/html/body/div/div[1]/div[1]/div/article/div/div[2]/div[2]/ul/li/a/@href').get()
            pdf_url = '/'.join(file_url.split('/')[-2:])

        abstract = self.clean_html_tags(abstract)
        abstract = self.clean_extra_whitespaces(abstract)
        abstract = self.clean_quotes(abstract)

        self.logger.debug(f'Abstract text: {abstract}')
        # might contain \r in abstract text, like \rightarrow
        item['abstract'] = repr(abstract)
        item['file_urls'] = [file_url]  # used to download pdf
        item['pdf_url'] = pdf_url
        item['title'] = self.clean_html_tags(item['title'])
        item['title'] = self.clean_extra_whitespaces(item['title'])
        item['title'] = self.clean_quotes(item['title'])
        item['source_url'] = 1

        self.check_abstract_is_complete(item["title"], abstract, response.url)

        yield item
