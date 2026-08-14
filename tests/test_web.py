"""Tests for the browser interface, read as text rather than run in a browser."""

from __future__ import annotations

import re

from phototriage.api import WEB_DIR

# The script reaches the page through one helper, `el("id")`, and could also
# call `document.getElementById("id")` directly. Both spellings are collected.
SCRIPT_IDS = re.compile(r"""(?:\bel|document\.getElementById)\(\s*["']([^"']+)["']\s*\)""")
MARKUP_IDS = re.compile(r"""\bid=["']([^"']+)["']""")
# `for` names the control a label belongs to; the two `aria-*` attributes name
# the elements that title and describe a control. All three hold ids.
MARKUP_REFS = re.compile(r"""\b(?:for|aria-labelledby|aria-describedby)=["']([^"']+)["']""")


def read(name: str) -> str:
    return (WEB_DIR / name).read_text(encoding="utf-8")


def test_every_id_the_script_asks_for_exists_in_the_page() -> None:
    """The two files are the only pair nothing else checks.

    `document.getElementById` answers a typo with `null` instead of an error, so
    a renamed or misspelled id stays silent until a handler runs in front of the
    user and fails on a line that names neither file.
    """
    used = set(SCRIPT_IDS.findall(read("app.js")))
    defined = set(MARKUP_IDS.findall(read("index.html")))

    missing = sorted(used - defined)
    assert not missing, f"app.js asks for ids that index.html does not define: {missing}"


def test_every_label_and_aria_reference_points_at_a_real_element() -> None:
    """A dangling reference costs the accessible name, and nothing complains.

    The browser drops a `for` or an `aria-describedby` that names no element
    without a word, so the control simply reaches a screen reader unnamed or
    unexplained. Only a reader of both attributes would notice.
    """
    markup = read("index.html")
    defined = set(MARKUP_IDS.findall(markup))
    referenced = {name for value in MARKUP_REFS.findall(markup) for name in value.split()}

    missing = sorted(referenced - defined)
    assert not missing, f"index.html points at ids it does not define: {missing}"
