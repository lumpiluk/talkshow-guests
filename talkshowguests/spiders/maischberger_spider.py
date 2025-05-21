import datetime
from pathlib import Path
import re

import scrapy

from talkshowguests import Talkshow


class MaischbergerSpider(scrapy.Spider):
    name = "maischberger"

    start_urls = [
        "https://www.daserste.de/information/talk/maischberger/sendung/index.html",  # noqa: E501
    ]

    def parse(self, response):
        teasers = response.css(".teaser")
        for teaser in teasers:
            title = teaser.css(".headline>a::text").get()
            teaser_txt = teaser.css(".teasertext>a::text").get()
            title_match = re.search(
                r"^[mM]aischberger am (?P<date>\d+.\d+.\d+)",
                title
            )
            if not title_match:
                continue
            date_of_show = datetime.datetime.strptime(
                title_match["date"],
                "%d.%m.%Y"
            )
            if (datetime.datetime.now() - date_of_show).days > 0:
                # Skip if date is in the past
                continue

            guest_list = teaser_txt
            # Remove prefix and postfix:
            self.log(f"{teaser_txt=}")
            match = re.search(
                r"^(?:Zu Gast:|Mit)?"  # prefix
                r"\s*(?P<guest_list>.+?)"
                r"(?:\.?\s*\xa0\|\xa0)?$",  # postfix
                guest_list
            )
            if match:
                guest_list = match["guest_list"]

            yield Talkshow.from_guest_list(
                name="Maischberger",
                isodate=date_of_show.isoformat(),
                guest_list=guest_list,
            )
