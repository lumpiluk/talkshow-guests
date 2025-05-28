# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import re

import scrapy


_COMPARE_IGNORE_KEYS = {
    "reported_on",  # added to dict in __main__.py
    "update_history",  # same, if episode was updated
    "diff_keys",  # same
}

_GUEST_LIST_AFFILIATION_KEYWORDS = {
    "AfD",
    "B‘90/Grüne",
    "B‘90/Die Grünen",
    "B'90/Grüne",
    "B'90/Die Grünen",
    "BSW",
    "Bündnis 90/Die Grünen",
    "Bündnis 90/Grüne",
    "CDU",
    "CSU",
    "Die Grünen",
    "Die Linke",
    "FDP",
    "Grüne",
    "Linke",
    "SPD",
}
"""Used to distinguish between affiliation and guest name"""


class GuestItem(scrapy.Item):
    name: str = scrapy.Field()
    affiliation: str = scrapy.Field()

    def __lt__(self, other):
        return (
            self["name"] + self["affiliation"]
            < other["name"] + other["affiliation"]
        )

    @staticmethod
    def from_text(text: str) -> "GuestItem":
        """
        Convert text to a GuestItem.

        Guests are often written as:
        - "FIRSTNAME LASTNAME"
        - "FIRSTNAME LASTNAME (AFFILIATION)"
        - "FIRSTNAME LASTNAME, AFFILIATION"
        - "FIRSTNAME LASTNAME (AFFILIATION 1), AFFILIATION 2" (Illner...)
        - "FIRSTNAME LASTNAME, AFFILIATION 1 (AFFILIATION 2)" (Maischberger...)
        """
        m = re.match(
            r"^(?P<name>[^\(,]+?)"
            r"(?:\s+\((?P<paren_affiliation>[^)]+)\))?"
            r"(?:,\s*(?P<comma_affiliation>[^\(]+)"
            r"(?:\s+\((?P<paren_in_comma_affiliation>[^\)]+)\))?"
            r")?$",
            text
        )
        if m:
            name = m["name"]
            affiliation = m["paren_affiliation"] or ""
            if m["paren_affiliation"] and m["comma_affiliation"]:
                affiliation += ", " + m["comma_affiliation"] or ""
            elif m["comma_affiliation"]:
                affiliation = m["comma_affiliation"] or ""
                if m["paren_in_comma_affiliation"]:
                    affiliation += f", {m["paren_in_comma_affiliation"]}"
        else:
            name = text
            affiliation = ""
        return GuestItem(
            name=GuestItem._strip_text(name),
            affiliation=GuestItem._strip_text(affiliation),
        )

    @staticmethod
    def _strip_text(text: str) -> str:
        return text.replace(
            "<strong>", "").replace(
            "</strong>", "").replace(
            "\xa0", " ").strip()


class RecordingInfoItem(scrapy.Item):
    location: str = scrapy.Field()
    tickets_available: bool = scrapy.Field()
    doors: str = scrapy.Field()
    """Time when people may enter"""
    tickets_url: str = scrapy.Field()


class TalkshowItem(scrapy.Item):
    name: str = scrapy.Field()
    isodate: str = scrapy.Field()
    guests: list[GuestItem] = scrapy.Field()
    topic: str = scrapy.Field()
    topic_details: str = scrapy.Field()
    url: str = scrapy.Field()
    recording_info: RecordingInfoItem = scrapy.Field()

    # Optional fields used only for items that we've already
    # reported on:
    reported_on = scrapy.Field()
    update_history = scrapy.Field()
    diff_keys = scrapy.Field()

    def eq_with_ignore(self, other):
        """Same as `==`, but ignores irrelevant keys."""
        # (We cannot override __eq__ because then we'd also
        # have to override __hash__ and that doesn't seem to
        # work well with scrapy Items since hash() appears to
        # be called before the item's fields are initialized.)
        for key in set(self.keys()) - _COMPARE_IGNORE_KEYS:
            if key not in other:
                return False
            if self[key] != other[key]:
                return False
        return True

    def get_diff_keys(self, other):
        return [
            key
            for key in set(self.keys()) - _COMPARE_IGNORE_KEYS
            if (key in self and key not in other)
            or (key in other and key not in self)
            or self[key] != other[key]
        ]

    @staticmethod
    def from_guest_list(
        guest_list: str,
        **kwargs,
    ) -> "TalkshowItem":
        return TalkshowItem(
            guests=TalkshowItem.parse_guest_list(guest_list),
            **kwargs,
        )

    @staticmethod
    def parse_guest_list(guest_list: str) -> list[str]:
        """
        Guests lists may look like this:
        "Marie-Agnes Strack-Zimmermann (FDP), Jan van Aken (Die Linke),
        Eckart von Hirschhausen (Arzt & Wissenschaftsjournalist),
        Amelie Fried (Autorin & Journalistin),
        Daniel Friedrich Sturm (Der Tagesspiegel) und
        Yasmine M’Barek (Zeit Online)"

        So we have to separate by commas and by the word "und",
        but only if it's outside of parentheses.

        In some unfortunately-not-rare cases, guest lists may also
        look like this:
        "Zu Gast: Markus Söder, CSU (bayerischer Ministerpräsident),
        Klaus von Dohnanyi, SPD (langjähriger Spitzenpolitiker),
        Béla Réthy (Sportjournalist), Dagmar Rosenfeld (Media Pioneer)
        und Sonja Zekri (Süddeutsche Zeitung)."
        """
        def smart_split(s):
            # With help from ChatGPT :S
            parts = []
            buf = ''
            parens = 0
            i = 0
            while i < len(s):
                if s[i] == '(':
                    parens += 1
                elif s[i] == ')':
                    parens -= 1
                # Check for ", " outside parentheses
                if parens == 0 and s[i:i+2] == ', ':
                    parts.append(buf.strip())
                    buf = ''
                    i += 2
                    continue
                # Check for " und " outside parentheses
                elif parens == 0 and s[i:i+5] == ' und ' and i + 5 < len(s):
                    # Peek ahead to ensure it's the last separator
                    # (no more commas)
                    if ',' not in s[i+5:]:
                        parts.append(buf.strip())
                        buf = ''
                        i += 5
                        continue
                buf += s[i]
                i += 1
            if buf:
                parts.append(buf.strip())
            return parts

        def is_affiliation(item: str):
            return (
                item.split("(")[0].strip()
                in _GUEST_LIST_AFFILIATION_KEYWORDS
            )

        guest_list_split = smart_split(guest_list)

        # Using a dict with keys only as an ordered set so we don't have
        # to sort and thus mangle the order of the guests.
        return list({
            (
                GuestItem.from_text(first)
                if second is None or not is_affiliation(second)
                else GuestItem.from_text(f"{first}, {second}")
            ): None
            for (first, second)
            in zip(guest_list_split, guest_list_split[1:] + [None])
            if not is_affiliation(first)
        }.keys())
