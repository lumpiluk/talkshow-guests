import argparse
import copy
import datetime
import json
import os
import pathlib

from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from .items import TalkshowItem
from .reports.telegram import report_episodes_telegram


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--crawler-results",
        type=pathlib.Path,
        help="Output json (jsonlines) path for crawler results",
        default="latest-result.jsonlines",
    )
    parser.add_argument(
        "--history-file",
        type=pathlib.Path,
        help="Path to a history file of previously "
             "reported talkshows. Will be created if it "
             "does not yet exist.",
        default=pathlib.Path("history.json"),
    )
    parser.add_argument(
        "--report-telegram",
        action="store_true",
        help="Report via Telegram bot. "
             "Requires the following environment variables: "
             "TELEGRAM_API_TOKEN, TELEGRAM_CHAT_ID",
    )
    args = parser.parse_args()

    # Environment variables can be either passed as regular
    # environment variables or as a .env file in the same
    # folder:
    load_dotenv()

    settings = get_project_settings()
    settings.set("FEED_FORMAT", "jsonlines")
    settings.set("FEED_URI", str(args.crawler_results))
    # Clear previous results because 'jsonlines' seems to append:
    args.crawler_results.unlink(missing_ok=True)

    process = CrawlerProcess(settings)
    for spider in process.spider_loader.list():
        process.crawl(spider)
    process.start()

    with open(args.crawler_results, "r") as f:
        crawler_results = [TalkshowItem(**json.loads(line)) for line in f]

    if args.history_file.exists():
        with args.history_file.open("r") as f:
            history = json.load(f)
    else:
        history: dict[str, dict] = dict()
        # Keys: "talkshow_isodate, talkshow_name".
        # Should contain TalkshowItem instances or equivalent
        # dicts with an extra entry "reported_on" and
        # optionally "update_history" and "diff_keys" if one
        # episode was reported more than once due to updates.

    episodes_to_report = []
    for episode in crawler_results:
        date = datetime.datetime.fromisoformat(episode["isodate"])
        if (datetime.datetime.now() - date).days > 0:
            # Date is in the past
            continue
        ep_key = f"{episode["isodate"]}, {episode["name"]}"
        if ep_key in history:
            if episode.eq_with_ignore(history[ep_key]):
                # We've already reported on this episode:
                continue
            # Don't skip if any content changed!
            if "update_history" not in episode:
                episode["update_history"] = []
            # Copy episode from history to this episode's
            # update_history.
            # Using the episode from history instead of this
            # episode has the advantage that "reported_on"
            # will be included.
            episode["update_history"].append(
                copy.deepcopy(history[ep_key])
            )
            episode["diff_keys"] = episode.get_diff_keys(history[ep_key])

        episodes_to_report.append(episode)

    if args.report_telegram:
        api_token = os.getenv("TELEGRAM_API_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if api_token and chat_id:
            report_episodes_telegram(
                episodes=episodes_to_report,
                api_token=api_token,
                chat_id=chat_id,
            )
        else:
            raise ValueError(
                "Missing TELEGRAM_API_TOKEN or TELEGRAM_CHAT_ID"
            )

    history.update({
        # Merge key into one str because json doesn't like tuple keys:
        f"{ep["isodate"]}, {ep["name"]}":
        {"reported_on": datetime.datetime.now().isoformat(), **ep}
        for ep in episodes_to_report
    })
    with args.history_file.open("w") as f:
        f.write(json.dumps(history))
