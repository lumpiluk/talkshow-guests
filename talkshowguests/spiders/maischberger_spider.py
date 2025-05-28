import datetime
import re

import scrapy

from talkshowguests.items import TalkshowItem
from talkshowguests.spiders.utils_tvtickets import (
    find_show_in_tickets_page,
)


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

            # Remove prefix and postfix:
            guest_list = teaser_txt
            match = re.search(
                r"^(?:Zu Gast:|Mit)?"  # prefix
                r"\s*(?P<guest_list>.+?)"
                r"(?:\.?\s*\xa0\|\xa0)?$",  # postfix "\xa0|\xa0"
                guest_list
            )
            if match:
                guest_list = match["guest_list"]

            # The overview page is good for getting the guest list,
            # but it does not list the topics of episodes.
            # -> Pass guest list on to a new request for the episode
            # page
            href = teaser.css(".headline>a::attr(href)").get()
            yield scrapy.Request(
                response.urljoin(href),
                meta={"talkshow_data": {
                    "name": "Maischberger",
                    "guest_list": guest_list,
                    "isodate": date_of_show.isoformat(),
                }},
                callback=self.parse_episode_page,
                errback=self.on_request_error,
            )

    def parse_episode_page(self, response):
        # Maischberger does not seem to list a concise topic
        # for an entire episode. Instead there are usually three
        # paragraphs:
        # 1. "TOPIC A: guests that talk about this topic"
        # 2. "TOPIC B: guests that talk about this topic"
        # 3. "Es kommentieren: more guests"
        # We can't rely on colons as separators between topics
        # and guests here.
        # -> Use the first two paragraphs as topic:
        topic = " ".join(response.css(".con p::text").getall()[:2])

        # Next check the tickets page to see where and when exactly
        # this episode will be recorded:
        yield scrapy.Request(
            "https://tvtickets.de/maischberger-ber.php",
            meta={"talkshow_data": {
                **response.meta["talkshow_data"],
                "topic": topic,
                "topic_details": "",
                "url": response.url,
            }},
            callback=self.parse_tickets_page,
            errback=self.on_request_error,
            # Duplicate requests to this page are ok,
            # because we'll request it coming from different episodes:
            dont_filter=True,
        )

    def parse_tickets_page(self, response, location="Berlin Adlershof"):
        if item := find_show_in_tickets_page(
                response,
                recording_location=location,
        ):
            yield item
            return

        # Eposide not found on this ticket page
        if location == "Berlin Adlershof":
            # We always check the page for Berlin first (parse_episode_page).
            # At this point we didn't find the event there, so try the page
            # for cologne:
            yield scrapy.Request(
                "https://tvtickets.de/maischberger-koe.php",
                meta={"talkshow_data": {
                    **response.meta["talkshow_data"],
                }},
                callback=lambda response: self.parse_tickets_page(
                    response=response,
                    location="Köln WDR Studio"
                ),
                errback=self.on_request_error,
                # Duplicate requests to this page are ok,
                # because we'll request it coming from different episodes:
                dont_filter=True,
            )
        else:
            # Event is neither on the Berlin nor the Cologne ticket page.
            # TalkshowItem without ticket info
            yield TalkshowItem.from_guest_list(
                **response.meta["talkshow_data"],
            )

    def on_request_error(self, failure):
        """
        When a request to a subpage or the tickets page failed,
        we'll just yield as much of the item as we already have.
        """
        self.log(
            f"Request failed, yielding intermediate result; "
            f"url: {failure.request.url}"
        )
        yield TalkshowItem.from_guest_list(
            **failure.request.meta["talkshow_data"],
        )
