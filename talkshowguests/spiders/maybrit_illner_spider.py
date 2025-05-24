import json
import re

import scrapy

from talkshowguests.items import GuestItem, TalkshowItem
from talkshowguests.spiders.utils_zdf import parse_script_text


class MaybritIllnerSpider(scrapy.Spider):
    name = "maybritillner"

    start_urls = [
        "https://www.zdf.de/talk/maybrit-illner-128",
    ]

    def parse(self, response):
        # All relevant content is included in many <script>
        # elements at the end of the page:
        script_elems = response.css("script::text")

        for script_elem in script_elems:
            script_data = parse_script_text(script_elem.get())
            if not script_data:
                continue

            # Useful if you want to inspect the json objects:
            # with open(f"debug_script-data_{hash(script_elem)}.json", "w") as f:
            #     json.dump(script_data, f, indent=2)

            try:
                season_objs: list[dict] = script_data[0][
                    "result"]["data"][
                    "smartCollectionByCanonical"][
                    "seasons"][
                    "nodes"]
            except (KeyError, TypeError):
                # Probably not the script_elem we are looking for
                continue
            episode_objs: list[dict] = [
                ep
                for season_obj in season_objs
                for ep in season_obj["episodes"]["nodes"]
            ]

            for episode_obj in episode_objs:
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
                    isodate=episode_obj.get("editorialDate"),
                    topic=topic,
                    topic_details="",
                    url=response.url,
                    guests=guests,
                )

