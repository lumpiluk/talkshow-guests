import json
import re

import scrapy

from talkshowguests.items import GuestItem, TalkshowItem
from talkshowguests.spiders.utils_zdf import (
    get_episodes_from_zdf_page,
)


class MarkusLanzSpider(scrapy.Spider):
    name = "markuslanz"

    start_urls = [
        "https://www.zdf.de/talk/markus-lanz-114",
    ]

    def parse(self, response):
        for episode_obj in get_episodes_from_zdf_page(response):
            guest_paragraph_objs = episode_obj.get(
                "longInfoText", {}).get(
                "items", [{}])[0].get(
                "paragraph")
            guests = [
                GuestItem.from_text(m.group(1))
                for par in guest_paragraph_objs
                for m in [re.search(
                    r"<strong>(.*?)</strong>",
                    par.get("text", ""))
                ]
                if m  # only include if there's a match
            ]
            yield TalkshowItem(
                name="Markus Lanz",
                isodate=episode_obj.get("editorialDate"),
                topic=episode_obj.get("teaser", {}).get("description"),
                topic_details="",
                url=response.url,
                guests=guests,
            )
