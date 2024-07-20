import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem


class EccvSpider(BaseSpider):
    name = 'eccv'
    allowed_domains = ['ecva.net/']
    start_urls = ['https://www.ecva.net/papers.php']

    def __init__(self,  year: str = ''):
        BaseSpider.__init__(self, 'eccv', year)

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f'Start scraping {url} for {self.year}')
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        titles = response.xpath('//*[@id="content"]/dl/dt/a/text()').getall()
        abstracts_links = response.xpath('//*[@id="content"]/dl/dt/a/@href').getall()
        pdfs_links = response.xpath(
            '//*[@id="content"]/dl/dd/a/@href').getall()
        assert len(titles) == len(abstracts_links) == len(pdfs_links), \
            f'Found {len(titles)} titles, {len(abstracts_links)} abstracts, and {len(pdfs_links)} pdfs'

        self.logger.info(f'Found {len(titles)} papers')

        for title, abstract_link, pdf_link in zip(titles, abstracts_links, pdfs_links):
            if abstract_link.split('/')[1] == f'{self.name}_{self.year}':
                abstract_url = response.urljoin(abstract_link)
                pdf_url = response.urljoin(pdf_link)
                item = PdfFilesItem()
                item['abstract_url'] = abstract_link.replace(
                    f'papers/eccv_{self.year}/papers_ECCV/html/', '').replace('.php', '')
                item['file_urls'] = [pdf_url]  # used to download pdf
                item['pdf_url'] = pdf_link.replace(
                    f'papers/eccv_{self.year}/papers_ECCV/papers/', '').replace('.pdf', '')
                item['title'] = title.strip()

                self.logger.debug(f'Found pdf url for {title}: {pdf_link}')

                yield scrapy.Request(url=abstract_url,
                                    callback=self.parse_abstract,
                                    dont_filter=True,
                                    meta={'item': item})

    def parse_abstract(self, response: scrapy.http.TextResponse):
        item = response.meta['item']

        abstract = response.xpath('//*[@id="abstract"]/text()').getall()
        if abstract is None:
            self.logger.warning(
                f'No abstract found for "{item["title"]}": {item["abstract_url"]}')
            return

        abstract = ' '.join([a.strip() for a in abstract if len(a.strip()) > 0])
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

        item['authors'] = response.xpath('//*[@id="authors"]/b/i/text()').get().strip()

        item['title'] = self.clean_html_tags(item['title'])
        item['title'] = self.clean_extra_whitespaces(item['title'])
        item['title'] = self.clean_quotes(item['title'])

        self.logger.debug(f'Abstract text: {abstract}')
        # might contain \r in abstract text, like \rightarrow
        item['abstract'] = repr(abstract)
        item['source_url'] = 3
        yield item
