import json
import re

import scrapy

from talkshowguests.items import GuestItem, RecordingInfoItem, TalkshowItem
from talkshowguests.spiders.utils_zdf import (
    get_episodes_from_zdf_page,
)


class MarkusLanzSpider(scrapy.Spider):
    name = "markuslanz"

    start_urls = [
        "https://www.zdf.de/talk/markus-lanz-114",
    ]

    def parse(self, response):
        for episode_obj in get_episodes_from_zdf_page(
                response, debug_dump_json=False):
            guest_paragraph_objs = episode_obj.get(
                "longInfoText", {}).get(
                "items", [{}])[0].get(
                "paragraph")
            guests = [
                GuestItem.from_text(m)
                for par in guest_paragraph_objs
                for m in re.findall(
                    r"<(?:strong|b)>(.*?)</(?:strong|b)>",
                    par.get("text", "")
                )
            ]
            yield TalkshowItem(
                name="Markus Lanz",
                isodate=episode_obj.get("editorialDate").split("T")[0],
                # ^ editorialDate is sometimes used for the time when an
                # episode airs, and sometimes for when some text has been
                # edited. For lack of an alternative, we'll just truncate
                # the time and use the date only.
                topic=episode_obj.get("teaser", {}).get("description"),
                topic_details="",
                url=response.url,
                guests=guests,
                recording_info=RecordingInfoItem(
                    location="Schützenstraße 15, 22761 Hamburg",
                    tickets_available=None,
                    doors="Ohne Publikum",
                    # According to Wikipedia,
                    # recorded some hours before it airs
                    tickets_url=None,
                ),
            )
