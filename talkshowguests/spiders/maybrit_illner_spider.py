import re

import scrapy

from talkshowguests.items import GuestItem, TalkshowItem
from talkshowguests.spiders.utils_zdf import (
    get_episodes_from_zdf_page,
)


class MaybritIllnerSpider(scrapy.Spider):
    name = "maybritillner"

    start_urls = [
        "https://www.zdf.de/talk/maybrit-illner-128",
    ]

    def parse(self, response):
        for episode_obj in get_episodes_from_zdf_page(
                response, debug_dump_json=False):
            guests = []
            info_paragraph_objs = episode_obj.get(
                "longInfoText", {}).get(
                "items", [{}])[0].get(
                "paragraph")
            has_guest_list = (
                "Zu Gast" in info_paragraph_objs[0].get("text")
                or "Die Gäste" in info_paragraph_objs[0].get("text")
            )
            # If there is a guest list, it's usually in the second
            # paragraph in the form of a HTML <ul>.
            if has_guest_list:
                guests = [
                    GuestItem.from_text(guest)
                    for guest
                    in re.findall(
                        r"<li>(.*?)</li>",
                        info_paragraph_objs[1].get("text")
                    )
                ]
            topic = ""
            # The topic can appear in any of the paragraphs;
            # often it's the last or second-to-last one,
            # sometimes it's none.
            # If there is one, it usually ends with "ZDF"
            for info_paragraph_obj in info_paragraph_objs:
                topic_match = re.search(
                    r"(?:(?:\"|\u201e)maybrit illner(?:\"|\u201c) "
                    r"mit dem Thema )?"
                    r"(?:\"|\u201e)"
                    r"(.*?)"
                    r"(\"|\u201c)"
                    r".*?um \d+:\d+ Uhr im ZDF",
                    info_paragraph_objs[-1].get("text")
                )
                if topic_match:
                    topic = topic_match.group(1)
                    break
            yield TalkshowItem(
                name="Maybrit Illner",
                isodate=episode_obj.get("editorialDate").split("T")[0],
                # ^ editorialDate is sometimes used for the time when an
                # episode airs, and sometimes for when some text has been
                # edited. For lack of an alternative, we'll just truncate
                # the time and use the date only.
                topic=topic,
                topic_details="",
                url=response.url,
                guests=guests,
            )
