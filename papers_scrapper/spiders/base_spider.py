import re
from pathlib import Path

from scrapy.spiders import CrawlSpider


class BaseSpider(CrawlSpider):
    def __init__(self, conference: str, year: str):
        html_regex = [
            '</b>',
            '</del>',
            '</div>',
            '</em>',
            '</i>',
            '</ins>',
            '</mark>',
            '</small>',
            '</strong>',
            '</sub>',
            '</sup>',
            '<b>',
            '<del>',
            '<div>',
            '<em>',
            '<i>',
            '<ins>',
            '<mark>',
            '<small>',
            '<strong>',
            '<sub>',
            '<sup>',
        ]

        self._html_regex = re.compile('|'.join(html_regex))
        self._html_with_attributes_regex = re.compile(r'<[\w\s_\-\−\–=\"]+>')
        self._special_chars_regex = re.compile('[\s]*<(/)?[\w\s_\-\−\–=\"]+(/)?>[\s]*')

        self.conference = conference
        self.year = year
        self.save_path = Path(conference.lower()) / year

    def clean_html_tags(self, text: str) -> str:
        # remove html tags
        text = self._html_with_attributes_regex.sub('', text)
        text = self._html_regex.sub('', text)
        return self._special_chars_regex.sub(' ', text).strip()

    def clean_extra_whitespaces(self, text: str) -> str:
        text = ' '.join(t for t in text.split('\n') if len(t.strip()) > 0).strip()
        return ' '.join(t for t in text.split() if len(t.strip()) > 0).strip()

    def clean_quotes(self, text: str) -> str:
        while (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
            text = text[1:-1].strip()
        return text

    def remove_line_breaks(self, text: str) -> str:
        return ' '.join(t.strip() for t in text.split())
