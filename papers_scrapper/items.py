# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class PdfFilesItem(scrapy.Item):
    # the name of the field to host url for the file to be
    # downloaded must have name 'file_urls'
    abstract = scrapy.Field()
    abstract_url = scrapy.Field()
    authors = scrapy.Field()
    file_urls = scrapy.Field() # used to download the pdfs
    pdf_url = scrapy.Field()
    source_url = scrapy.Field()
    title = scrapy.Field()
