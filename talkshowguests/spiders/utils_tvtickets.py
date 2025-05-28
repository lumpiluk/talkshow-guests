from talkshowguests.items import RecordingInfoItem, TalkshowItem


def find_show_in_tickets_page(
    response,
    recording_location,
) -> TalkshowItem | None:
    """
    Return a complemented TalkshowItem based on info from a tickets page.

    Assuming that `response.meta` already includes the basic info beyond
    the `recording_info` field.
    """
    episode_elems = response.css(".date_wrapper")
    months = ["JAN", "FEB", "MÄR", "APR", "MAI", "JUN", "JUL", "AUG",
              "SEP", "OKT", "NOV", "DEZ"]
    # Search the listed events for the episode of which we already
    # have an isodate:
    for episode_elem in episode_elems:
        year = episode_elem.css(".year::text").get()
        month = months.index(episode_elem.css(".month::text").get()) + 1
        day = int(episode_elem.css(".day::text").get())
        isodate = f"{year}-{month:02}-{day:02}"
        if not response.meta["talkshow_data"]["isodate"].startswith(
                isodate):
            continue
        return TalkshowItem.from_guest_list(
            recording_info=RecordingInfoItem(
                location=recording_location,
                tickets_available=episode_elem.css(
                    ".btn_tickets_buchen_info::text").get() == "BUCHEN",
                doors=episode_elem.css(
                    ".termin_abholen::text").get().strip(),
                tickets_url=response.url,
            ),
            **response.meta["talkshow_data"],
        )
    return None
