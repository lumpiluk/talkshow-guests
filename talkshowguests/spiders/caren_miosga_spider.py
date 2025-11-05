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
        "https://www.ndr.de/fernsehen/sendungen/caren-miosga/rueckschau",  # noqa: E501
    ]

    def parse(self, response):
        if (
                "Sendungen im Überblick" not in
                response.css("head > title::text").get()
        ):
            # We are on the page of a specific show, not the overview.
            guests: list[str] = [
                it.css("::text").get()
                for it in response.css("h2")
                if it.css("::attr(id)")
            ]
            date = datetime.datetime.fromisoformat(
                response.css(
                    "header span[itemprop='startDate']::attr(content)"
                ).get()
            )

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
            ".teaser h2 > a::attr(href)"
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
