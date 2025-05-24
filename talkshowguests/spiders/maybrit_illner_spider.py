import scrapy

from talkshowguests.spiders.utils_zdf import parse_script_text, parse_zdf


class MaybritIllnerSpider(scrapy.Spider):
    name = "maybritillner"

    start_urls = [
        "https://www.zdf.de/talk/maybrit-illner-128",
    ]

    parse = lambda self, response: parse_zdf(
        self,
        response,
        name_of_show="Maybrit Illner",
    )
