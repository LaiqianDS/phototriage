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

# Focused mode hides both bars, so what they report is reported again here.
HUD_IDS = ("hud-filename", "hud-progress", "hud-kept", "hud-status")

# The states the script drives from the body element. The stylesheet is the
# whole of what each one does, so the two files have to agree on the name.
BODY_STATES = ("resting", "focused", "zoomed")
BODY_CLASSES = re.compile(r"""document\.body\.classList\.\w+\(\s*["']([^"']+)["']""")


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


def test_the_focused_mode_display_is_defined_and_kept_up_to_date() -> None:
    """A twin the script never writes is worse than no twin at all.

    It would sit on screen reporting the previous photo, and the failure is
    silent in both directions: an element the page drops leaves the script
    writing to `null`, and an element the script stops writing keeps its last
    value. Only reading the two files together catches either one.
    """
    defined = set(MARKUP_IDS.findall(read("index.html")))
    written = set(SCRIPT_IDS.findall(read("app.js")))

    undefined = sorted(name for name in HUD_IDS if name not in defined)
    assert not undefined, f"index.html does not define: {undefined}"

    stale = sorted(name for name in HUD_IDS if name not in written)
    assert not stale, f"app.js never writes to: {stale}"


def test_every_state_on_the_body_is_drawn_by_the_stylesheet() -> None:
    """A class name is the whole contract between the script and the stylesheet.

    Resting, focused mode and zoom are each one class on `body` and a set of
    rules that answer it. Rename either side and the key still works, the class
    still lands, and nothing on screen moves. Nothing throws, so only reading
    the two files together catches it.
    """
    driven = set(BODY_CLASSES.findall(read("app.js")))
    stylesheet = read("style.css")

    absent = sorted(name for name in BODY_STATES if name not in driven)
    assert not absent, f"app.js never puts these on the body: {absent}"

    unstyled = sorted(name for name in driven if f"body.{name}" not in stylesheet)
    assert not unstyled, f"style.css has no rule for: {unstyled}"
