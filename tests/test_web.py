"""Tests for the browser interface, read as text rather than run in a browser."""

from __future__ import annotations

import re
from pathlib import Path

from phototriage.api import WEB_DIR, create_app
from phototriage.store import Store

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

# Every request the script makes goes through `call("endpoint", ...)`, with the
# endpoint either quoted or at the start of a template string.
CALLED_ENDPOINTS = re.compile(r"""\bcall\(\s*["'`]([a-z-]+)""")

# Focused mode and the zoom were reached from the keyboard alone. These are the
# buttons that let a pointer in and out, each named after its key.
POINTER_CONTROLS = {"enter-focused": "F", "toggle-zoom": "Espacio", "leave-focused": "Esc"}
BUTTONS = re.compile(r"""<button\b[^>]*\bid=["']([^"']+)["'][^>]*>(.*?)</button>""", re.DOTALL)
CLICKS = re.compile(r"""\bel\(\s*["']([^"']+)["']\s*\)\.addEventListener\(\s*["']click["']""")


def read(name: str) -> str:
    return (WEB_DIR / name).read_text(encoding="utf-8")


def declarations(stylesheet: str, selector: str) -> str:
    """The body of the one rule written against exactly `selector`."""
    opening = f"\n{selector} {{"
    start = stylesheet.find(opening)
    assert start != -1, f"style.css has no rule for `{selector}`"
    start += len(opening)
    return stylesheet[start : stylesheet.index("}", start)]


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


def test_focused_mode_paints_no_colour_of_its_own_over_the_photo() -> None:
    """The verdict colour belongs to the card, and in here there is no card.

    The two edge buttons carry a flat tint as cards. Focused mode turns them
    into full height strips down the sides of the photo, where any colour of
    ours shifts the colour the eye reads at that edge of the image, and reading
    colour is half of what a review is for.

    What holds the line is one declaration cancelling a background the button
    already has, so deleting it brings the tint back with nothing on screen to
    explain it and nothing anywhere to complain.
    """
    stylesheet = read("style.css")
    edge = declarations(stylesheet, "body.focused .edge")

    assert "background-image: none" in edge, "the tint of the card reaches the photo"
    assert "background-color: transparent" in edge, "the surface of the card reaches the photo"

    for side in ("discard", "keep"):
        painted = [
            line.strip()
            for line in declarations(stylesheet, f"body.focused .edge.{side}").splitlines()
            if "background" in line
        ]
        assert not painted, f"body.focused .edge.{side} paints over the photo: {painted}"


def test_focused_mode_and_the_zoom_can_be_reached_without_a_keyboard() -> None:
    """A button the script never listens to looks like the way in and does nothing.

    Each button also names its key, so a pointer user learns the shortcut by
    using the button, and a key nothing on screen names stays a feature only the
    README knows about.
    """
    buttons = dict(BUTTONS.findall(read("index.html")))
    clicked = set(CLICKS.findall(read("app.js")))

    for name, key in POINTER_CONTROLS.items():
        assert name in buttons, f"index.html has no button `{name}`"
        assert name in clicked, f"app.js does not listen to clicks on `{name}`"
        assert f">{key}</kbd>" in buttons[name], f"`{name}` does not name its key, {key}"


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


def test_leaving_focused_mode_survives_a_browser_without_the_fullscreen_api() -> None:
    """Safari before 16.4 spells fullscreen with a `webkit` prefix only.

    There `document.fullscreenElement` is undefined, not null, so a comparison
    with null reads as "in fullscreen" and calls an `exitFullscreen` that does
    not exist. The page throws every time focused mode is left. Focused mode
    there never went fullscreen in the first place, so asking whether the
    element is set at all is both correct and enough.
    """
    script = read("app.js")

    compared = re.findall(r"fullscreenElement\s*[!=]==?\s*null", script)
    assert not compared, f"app.js compares fullscreenElement with null: {compared}"
    assert "fullscreenElement" in script, "app.js no longer reads fullscreenElement at all"


def test_every_endpoint_the_script_calls_is_a_route_the_server_answers(tmp_path: Path) -> None:
    """A misspelled endpoint answers 404 only when someone presses the button.

    The static mount at `/` would answer any other path with its own 404, so
    nothing fails at startup, and the interface shows `Not Found` on the status
    line in front of the user.
    """
    app = create_app(Store(tmp_path / "state.json"))
    served = {
        route.path.removeprefix("/api/") for route in app.routes if route.path.startswith("/api/")
    }
    called = set(CALLED_ENDPOINTS.findall(read("app.js")))

    assert called, "no call to the API found in app.js"
    missing = sorted(called - served)
    assert not missing, f"app.js calls endpoints the server does not answer: {missing}"
