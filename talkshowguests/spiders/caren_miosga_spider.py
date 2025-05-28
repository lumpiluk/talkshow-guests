import datetime
import re

import scrapy

from talkshowguests.items import GuestItem, TalkshowItem
from talkshowguests.spiders.utils_tvtickets import (
    find_show_in_tickets_page,
)


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

            # Next check the tickets page to see where and when exactly
            # this episode will be recorded:
            yield scrapy.Request(
                "https://tvtickets.de/carenmiosga",
                meta={"talkshow_data": {
                    "name": "Caren Miosga",
                    "isodate": date.isoformat(),
                    "topic": response.css("h1::text").get(),
                    "topic_details": "",
                    "url": response.url,
                    "guests": [GuestItem.from_text(g) for g in guests],
                }},
                callback=self.parse_tickets_page,
                errback=self.on_request_error,
                # Duplicate requests to this page are ok,
                # because we'll request it coming from different episodes:
                dont_filter=True,
            )

        # Follow links to the respective page of each show:
        hrefs = response.css(
            "h3.ressort + .teaser > .headline > a::attr(href)"
        ).getall()
        for href in hrefs:
            yield scrapy.Request(response.urljoin(href), self.parse)

    def parse_tickets_page(self, response):
        if item := find_show_in_tickets_page(
                response,
                recording_location="Berlin Adlershof",
        ):
            yield item
            return

        # Episode not found on the tickets page
        yield TalkshowItem(
            **response.meta["talkshow_data"],
        )

    def on_request_error(self, failure):
        """
        When a request to the tickets page failed,
        we'll just yield as much of the item as we already have.
        """
        self.log(
            f"Request failed, yielding intermediate result; "
            f"url: {failure.request.url}"
        )
        yield TalkshowItem(
            **failure.request.meta["talkshow_data"],
        )
