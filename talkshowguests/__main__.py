import asyncio
import argparse
import datetime
import json
import os
import pathlib

from dotenv import load_dotenv
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
        results = [TalkshowItem(**json.loads(line)) for line in f]

        # print("\n\n\nHere come the results:")
        # print(results)

    if args.history_file.exists():
        with args.history_file.open("r") as f:
            history = json.load(f)
    else:
        history: dict[str, dict] = dict()
        # Keys: "talkshow_isodate, talkshow_name".
        # Should contain TalkshowItem instances or equivalent
        # dicts with an extra entry "reported_on".

    episodes_to_report = []
    for episode in results:
        date = datetime.datetime.fromisoformat(episode["isodate"])
        if (datetime.datetime.now() - date).days > 0:
            # Date is in the past
            continue
        if f"{episode["isodate"]}, {episode["name"]}" in history:
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

    history.update({
        # Merge key into one str because json doesn't like tuple keys:
        f"{ep["isodate"]}, {ep["name"]}":
        {"reported_on": datetime.datetime.now().isoformat(), **ep}
        for ep in episodes_to_report
    })
    with args.history_file.open("w") as f:
        f.write(json.dumps(history))


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
                disable_web_page_preview=True,
            )

    msg = "*Neue Talkshow-Folgen:*\n\n"
    for episode in episodes:
        msg += "["  # start link
        msg += datetime.datetime.fromisoformat(episode["isodate"]).strftime(
            "%Y-%m-%d"  # We don't want hours and minutes for now
        )
        msg += (
            f" *{episode['name']}*]({episode['url']})\n"
            f"Gäste:"
            + (
                "\n" +
                "\n".join([f"- {g}" for g in episode['guests']])
                if episode["guests"]
                else " TBA"
            )
            + (f"\nThema: _{episode['topic']}_" if episode["topic"] else "")
            + "\n\n"
        )
    msg = msg.replace("-", r"\-")
    print(msg)
    asyncio.run(_send_message(msg))
