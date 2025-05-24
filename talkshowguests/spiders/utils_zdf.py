"""
Utilities for talkshows on ZDF,
which have similar websites.
"""

import json
import re


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
