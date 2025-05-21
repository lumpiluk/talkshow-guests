import re

import scrapy

from talkshowguests.items import TalkshowItem


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
            r"Unsere Gäste am.*, \d+.*\\\""
            r"\.*text\\\":\\\""
            r"(.*)"
            r"paragraph-content-aggregator"
        )
        for script_elem in script_elems:
            # Usually there seems to be only one of these
            # "Unsere Gäste am" blocks on the "Details" tab,
            # i.e., only for the newest episode.
            for guests_match in re_guests.finditer(script_elem.get()):
                guests: list[str] = re.findall(
                    r"\\u003cstrong\\u003e"  # escaped "<strong>"
                    r"([^\\]*)"  # anything that's not a '\'
                    r"\\u003c/strong\\u003e",  # "</strong>"
                    guests_match.group()
                )
                potential_dates = re.findall(
                    r"editorialDate\\\":\\\"(\d+-\d+-\d+)",
                    script_elem.get()[:guests_match.start()]
                )
                yield TalkshowItem(
                    name="Markus Lanz",
                    # Find the last "editorialDate" before the
                    # guest list:
                    isodate=(
                        potential_dates[-1]
                        if potential_dates else "1970-01-01"
                    ),
                    guests=guests,
                )
