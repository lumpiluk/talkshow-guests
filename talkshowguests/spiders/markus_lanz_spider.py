import json
import re

import scrapy

from talkshowguests.items import GuestItem, TalkshowItem
from talkshowguests.spiders.utils_zdf import parse_script_text


class MarkusLanzSpider(scrapy.Spider):
    name = "markuslanz"

    start_urls = [
        "https://www.zdf.de/talk/markus-lanz-114",
    ]

    parse = lambda self, response: parse_zdf(
        self,
        response,
        name_of_show="Markus Lanz",
    )

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
                    # ^ We could also parse this, but better be safe
                    isodate=episode_obj.get("editorialDate"),
                    topic=episode_obj.get("teaser", {}).get("description"),
                    topic_details="",
                    url=response.url,
                    guests=guests,
                )


