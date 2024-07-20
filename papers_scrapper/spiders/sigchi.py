import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem


class SIGCHISpider(BaseSpider):
    name = 'sigchi'
    allowed_domains = ['st.sigchi.org/', 'chi2021.acm.org/']
    # start_urls = ['https://st.sigchi.org/publications/toc/chi-2020.html', 'https://st.sigchi.org/publications/toc/chi-2020-ea.html']

    def __init__(self, year: str = ''):
        BaseSpider.__init__(self, 'sigchi', year)
        # if int(year) < 2021:
        self.start_urls = [f'https://st.sigchi.org/publications/toc/chi-{year}.html']
        # else:
            # self.start_urls = [f'https://chi{year}.acm.org/proceedings']

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(
                f'Start scraping {url}')
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        links = response.xpath('//*[@id="DLcontent"]/h3/a')
        abstracts = response.xpath('//*[@id="DLcontent"]/div/div')
        authors_lines = response.xpath('//*[@id="DLcontent"]/ul')

        if len(authors_lines) == len(abstracts) - 1:
            # adding missing authors for 2021 paper https://dl.acm.org/doi/10.1145/3411764.3445719
            authors_lines.insert(578, 'Daniel McDuff, Ewa M. Nowara')

        assert len(links) == len(abstracts) == len(authors_lines), f'Found {len(links)} links, {len(abstracts)} abstracts, and {len(authors_lines)} authors lines'

        self.logger.info(f'Found {len(links)} papers')

        for link, abstract, authors_line in zip(links, abstracts, authors_lines):
            abstract_link = link.xpath('@href').get()

            abstract_text = abstract.xpath('p/text()').getall()
            abstract_text = [a.strip() for a in abstract_text]
            abstract_text = ' '.join(abstract_text)
            abstract_text = self.clean_html_tags(abstract_text)
            abstract_text = self.clean_extra_whitespaces(abstract_text)
            abstract_text = self.clean_quotes(abstract_text)

            title = link.xpath('text()').getall()
            title = ' '.join(title)
            title = self.clean_html_tags(title)
            title = self.clean_extra_whitespaces(title)
            title = self.clean_quotes(title)

            if not isinstance(authors_line, str):
                authors = authors_line.xpath('li/text()').getall()
                authors = ', '.join(authors)
            else:
                authors = authors_line

            item = PdfFilesItem()
            item['abstract_url'] = abstract_link.replace('https://dl.acm.org/doi/abs/', '')
            item['abstract_url'] = abstract_link.replace('https://dl.acm.org/doi/', '')
            item['authors'] = authors.strip()
            item['abstract'] = repr(abstract_text)
            item['title'] = title
            item['source_url'] = 8
            yield item
