# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class TalkshowguestsPipeline:

    def __init__(self):
        self.names_and_dates_seen = set()

    def process_item(self, item, spider):
        # date = datetime.datetime.fromisoformat(item["isodate"])
        # if (datetime.datetime.now() - date).days > 0:
        #     raise DropItem(f"Date is in the past: {date}")
        # ^ We'll do that in postprocessing, because we also
        #   want to check if any of the spiders didn't return
        #   any results at all.
        if (item["name"], item["isodate"]) in self.names_and_dates_seen:
            raise DropItem(f"Duplicate item: {item}")
        self.names_and_dates_seen.add((
            item["name"], item["isodate"]
        ))
        return item
