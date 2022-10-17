# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


import logging
from functools import partial
from pathlib import Path

# useful for handling different item types with a single interface
import scrapy
from scrapy.exporters import CsvItemExporter
from scrapy.pipelines.files import FilesPipeline

from papers_scrapper.items import PdfFilesItem


_logger = logging.getLogger(__name__)


class PdfFilesPipeline(FilesPipeline):
    def file_path(self, request: scrapy.http.Request, response: scrapy.http.Response = None, info: scrapy.pipelines.media.MediaPipeline.SpiderInfo = None, *, item=None):
        file_name = request.url.split("/")[-1]
        return str(Path(info.spider.save_path) / 'papers' / file_name)


class CsvExportPipeline:
    def __init__(self, file_name: str, fields: list[str], delimiter: str=';'):
        self._delimiter = delimiter
        self._file_name = file_name
        self._fields_to_export = fields

    def open_spider(self, spider: scrapy.spiders.Spider):
        paper_infos_path = Path('data') / spider.save_path / self._file_name
        _logger.debug(f'Saving papers\' informations to {paper_infos_path}')

        save_dir = paper_infos_path.parent
        if not save_dir.exists():
            _logger.debug(f'Creating directory {save_dir}')
            save_dir.mkdir(parents=True)

        self.file_handler = open(paper_infos_path, 'wb')
        self.csv_exporter = CsvItemExporter(
            self.file_handler, fields_to_export=self._fields_to_export, delimiter=self._delimiter)
        self.csv_exporter.start_exporting()

    def close_spider(self, spider: scrapy.spiders.Spider):
        self.csv_exporter.finish_exporting()
        self.file_handler.close()

    def process_item(self, item: PdfFilesItem, spider: scrapy.spiders.Spider):
        self.csv_exporter.export_item(item)
        return item


PaperInfoCsvExportPipeline = partial(CsvExportPipeline, file_name='paper_info.csv', fields=['title', 'abstract_url', 'pdf_url'])
PaperAbstractCsvExportPipeline = partial(CsvExportPipeline, file_name='abstracts.csv', fields=['title', 'abstract'], delimiter='|')
PaperAuthorsCsvExportPipeline = partial(CsvExportPipeline, file_name='authors.csv', fields=['title', 'authors'])

