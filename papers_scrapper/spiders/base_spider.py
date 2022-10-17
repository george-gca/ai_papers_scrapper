import re
from os import path

from scrapy.spiders import CrawlSpider


class BaseSpider(CrawlSpider):
    def __init__(self):
        html_regex = [
            '<b>',
            '<strong>',
            '<i>',
            '<em>',
            '<mark>',
            '<small>',
            '<del>',
            '<ins>',
            '<sub>',
            '<sup>',
            '</b>',
            '</strong>',
            '</i>',
            '</em>',
            '</mark>',
            '</small>',
            '</del>',
            '</ins>',
            '</sub>',
            '</sup>',
        ]

        self._html_regex = re.compile('|'.join(html_regex))
        self._special_chars_regex = re.compile('[\s]*<(/)?[\w\s_\-\−\–=\"]+(/)?>[\s]*')

    def clean_html_tags(self, text: str) -> str:
        # remove html tags
        text = self._html_regex.sub('', text)
        return self._special_chars_regex.sub(' ', text).strip()

    def clean_extra_whitespaces(self, text: str) -> str:
        text = [t for t in text.split('\n') if len(t.strip()) > 0]
        text = ' '.join(text).strip()
        text = [t for t in text.split() if len(t.strip()) > 0]
        return ' '.join(text).strip()
