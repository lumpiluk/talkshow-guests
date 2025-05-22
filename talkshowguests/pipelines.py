# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import datetime


# useful for handling different item types with a single interface
# from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem


class TalkshowguestsPipeline:
    def process_item(self, item, spider):
        date = datetime.datetime.fromisoformat(item["isodate"])
        # if (datetime.datetime.now() - date).days > 0:
        #     raise DropItem(f"Date is in the past: {date}")
        return item
