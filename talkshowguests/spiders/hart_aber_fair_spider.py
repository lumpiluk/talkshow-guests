import datetime
import re

import scrapy

from talkshowguests.items import GuestItem, TalkshowItem


def strip(text: str) -> str:
    if not text:
        return ""
    return text.replace("\n", "").replace("\xa0|\xa0", "")


class HartAberFairSpider(scrapy.Spider):
    name = "hartaberfair"

    start_urls = [
        "https://www1.wdr.de/daserste/hartaberfair/index.html",
    ]

    def parse(self, response):
        # Hart aber Fair seems to always highlight the latest episode only,
        # which makes it easy for us.
        date_match = re.search(
            r"(\d+.\d+.\d+)",
            # There are multiple "h2.conHeadline"s, but only the first
            # contains the date:
            response.css("h2.conHeadline::text").get()
        )
        if date_match:
            date = datetime.datetime.strptime(
                date_match.group(1),
                "%d.%m.%Y"
            )
        else:
            date = datetime.datetime.fromisoformat("1970-01-01")

        guests: list[GuestItem] = []
        for section in response.css(".sectionA"):
            if strip(section.css(".conHeadline::text").get()) != "Gäste":
                continue
            guests = list({
                GuestItem.from_text(strip(guest))
                for guest
                in section.css(".box h4.headline::text").getall()
            })

        topic = ""
        for section in response.css(".sectionA"):
            sec_headline = strip(section.css(".conHeadline::text").get())
            if sec_headline.startswith("Sendung vom"):
                topic = strip(section.css(".teaser>a::attr(title)").get())
                self.log(f"{topic=}")
                break

        yield TalkshowItem(
            name="Hart aber fair",
            isodate=date.isoformat(),
            topic=topic,
            topic_details=strip(response.css(
                ".teaser .programInfo + p.teasertext::text"
            ).get()),
            url=response.urljoin(
                response.css(".teaser>a::attr(href)").get()
            ),
            guests=guests,
        )
