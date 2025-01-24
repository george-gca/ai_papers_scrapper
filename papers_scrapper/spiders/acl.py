import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem

# https://coderecode.com/download-files-scrapy/
# https://docs.scrapy.org/en/latest/topics/spiders.html


class ACLSpider(BaseSpider):
    name = 'acl'
    allowed_domains = ['aclanthology.org/']
    start_urls = ['https://aclanthology.org/']

    def __init__(self, conference: str='', year: str=''):
        BaseSpider.__init__(self, conference, year)

    def start_requests(self):
        #TODO verify why it is not calling parse automatically
        if self.conference.lower().startswith('sig'):
            conference_type = 'sigs'
        else:
            conference_type = 'venues'

        for url in self.start_urls:
            main_track = f'{url}{conference_type}/{self.conference.lower()}/'
            self.logger.info(
                f'Start scraping {main_track} for {self.year}')
            yield scrapy.Request(url=main_track, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        years = response.xpath('//*[@id="main"]/div/div/div[1]/h4/a/text()').getall()
        if len(years) == 0:
            years = response.xpath('//*[@id="main"]/div/div/div[1]/h4/text()').getall()

        for i, year in enumerate(years):
            if year == self.year:
                links = response.xpath(f'//*[@id="main"]/div/div[{i+1}]/div[2]/ul/li/a/@href').getall()
                for link in links:
                    subpage_url = response.urljoin(link)
                    self.logger.debug(f'Found {subpage_url}')
                    yield scrapy.Request(
                        url=subpage_url,
                        callback=self.parse_subpage,
                        dont_filter=True
                    )

    def parse_subpage(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        links = response.xpath('//*[@id="main"]/div[2]/p/span[2]/strong/a')
        for link in links:
            title = link.xpath('.//text()').getall()
            title = ''.join(title).strip()
            if title.startswith('"') and title.endswith('"'):
                title = title[1:-1].strip()

            lower_title = title.strip().lower()
            if not lower_title.startswith('proceedings of ') and not lower_title.startswith('transactions of ') \
                and not lower_title.startswith('findings of '):

                abstract_link = link.xpath('@href').get()
                abstract_url = response.urljoin(abstract_link)
                item = PdfFilesItem()
                if abstract_link.startswith('/'):
                    abstract_link = abstract_link[1:]
                if abstract_link.endswith('/'):
                    abstract_link = abstract_link[:-1]
                item['abstract_url'] = abstract_link
                item['title'] = title
                self.logger.debug(f'Found abstract link for {title}: {abstract_url}')

                yield scrapy.Request(url=abstract_url,
                                    callback=self.parse_abstract,
                                    dont_filter=True,
                                    meta={'item': item})

    def parse_abstract(self, response: scrapy.http.TextResponse):
        item = response.meta['item']
        file_url = response.xpath('//*[@id="main"]/div[1]/div[2]/a[1]/@href').get()

        if file_url is None:
            file_url = response.xpath('//*[@id="main"]/div[2]/div[2]/a[1]/@href').get()

            if file_url is None:
                file_url = response.xpath('//*[@id="main"]/div[3]/div[2]/a[1]/@href').get()

        if file_url is None or len(file_url) < 5:
            self.logger.warning(f'No PDF found for "{item["title"]}": {item["abstract_url"]}')
            return

        item['file_urls'] = [file_url] # used to download pdf
        item['pdf_url'] = file_url.replace('https://aclanthology.org/', '')

        abstract = response.xpath('//*[@id="main"]/div[1]/div[1]/div/div/text()').get()

        if abstract is None:
            abstract = response.xpath('//*[@id="main"]/div[2]/div[1]/div/div/span').get()

            if abstract is None:
                abstract = response.xpath('//*[@id="main"]/div[3]/div[1]/div/div/span').get()

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

        authors = response.xpath('//*[@id="main"]/div[1]/p/a/text()').getall()
        item['authors'] = ', '.join(authors).strip()

        self.logger.debug(f'Abstract text: {abstract}')
        # might contain \r in abstract text, like \rightarrow
        item['abstract'] = repr(abstract)
        item['source_url'] = 2
        yield item
