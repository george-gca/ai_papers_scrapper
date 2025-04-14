import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem


class NeuripsSpider(BaseSpider):
    name = 'neurips'
    # allowed_domains = ['papers.nips.cc/', 'datasets-benchmarks-proceedings.neurips.cc/']
    start_urls = ['https://papers.nips.cc/paper/', 'https://datasets-benchmarks-proceedings.neurips.cc/paper/']

    def __init__(self,  year: str = ''):
        BaseSpider.__init__(self, 'neurips', year)

    def start_requests(self):
        for url in self.start_urls:
            link = f'{url}{self.year}'
            self.logger.info(f'Start scraping {link} for {self.year}')
            yield scrapy.Request(url=link, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        for link in response.xpath('/html/body/div[1]/div/ul/li/a/@href'):
            subpage_url = response.urljoin(link.get())
            self.logger.debug(f'Found {subpage_url}')
            yield scrapy.Request(
                url=subpage_url,
                callback=self.parse_subpage,
                dont_filter=True
            )

    def parse_subpage(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        abstract_url = response.url
        links = response.xpath('//a')
        pdf_link = None

        for link in links:
            link_text = link.xpath('text()').get()
            if link_text is not None and 'paper' in link_text.lower():
                pdf_link = link.xpath('@href').get()
                break

        if pdf_link is None:
            self.logger.warning(
                f'Page does not contain pdf file: {abstract_url}')
            return

        # it is div[2] when looking in chrome, but div[1] in here, don't know why
        title = response.xpath('/html/body/div[1]/div/h4[1]/text()').get()
        if title is None:
            self.logger.warning(
                f'No title found in {abstract_url}')
            return

        i = 3
        abstract = response.xpath(f'/html/body/div[1]/div/p[{i}]/text()').get()
        if not abstract:
            i += 1
            abstract = response.xpath(f'/html/body/div[1]/div/p[{i}]/text()').get()

            if not abstract:
                i += 1
                abstract = response.xpath(f'/html/body/div[1]/div/p[{i}]/text()').get()

        if abstract:
            rest_of_abstract = abstract
            while rest_of_abstract:
                i += 1
                rest_of_abstract = response.xpath(f'/html/body/div[1]/div/p[{i}]/text()').get()
                if rest_of_abstract:
                    abstract += f' {rest_of_abstract}'

        if not abstract:
            abstract = response.xpath('/html/body/div[1]/div/pre/code/text()').get()

        if abstract is None:
            self.logger.warning(
                f'No abstract found for "{title}": {abstract_url}')
            return

        i = 2
        authors = response.xpath(f'/html/body/div[1]/div/p[{i}]/i/text()').get()
        if not authors:
            i += 1
            authors = response.xpath(f'/html/body/div[1]/div/p[{i}]/i/text()').get()

            if not authors:
                i += 1
                authors = response.xpath(f'/html/body/div[1]/div/p[{i}]/i/text()').get()

        if isinstance(abstract, list):
            abstract = ' '.join(abstract)

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

        file_url = response.urljoin(pdf_link)
        self.logger.debug(f'Found pdf url for {title}: {file_url}')
        self.logger.debug(f'Abstract text: {abstract}')

        item = PdfFilesItem()
        # might contain \r in abstract text, like \rightarrow
        item['abstract'] = repr(abstract)
        item['abstract_url'] = abstract_url.replace(
            f'https://papers.nips.cc/paper/{self.year}/hash/', '')
        item['authors'] = authors.strip()
        item['file_urls'] = [file_url] # used to download pdf
        item['pdf_url'] = pdf_link.replace(
            f'/paper/{self.year}/file/', '')
        item['title'] = title
        item['title'] = self.clean_html_tags(item['title'])
        item['title'] = self.clean_extra_whitespaces(item['title'])
        item['title'] = self.clean_quotes(item['title'])
        item['source_url'] = 7
        yield item
