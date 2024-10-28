import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem


class KDDSpider(BaseSpider):
    name = 'kdd'
    allowed_domains = ['kdd.org/']
    start_urls = ['https://kdd.org/']

    def __init__(self, year: str = ''):
        BaseSpider.__init__(self, 'kdd', year)

    def start_requests(self):
        for url in self.start_urls:
            if self.year != '2022':
                conference_url = f'{url}kdd{self.year}/accepted-papers/toc'
            else:
                conference_url = f'{url}kdd{self.year}/toc.html'

            self.logger.info(f'Start scraping {conference_url} for {self.year}')
            yield scrapy.Request(url=conference_url, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        if self.year == '2017':
            xpath_str = '//*[@id="content"]/div/div/div[1]/div/div/div[1]/div/section/table/tbody/tr/td/strong/span/a'
            replace_in_url = 'https://www.kdd.org/kdd2017/papers/view/'
        elif self.year == '2018':
            xpath_str = '/html/body/main/div/section/div[1]/div/div/div/ul/li/div/span[1]/a'
            replace_in_url = f'https://www.kdd.org/kdd{self.year}/accepted-papers/view/'
        elif self.year == '2020':
            xpath_str = '/html/body/main/div[2]/section/div/div[1]/div/div/ul/li/div/span[1]/a'
            replace_in_url = f'https://www.kdd.org/kdd{self.year}/accepted-papers/view/'

        if self.year < '2021':
            for link in response.xpath(xpath_str):
                title = link.xpath('text()').get()
                title = self.clean_html_tags(title)
                title = self.clean_extra_whitespaces(title)
                while (title.startswith('"') and title.endswith('"')) or (title.startswith("'") and title.endswith("'")):
                    title = title[1:-1].strip()

                abstract_link = link.xpath('@href').get()

                item = PdfFilesItem()
                item['abstract_url'] = abstract_link.replace(replace_in_url, '')
                item['title'] = title

                self.logger.debug(f'Found {abstract_link}')
                yield scrapy.Request(
                    url=abstract_link,
                    callback=self.parse_abstract,
                    dont_filter=True,
                    meta={'item': item}
                )

        else:
            links = response.xpath('//*[@id="DLcontent"]/h3/a')
            abstracts = response.xpath('//*[@id="DLcontent"]/div/div')
            authors_lines = response.xpath('//*[@id="DLcontent"]/ul')
            assert len(links) == len(abstracts) == len(authors_lines), \
                f'Found {len(links)} links, {len(abstracts)} abstracts, and {len(authors_lines)} authors lines'

            for link, abstract, authors_line in zip(links, abstracts, authors_lines):
                abstract_link = link.xpath('@href').get()

                abstract_text = abstract.xpath('p/text()').getall()
                abstract_text = ' '.join(abstract_text)
                abstract_text = self.clean_html_tags(abstract_text)
                abstract_text = self.clean_extra_whitespaces(abstract_text)
                abstract_text = self.clean_quotes(abstract_text)

                title = link.xpath('text()').getall()
                title = ' '.join(title)
                title = self.clean_html_tags(title)
                title = self.clean_extra_whitespaces(title)
                title = self.clean_quotes(title)

                authors = authors_line.xpath('li/text()').getall()
                authors = ', '.join(authors)

                item = PdfFilesItem()
                # item['abstract_url'] = abstract_link.replace('https://dl.acm.org/doi/abs/', '')
                item['abstract_url'] = abstract_link.replace('https://dl.acm.org/doi/', '')
                item['abstract'] = repr(abstract_text)
                item['authors'] = authors.strip()
                item['title'] = title
                item['source_url'] = 5
                yield item

    def parse_abstract(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        item = response.meta['item']

        if self.year == '2017':
            abstract = response.xpath('//*[@id="content"]/div/div[1]/div[1]/div/div/div[2]/p[2]').get()
            authors = response.xpath('//*[@id="content"]/div/div[1]/div[1]/div/div/div[2]/p[1]/strong/text()').get()
            authors = authors.split(';')
            authors = [n[: n.find('(')].strip() for n in authors]
            authors = ', '.join(authors)

        elif self.year == '2018':
            abstract = response.xpath('/html/body/main/section[2]/div/div/div/p').get()
            authors = response.xpath('/html/body/main/section[2]/div/div/div/h6/text()').get()
            authors = authors.split(';')
            authors = [n[: n.find('(')].strip() for n in authors]
            authors = ', '.join(authors)

        elif self.year == '2020':
            abstract = response.xpath('//*[@id="go-to-content"]/div[1]/div/div/p').get()
            authors = response.xpath('//*[@id="go-to-content"]/div[1]/p/text()').get()
            authors = authors.split(';')
            authors = [n[: n.find(':')].strip() for n in authors]
            authors = ', '.join(authors)

        abstract = self.clean_html_tags(abstract)
        abstract = self.clean_extra_whitespaces(abstract)

        item['abstract'] = repr(abstract)
        item['authors'] = authors.strip()
        item['source_url'] = 5
        yield item
