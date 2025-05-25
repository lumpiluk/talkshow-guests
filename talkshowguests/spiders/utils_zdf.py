"""
Utilities for talkshows on ZDF,
which have similar websites.
"""

import json
import re


def get_episodes_from_zdf_page(response):
    # All relevant content is included in many <script>
    # elements at the end of the page:
    script_elems = response.css("script::text")

    for script_elem in script_elems:
        script_data = parse_script_text(script_elem.get())
        if not script_data:
            continue

        # Useful if you want to inspect the json objects:
        # with open(f"debug_script-data_{hash(script_elem)}.json", "w") as f:
        #     json.dump(script_data, f, indent=2)

        try:
            season_objs: list[dict] = script_data[0][
                "result"]["data"][
                "smartCollectionByCanonical"][
                "seasons"][
                "nodes"]
        except (KeyError, TypeError):
            # Probably not the script_elem we are looking for
            continue
        for season_obj in season_objs:
            for ep in season_obj["episodes"]["nodes"]:
                yield ep


def parse_script_text(text: str) -> dict:
    """
    Attempt to convert the content of a <script>
    tag to json.
    Placing lots of such <script> tags at the end
    of a webpage instead of using regular HTML
    seems to be a React thing.
    """
    match = re.search(
        r'self\.__next_f\.push\('
        r'\[1,"[a-z0-9]+:'  # \[
        r'(.*?)'
        r'"\]\);?',  # has to be closed by a `])`
        text,
        re.DOTALL,  # make `.` also match newlines
    )
    if not match:
        return {}
    escaped_json = match.group(1)
    unescaped_json = json.loads(f'"{escaped_json}"')

    try:
        return json.loads(unescaped_json)
    except json.JSONDecodeError as e:
        return {}
