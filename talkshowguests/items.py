# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class TalkshowItem(scrapy.Item):
    name = scrapy.Field()
    isodate = scrapy.Field()
    guests = scrapy.Field()
    topic = scrapy.Field()
    topic_details = scrapy.Field()
    url = scrapy.Field()

    def from_guest_list(
        name: str,
        isodate: str,
        topic: str,
        topic_details: str,
        url: str,
        guest_list: str,
    ) -> "TalkshowItem":
        return TalkshowItem(
            name=name,
            isodate=isodate,
            topic=topic,
            topic_details=topic_details,
            url=url,
            guests=TalkshowItem.parse_guest_list(guest_list),
        )

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
        return smart_split(guest_list)
