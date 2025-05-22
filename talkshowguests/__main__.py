import asyncio
import argparse
import datetime
import json
import os
import pathlib

from dotenv import load_dotenv
import pandas as pd
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import telegram

from .items import TalkshowItem


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
        help="Path to a history CSV file of previously "
             "reported talkshows. Will be created if it "
             "does not yet exist.",
        default=pathlib.Path("history.csv"),
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
        results = [TalkshowItem(**json.loads(line)) for line in f]

        # print("\n\n\nHere come the results:")
        # print(results)

    if args.history_file.exists():
        history = pd.read_csv(args.history_file)
    else:
        history = pd.DataFrame(
            columns=list(TalkshowItem.fields.keys()) + ["reported_on"]
        )

    episodes_to_report = []
    for episode in results:
        date = datetime.datetime.fromisoformat(episode["isodate"])
        if (datetime.datetime.now() - date).days > 0:
            # Date is in the past
            continue
        if not history.query(
                f"isodate==\"{episode['isodate']}\" "
                f"and name==\"{episode['name']}\""
        ).empty:
            # We've already reported on this episode:
            continue
            # TODO: don't skip if any content changed!
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

    new_history = pd.concat([
        history,
        pd.DataFrame.from_records([
            {"reported_on": datetime.datetime.now(), **ep}
            for ep in episodes_to_report
        ])
    ])
    new_history.to_csv(args.history_file)


def report_episodes_telegram(
    episodes: list[TalkshowItem],
    api_token: str,
    chat_id: str,
):
    if not episodes:
        return

    async def _send_message(msg: str):
        bot = telegram.Bot(api_token)
        async with bot:
            await bot.send_message(
                text=msg,
                chat_id=chat_id,
                parse_mode="MarkdownV2",
            )

    msg = "*Neue Talkshow-Folgen:*\n\n"
    for episode in episodes:
        msg += datetime.datetime.fromisoformat(episode["isodate"]).strftime(
            "%Y-%m-%d"  # We don't want hours and minutes for now
        )
        msg += (
            f" *{episode['name']}*\n"
            f"Gäste:\n"
            + "\n".join([f"- {g}" for g in episode['guests']])
            + (f"Thema: _{episode['topic']}_" if episode["topic"] else "")
            + "\n\n"
        )
    msg = msg.replace("-", "\-")
    print(msg)
    asyncio.run(_send_message(msg))
