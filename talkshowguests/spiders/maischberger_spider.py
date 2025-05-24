import datetime
import re

import scrapy

from talkshowguests.items import TalkshowItem


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
                meta={
                    "guest_list": guest_list,
                    "isodate": date_of_show.isoformat(),
                },
                callback=self.parse_episode_page,
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
        yield TalkshowItem.from_guest_list(
            name="Maischberger",
            isodate=response.meta["isodate"],
            # First paragraph should contain the topic:
            topic=topic,
            topic_details="",  # Would be the same as topic here
            url=response.url,
            guest_list=response.meta["guest_list"],
        )
