import json
import re

import scrapy

from talkshowguests.items import GuestItem, TalkshowItem
from talkshowguests.spiders.utils_zdf import parse_script_text, parse_zdf


class MarkusLanzSpider(scrapy.Spider):
    name = "markuslanz"

    start_urls = [
        "https://www.zdf.de/talk/markus-lanz-114",
    ]

    parse = lambda self, response: parse_zdf(
        self,
        response,
        name_of_show="Markus Lanz",
    )


