import argparse
import json

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from .items import TalkshowItem


def main():
    parser = argparse.ArgumentParser()

    args = parser.parse_args()

    settings = get_project_settings()
    settings.set("FEED_FORMAT", "jsonlines")
    settings.set("FEED_URI", "result.jsonlines")

    process = CrawlerProcess(settings)
    for spider in process.spider_loader.list():
        process.crawl(spider)
    process.start()

    with open("result.jsonlines", "r") as f:
        results = [TalkshowItem(**json.loads(line)) for line in f]
        print("\n\n\nHere come the results:")
        print(results)
