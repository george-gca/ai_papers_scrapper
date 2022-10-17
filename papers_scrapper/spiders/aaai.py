from os import path

import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem


class AAAISpider(BaseSpider):
    name = 'aaai'
    allowed_domains = ['aaai.org/', 'ojs.aaai.org/']
    start_urls = ['https://aaai.org/Library/AAAI/']

    def __init__(self, conference: str = '', year: str = '', new_style: bool = True, subpage: bool = True):
        BaseSpider.__init__(self)
        self.conference = conference
        self.year = year
        self.save_path = path.join(conference.lower(), year)
        self.new_style = new_style
        if isinstance(new_style, str):
            new_style = new_style.lower()
            if new_style == 'false' or new_style == '0':
                self.new_style = False
            else:
                self.new_style = True
        self.subpage = subpage
        if isinstance(subpage, str):
            subpage = subpage.lower()
            if subpage == 'false' or subpage == '0':
                self.subpage = False
            else:
                self.subpage = True

    def start_requests(self):
        for url in self.start_urls:
            # aaai18contents.php
            conference_url = f'{url}{self.conference}{self.year[2:]}contents.php'
            self.logger.info(
                f'Start scraping {conference_url} for {self.year}')
            yield scrapy.Request(url=conference_url, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        if self.subpage:
            for link in response.xpath('//*[@id="box6"]/div/ul/li/a/@href'):
                subpage_url = response.urljoin(link.get())
                self.logger.debug(f'Found {subpage_url}')
                yield scrapy.Request(
                    url=subpage_url,
                    callback=self.parse_subpage,
                    dont_filter=True
                )
        else:
            papers_links = response.xpath(
                '//*[@id="box6"]/div/p/a[1]')

            for paper_link in papers_links:
                title = paper_link.xpath('text()').get()
                if 'this proceedings is also available in' not in title.lower():
                    abstract_link = paper_link.xpath('@href').get()
                    item = PdfFilesItem()
                    item['abstract_url'] = abstract_link.split('/')[-1]
                    item['title'] = title

                    if not self.new_style:
                        splitted_link = abstract_link.split('/')
                        if splitted_link[-2] == 'view':
                            splitted_link[-2] = 'viewPaper'
                            abstract_link = '/'.join(splitted_link)

                    self.logger.debug(f'Found {abstract_link} for {title}')
                    yield scrapy.Request(
                        url=abstract_link,
                        callback=self.parse_abstract,
                        dont_filter=True,
                        meta={'item': item}
                    )

    def parse_subpage(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        papers_links = response.xpath(
            '//*[@id="box6"]/div/p/a[1]')

        for paper_link in papers_links:
            title = paper_link.xpath('text()').get()
            if 'this proceedings is also available in' not in title.lower():
                abstract_link = paper_link.xpath('@href').get()
                item = PdfFilesItem()
                item['abstract_url'] = abstract_link.split('/')[-1]
                item['title'] = title

                self.logger.debug(f'Found {abstract_link} for {title}')
                yield scrapy.Request(
                    url=abstract_link,
                    callback=self.parse_abstract,
                    dont_filter=True,
                    meta={'item': item}
                )

    def parse_abstract(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        item = response.meta['item']
        if self.new_style:
            abstract = response.xpath(
                '/html/body/div/div[1]/div[1]/div/article/div/div[1]/section[3]/p').get()
            if abstract == None:
                abstract = response.xpath(
                    '/html/body/div/div[1]/div[1]/div/article/div/div[1]/section[3]/text()').getall()
                abstract = ''.join(abstract)

            authors = response.xpath(
                '/html/body/div/div[1]/div[1]/div/article/div/div[1]/section[1]/ul/li/span[1]/text()').getall()
            authors = ', '.join(authors)

            file_url = response.xpath(
                '/html/body/div/div[1]/div[1]/div/article/div/div[2]/div[2]/ul/li/a/@href').get()
            title = response.xpath('/html/body/div/div[1]/div[1]/div/article/h1/text()').get()
        else:
            title = response.xpath('//*[@id="title"]/text()').get()
            abstract = response.xpath('//*[@id="abstract"]/div').get()
            file_url = response.xpath('//*[@id="paper"]/a/@href').get()
            authors = response.xpath('//*[@id="author"]/em/text()').get()

        splitted_link = file_url.split('/')
        if splitted_link[-3] == 'view':
            splitted_link[-3] = 'download'
            file_url = '/'.join(splitted_link)

        pdf_url = '/'.join(splitted_link[-2:])
        file_url += '.pdf'

        if abstract == None:
            self.logger.warning(
                f'No abstract found for "{item["title"]}": {item["abstract_url"]}')
            return

        abstract_lines = abstract.split('\n')
        if len(abstract_lines) > 1:
            i = 0
            while i < len(abstract_lines):
                abstract_lines[i] = abstract_lines[i].strip()
                if abstract_lines[i].endswith('-') and i < len(abstract_lines) - 1:
                    abstract_lines[i] = f'{abstract_lines[i]}{abstract_lines.pop(i+1).strip()}'

                i += 1

            abstract = ' '.join(abstract_lines)

        abstract = self.clean_html_tags(abstract)
        abstract = self.clean_extra_whitespaces(abstract)
        while (abstract.startswith('"') and abstract.endswith('"')) or (abstract.startswith("'") and abstract.endswith("'")):
            abstract = abstract[1:-1].strip()

        self.logger.debug(f'Abstract text: {abstract}')
        # might contain \r in abstract text, like \rightarrow
        item['abstract'] = repr(abstract)
        item['file_urls'] = [file_url]  # used to download pdf
        item['pdf_url'] = pdf_url
        item['authors'] = authors.strip()

        item['title'] = self.clean_html_tags(title)
        item['title'] = self.clean_extra_whitespaces(item['title'])
        while (item['title'].startswith('"') and item['title'].endswith('"')) or (item['title'].startswith("'") and item['title'].endswith("'")):
            item['title'] = item['title'][1:-1].strip()

        yield item
