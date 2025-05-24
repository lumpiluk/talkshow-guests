import json
import re
import sys

import scrapy

from talkshowguests.items import GuestItem, TalkshowItem


class MarkusLanzSpider(scrapy.Spider):
    name = "markuslanz"

    start_urls = [
        "https://www.zdf.de/talk/markus-lanz-114",
    ]

    def parse(self, response):
        # All relevant content is included in many <script>
        # elements at the end of the page:
        script_elems = response.css("script::text")

        re_guests = re.compile(
            r"Unsere Gäste am.*, \d+"
            r"(.*)"
            r"paragraph-content-aggregator"
        )
        for script_elem in script_elems:
            script_data = self.parse_script_text(script_elem.get())
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
                    isodate=episode_obj.get("editorialDate"),
                    topic=episode_obj.get("teaser", {}).get("description"),
                    topic_details="",
                    url=response.url,
                    guests=guests,
                )

    @staticmethod
    def parse_script_text(text: str) -> dict:
        match = re.search(
            r'self\.__next_f\.push\('
            r'\[1,"[a-z0-9]+:'  # \[
            r'(.*?)'
            r'"\]\);?',  # has to be closed by a `])`
            text,
            re.DOTALL,  # make `.` also match newlines
        )
        if not match:
            return {}
        escaped_json = match.group(1)
        unescaped_json = json.loads(f'"{escaped_json}"')

        try:
            return json.loads(unescaped_json)
        except json.JSONDecodeError as e:
            return {}

