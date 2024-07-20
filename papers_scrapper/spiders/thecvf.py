import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem

# https://coderecode.com/download-files-scrapy/
# https://docs.scrapy.org/en/latest/topics/spiders.html


class TheCVFSpider(BaseSpider):
    name = 'thecvf'
    allowed_domains = ['openaccess.thecvf.com/']
    start_urls = ['https://openaccess.thecvf.com/']

    def __init__(self, conference: str='', year: str='', subpage: bool=True):
        BaseSpider.__init__(self, conference, year)
        self.subpage = subpage
        if isinstance(subpage, str):
            subpage = subpage.lower()
            if subpage == 'false' or subpage == '0':
                self.subpage = False
            else:
                self.subpage = True

    def start_requests(self):
        #TODO verify why it is not calling parse automatically
        for url in self.start_urls:
            main_track = f'{url}{self.conference.upper()}{self.year}'
            self.logger.info(
                f'Start scraping {main_track} {"with" if self.subpage else "without"} subpage for {self.year}')
            if self.subpage:
                yield scrapy.Request(url=main_track, callback=self.parse)
            else:
                yield scrapy.Request(url=main_track, callback=self.parse_subpage)

            workshop_track = f'{url}{self.conference.upper()}{self.year}_workshops'
            self.logger.info(
                f'Start scraping {workshop_track}')
            yield scrapy.Request(url=workshop_track, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        for link in response.xpath('//*[@id="content"]/dl/dd/a/@href'):
            if link.get() != '../menu.py' and not link.get().endswith('=all'):
                subpage_url = response.urljoin(link.get())
                self.logger.debug(f'Found {subpage_url}')
                yield scrapy.Request(
                    url=subpage_url,
                    callback=self.parse_subpage,
                    dont_filter=True
                )

    def parse_subpage(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        modifier = 1
        for i, link in enumerate(response.xpath('//*[@id="content"]/dl/dd/a[1]/@href')):
            file_extension = link.get().split('.')[-1]
            if file_extension not in ('pdf'):
                modifier -= 1
                continue

            abstract_link = response.xpath(
                f'//*[@id="content"]/dl/dt[{i+modifier}]/a/@href').get()
            title = response.xpath(
                f'//*[@id="content"]/dl/dt[{i+modifier}]/a/text()').get()

            abstract_url = response.urljoin(abstract_link)
            file_url = response.urljoin(link.get())
            self.logger.debug(f'Found pdf url for {title}: {file_url}')

            item = PdfFilesItem()
            item['abstract_url'] = abstract_link.replace('../', '')
            item['file_urls'] = [file_url] # used to download pdf
            item['pdf_url'] = link.get().replace('../', '')
            item['title'] = title

            yield scrapy.Request(url=abstract_url,
                                callback=self.parse_abstract,
                                dont_filter=True,
                                meta={'item': item})

    def parse_abstract(self, response: scrapy.http.TextResponse):
        item = response.meta['item']

        abstract = response.xpath('//*[@id="abstract"]/text()').get()
        if abstract is None:
            self.logger.warning(f'No abstract found for "{item["title"]}": {item["abstract_url"]}')
            return

        abstract = abstract.strip()
        if abstract.startswith('"') and abstract.endswith('"'):
            abstract = abstract[1:-1].strip()

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
        abstract = self.clean_quotes(abstract)

        item['title'] = self.clean_html_tags(item['title'])
        item['title'] = self.clean_extra_whitespaces(item['title'])
        item['title'] = self.clean_quotes(item['title'])

        item['authors'] = response.xpath('//*[@id="authors"]/b/i/text()').get()
        item['authors'] = item['authors'].strip()

        self.logger.debug(f'Abstract text: {abstract}')
        # might contain \r in abstract text, like \rightarrow
        item['abstract'] = repr(abstract)
        item['source_url'] = 9
        yield item
