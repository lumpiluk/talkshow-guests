import scrapy

from talkshowguests.spiders.utils_zdf import parse_script_text


class MaybritIllnerSpider(scrapy.Spider):
    name = "maybritillner"

    start_urls = [
        "https://www.zdf.de/talk/maybrit-illner-128",
    ]

    def parse(self, response):
        pass
