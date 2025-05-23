import asyncio
import datetime

import telegram

from talkshowguests.items import TalkshowItem


def _escape(msg: str) -> str:
    return msg.replace(
        "-", r"\-").replace(
        "(", r"\(").replace(
        ")", r"\)").replace(
        ".", r"\.")


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

    msg = _escape("*Neue Talkshow-Folgen:*\n\n")
    for episode in episodes:
        msg += "["  # start link
        msg += _escape(
            datetime.datetime.fromisoformat(episode["isodate"]).strftime(
                "%Y-%m-%d"  # We don't want hours and minutes for now
            )
        )
        msg += (
            f" *{episode['name']}*]({episode['url']})\n"
            f"Gäste"
            + _escape(
                " (aktualisiert):"
                if "guests" in episode.get("diff_keys", {})
                else ":"
            )
            + _escape(
                "\n" +
                "\n".join([f"- {g}" for g in episode['guests']])
                if episode["guests"]
                else " TBA"
            )
            + (
                _escape(
                    "\nThema"
                    + (
                        " (aktualisiert)"
                        if "topic" in episode.get("diff_keys", {})
                        else ""
                    )
                    + f": _{episode['topic']}_"
                )
                if episode["topic"]
                else ""
            )
            + "\n\n"
        )
    print(msg)
    asyncio.run(_send_message(msg))
