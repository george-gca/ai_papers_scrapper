import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem


class SIGGRAPHSpider(BaseSpider):
    name = 'siggraph'
    # allowed_domains = ['siggraph.org', ]
    start_urls = ['https://www.siggraph.org/siggraph-events/conferences/']

    def __init__(self, conference: str='', year: str = ''):
        BaseSpider.__init__(self, conference, year)

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f'Start scraping {url} for {self.year}')
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        if self.conference == 'siggraph':
            xpath_str = '//*[@id="post-423"]/div/div/div/div[3]/div[5]/div[2]/div/h4'
        elif self.conference == 'siggraph-asia':
            xpath_str = '//*[@id="post-423"]/div/div/div/div[3]/div[5]/div[1]/div/h4'
        else:
            raise ValueError(f'Conference {self.conference} not supported')

        for i, header in enumerate(response.xpath(xpath_str)):
            if header.xpath('text()').get().strip() == self.year:
                if self.conference == 'siggraph':
                    links = response.xpath(f'//*[@id="post-423"]/div/div/div/div[3]/div[5]/div[2]/div[{i+2}]/div/ul/li/a')
                else: # if self.conference == 'siggraph-asia':
                    links = response.xpath(f'//*[@id="post-423"]/div/div/div/div[3]/div[5]/div[1]/div[{i+2}]/div/ul/li/a')

                for link in links:
                    info_link = link.xpath('@href').get()
                    if info_link.startswith(('https://www.siggraph.org/wp-content/uploads/',
                                             'https://www.siggraph.org/sites/default/files/',
                                             'https://dev.siggraph.org/sites/default/files/')):
                        self.logger.info(f'Found {info_link}')
                        yield scrapy.Request(
                            url=info_link,
                            callback=self.parse_abstract,
                            dont_filter=True
                        )

                break

    def parse_abstract(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        titles = response.xpath('//*[@id="DLcontent"]/h3/a/text()').getall()
        links = response.xpath('//*[@id="DLcontent"]/h3/a/@href').getall()
        abstracts = response.xpath('//*[@id="DLcontent"]/div/div')
        authors = response.xpath('//*[@id="DLcontent"]/ul')

        for title, link, abstract, author_list in zip(titles, links, abstracts, authors):
            abstract_text = ' '.join(t.strip() for t in abstract.xpath('p/text()').getall())
            authors_text = ', '.join(a.strip() for a in author_list.xpath('li/text()').getall())

            if abstract_text.startswith('"') and abstract_text.endswith('"'):
                abstract_text = abstract_text[1:-1].strip()

            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1].strip()

            if '\n' in title:
                title = self.remove_line_breaks(title)

            if '\n' in abstract_text:
                abstract_text = self.remove_line_breaks(abstract_text)

            if '\n' in authors_text:
                authors_text = self.remove_line_breaks(authors_text)

            if len(title) == 0:
                self.logger.warning(f'No title found for {link}')
                continue

            if len(abstract_text) == 0:
                self.logger.warning(f'No abstract found for {title}')
                continue

            if len(authors_text) == 0:
                self.logger.warning(f'No authors found for {title}')
                continue

            if len(link) == 0:
                self.logger.warning(f'No link found for {title}')
                continue

            item = PdfFilesItem()
            item['abstract_url'] = link.replace('https://dl.acm.org/doi/', '')
            item['abstract'] = repr(abstract_text)
            item['authors'] = authors_text.strip()
            item['title'] = title
            item['source_url'] = 11
            yield item
