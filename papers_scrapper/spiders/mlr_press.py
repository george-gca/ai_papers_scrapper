import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem


class MLRPressSpider(BaseSpider):
    name = 'mlr_press'
    # allowed_domains = ['proceedings.mlr.press/']
    start_urls = ['https://proceedings.mlr.press/']

    def __init__(self, conference: str = '', year: str = ''):
        BaseSpider.__init__(self, conference, year)

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f'Start scraping {url} for {self.year}')
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        conference_names = response.xpath('/html/body/main/div/article/div/ul[3]/li/text()').getall()
        links = response.xpath('/html/body/main/div/article/div/ul[3]/li/a/@href').getall()
        correct_links = [link for c, link in zip(conference_names, links) if self.conference.upper() in c and self.year in c]
        if len(correct_links) == 0:
            self.logger.warning(f'Could not find {self.conference} {self.year}')
            return

        for correct_link in correct_links:
            subpage_url = response.urljoin(correct_link)
            self.logger.info(f'Found {subpage_url}')
            yield scrapy.Request(
                url=subpage_url,
                callback=self.parse_subpage,
                dont_filter=True
            )

    def parse_subpage(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        abstract_links = response.xpath(
            '/html/body/main/div/div/p[3]/a[1]/@href').getall()
        pdf_links = response.xpath(
            '/html/body/main/div/div/p[3]/a[2]/@href').getall()
        assert len(abstract_links) == len(pdf_links), \
            f'Found {len(abstract_links)} abstracts and {len(pdf_links)} pdfs'

        for abstract_link, pdf_link in zip(abstract_links, pdf_links):
            self.logger.debug(f'Found pdf url: {pdf_link}')

            abstract_link = abstract_link.strip()
            if abstract_link.startswith('"') and abstract_link.endswith('"') or \
                    abstract_link.startswith("'") and abstract_link.endswith("'"):
                abstract_link = abstract_link[1:-1].strip()

            item = PdfFilesItem()
            item['abstract_url'] = abstract_link.replace(self.start_urls[0], '')
            item['abstract_url'] = '.'.join(item['abstract_url'].split('.')[:-1])
            item['file_urls'] = [pdf_link]  # used to download pdf
            item['pdf_url'] = pdf_link.replace(self.start_urls[0], '')
            item['pdf_url'] = '/'.join(item['pdf_url'].split('/')[:-1])

            yield scrapy.Request(url=abstract_link,
                                 callback=self.parse_abstract,
                                 dont_filter=True,
                                 meta={'item': item})

    def parse_abstract(self, response: scrapy.http.TextResponse):
        item = response.meta['item']

        abstract = ' '.join(response.xpath('//*[@id="abstract"]').getall())

        if abstract is None:
            self.logger.warning(
                f'No abstract found for: {item["abstract_url"]}')
            return

        abstract = abstract.strip()
        if abstract.startswith('"') and abstract.endswith('"') or \
                abstract.startswith("'") and abstract.endswith("'"):
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

        self.logger.debug(f'Abstract text: {abstract}')
        # might contain \r in abstract text, like \rightarrow
        item['abstract'] = repr(abstract)

        item['title'] = response.xpath('/html/body/main/div/article/h1/text()').get()
        item['title'] = self.clean_html_tags(item['title'])
        item['title'] = self.clean_extra_whitespaces(item['title'])
        item['title'] = self.clean_quotes(item['title'])

        item['authors'] = response.xpath('/html/body/main/div/article/span/text()').get().strip()
        item['authors'] = item['authors'].replace('\xa0', ' ').strip()
        item['source_url'] = 6

        yield item
