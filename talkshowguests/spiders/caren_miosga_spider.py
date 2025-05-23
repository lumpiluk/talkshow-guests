import datetime
import re

import scrapy

from talkshowguests.items import GuestItem, TalkshowItem


class CarenMiosgaSpider(scrapy.Spider):
    name = "carenmiosga"

    start_urls = [
        "https://www.daserste.de/information/talk/caren-miosga/sendung/index.html",  # noqa: E501
    ]

    def parse(self, response):
        if (
                not response.css("head > title::text").get().startswith(
                    "Alle Sendungen")
        ):
            # We are on the page of a specific show, not the overview.
            guests: list[str] = [
                re.search(r"(.*)(?:\xa0\|\xa0.*)", info_txt).group(1)
                if "\xa0|\xa0" in info_txt
                else info_txt
                for info_txt
                in response.css(".mediaLeft .infotext::text").getall()
            ]
            date_match = re.search(
                r"(\d+.\d+.\d+)",
                response.css(".infoBroadcastDateBox p::text").get()
            )
            if date_match:
                date = datetime.datetime.strptime(
                    date_match.group(1),
                    "%d.%m.%y"
                )
            else:
                date = datetime.datetime.fromisoformat("1970-01-01")
            yield TalkshowItem(
                name="Caren Miosga",
                isodate=date.isoformat(),
                topic=response.css("h1::text").get(),
                topic_details="",  # TODO
                url=response.url,
                guests=[GuestItem.from_text(g) for g in guests],
            )

        # Follow links to the respective page of each show:
        hrefs = response.css(
            "h3.ressort + .teaser > .headline > a::attr(href)"
        ).getall()
        for href in hrefs:
            yield scrapy.Request(response.urljoin(href), self.parse)
