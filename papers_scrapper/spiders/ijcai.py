import scrapy
# from scrapy.shell import inspect_response

from .base_spider import BaseSpider
from ..items import PdfFilesItem

# https://coderecode.com/download-files-scrapy/
# https://docs.scrapy.org/en/latest/topics/spiders.html

# starts-with(@id,'paper')
# //*[starts-with(@id,'paper')]
class IJCAISpider(BaseSpider):
    name = 'ijcai'
    allowed_domains = ['www.ijcai.org/']
    start_urls = ['https://www.ijcai.org/']

    def __init__(self, year: str=''):
        BaseSpider.__init__(self, 'ijcai', year)

    def start_requests(self):
        #TODO verify why it is not calling parse automatically
        for url in self.start_urls:
            main_track = f'{url}proceedings/{self.year}/'
            self.logger.info(
                f'Start scraping {main_track} for {self.year}')
            yield scrapy.Request(url=main_track, callback=self.parse)

    def parse(self, response: scrapy.http.TextResponse):
        # inspect_response(response, self)
        papers = response.xpath('//*[starts-with(@id,"paper")]')
        for paper in papers:
            title = paper.xpath('div[1]/text()').get().strip()
            file_url = paper.xpath('div[3]/a[1]/@href').get()
            abstract_link = paper.xpath('div[3]/a[2]/@href').get()

            # "/proceedings/2021/1"

            item = PdfFilesItem()
            item['abstract_url'] = abstract_link.replace(f'/proceedings/{self.year}/', '')
            item['file_urls'] = [response.urljoin(file_url)] # used to download pdf
            item['pdf_url'] = file_url

            item['title'] = title
            item['title'] = self.clean_html_tags(item['title'])
            item['title'] = self.clean_extra_whitespaces(item['title'])
            item['title'] = self.clean_quotes(item['title'])

            subpage_url = response.urljoin(abstract_link)
            self.logger.debug(f'Found abstract link for {title}: {subpage_url}')

            yield scrapy.Request(
                url=subpage_url,
                callback=self.parse_abstract,
                dont_filter=True,
                meta={'item': item}
            )

    def parse_abstract(self, response: scrapy.http.TextResponse):
        item = response.meta['item']
        abstract = response.xpath('//*[@id="block-system-main"]/div/div/div[3]/div[1]/text()').get()
        if abstract is None:
            self.logger.warning(f'No abstract found for "{item["title"]}": {item["abstract_url"]}')
            return

        abstract = abstract.strip()
        abstract = self.clean_quotes(abstract)

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
        item['authors'] = response.xpath('//*[@id="block-system-main"]/div/div/div[1]/div[1]/h2/text()').get().strip()
        item['source_url'] = 4

        yield item
