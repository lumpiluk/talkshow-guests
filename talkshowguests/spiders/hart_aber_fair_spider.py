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
        next_talkshow_item = None
        for section in response.css(".sectionA"):
            if not section.css("h2.conHeadline"):
                continue
            date_match = re.search(
                r"(\d+.\d+.\d+)",
                section.css("h2.conHeadline::text").get()
            )
            if date_match:
                if next_talkshow_item is not None:
                    # There is another talkshow item we haven't yielded yet
                    # (i.e., a talkshow item without guests)
                    # -> yield before overwriting
                    yield next_talkshow_item
                next_talkshow_item = TalkshowItem(
                    name="Hart aber fair",
                    isodate=datetime.datetime.strptime(
                        date_match.group(1),
                        "%d.%m.%Y"
                    ).isoformat(),
                    topic=strip(section.css(".teaser>a::attr(title)").get()),
                    topic_details=strip(response.css(
                        ".teaser .programInfo + p.teasertext::text"
                    ).get()),
                    url=response.urljoin(
                        response.css(".teaser>a::attr(href)").get()
                    ),
                    guests=[],  # to be overwritten
                )
                # Guests are usually in the subsequent section
            elif strip(section.css(".conHeadline::text").get()) == "Gäste":
                # Use a dict with keys only as an ordered set:
                guest_strs = list({
                    strip(guest): None
                    for guest
                    in section.css(".box h4.headline::text").getall()
                }.keys())
                next_talkshow_item["guests"] = [
                    GuestItem.from_text(strip(guest_str))
                    for guest_str in guest_strs
                ]
                yield next_talkshow_item
                next_talkshow_item = None
            elif next_talkshow_item is not None:
                # The section immediately following the teaser section
                # did not contain a guest list -> yield item without
                # a guest list
                yield next_talkshow_item
                next_talkshow_item = None
