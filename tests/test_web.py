"""Tests for the browser interface, read as text rather than run in a browser."""

from __future__ import annotations

import re
from pathlib import Path

from phototriage.api import WEB_DIR, create_app
from phototriage.store import Store

# The script reaches the page through one helper, `el("id")`, and could also call
# `document.getElementById("id")` directly.
SCRIPT_IDS = re.compile(r"""(?:\bel|document\.getElementById)\(\s*["']([^"']+)["']\s*\)""")
MARKUP_IDS = re.compile(r"""\bid=["']([^"']+)["']""")
# `for` names the control a label belongs to; the two `aria-*` attributes name the elements that
# title and describe a control.
MARKUP_REFS = re.compile(r"""\b(?:for|aria-labelledby|aria-describedby)=["']([^"']+)["']""")

# Focused mode hides both bars, so what they report is reported again here.
HUD_IDS = ("hud-filename", "hud-progress", "hud-kept", "hud-status")

# The states the script drives from the body element.
BODY_STATES = ("resting", "focused", "zoomed")
BODY_CLASSES = re.compile(r"""document\.body\.classList\.\w+\(\s*["']([^"']+)["']""")

# Every request the script makes goes through `call("endpoint", ...)`, with the endpoint either
# quoted or at the start of a template string.
CALLED_ENDPOINTS = re.compile(r"""\bcall\(\s*["'`]([a-z-]+)""")

# Focused mode and the zoom were reached from the keyboard alone.
POINTER_CONTROLS = {"enter-focused": "F", "toggle-zoom": "Space", "leave-focused": "Esc"}
BUTTONS = re.compile(r"""<button\b[^>]*\bid=["']([^"']+)["'][^>]*>(.*?)</button>""", re.DOTALL)
CLICKS = re.compile(r"""\bel\(\s*["']([^"']+)["']\s*\)\.addEventListener\(\s*["']click["']""")


def read(name: str) -> str:
    return (WEB_DIR / name).read_text(encoding="utf-8")


def test_every_id_the_landing_page_script_asks_for_exists_in_the_landing_page() -> None:
    """The same silent `null` as in the app, on the page nothing else checks."""
    site = Path(__file__).parents[1] / "site"
    used = set(SCRIPT_IDS.findall((site / "demo.js").read_text(encoding="utf-8")))
    defined = set(MARKUP_IDS.findall((site / "index.html").read_text(encoding="utf-8")))

    assert used, "no id found in demo.js"
    missing = sorted(used - defined)
    assert not missing, f"demo.js asks for ids that site/index.html does not define: {missing}"


def test_the_tour_video_waits_for_the_reader_and_its_files_are_in_the_site() -> None:
    """A wrong file name shows as an empty player, and autoplay as 3.4 MB nobody asked for."""
    site = Path(__file__).parents[1] / "site"
    video = re.search(r"<video\b([^>]*)>(.*?)</video>", (site / "index.html").read_text(), re.S)

    assert video, "site/index.html has no video"
    attributes, inside = video.groups()
    assert 'preload="none"' in attributes
    assert "autoplay" not in attributes
    files = re.findall(r'\b(?:poster|src)="([^"]+)"', attributes + inside)
    assert len(files) == 2, f"expected a poster and one source, found {files}"
    missing = [name for name in files if not (site / name).is_file()]
    assert not missing, f"the video names files that are not in site/: {missing}"


def declarations(stylesheet: str, selector: str) -> str:
    """The body of the one rule written against exactly `selector`."""
    opening = f"\n{selector} {{"
    start = stylesheet.find(opening)
    assert start != -1, f"style.css has no rule for `{selector}`"
    start += len(opening)
    return stylesheet[start : stylesheet.index("}", start)]


def test_every_id_the_script_asks_for_exists_in_the_page() -> None:
    """The two files are the only pair nothing else checks."""
    used = set(SCRIPT_IDS.findall(read("app.js")))
    defined = set(MARKUP_IDS.findall(read("index.html")))

    missing = sorted(used - defined)
    assert not missing, f"app.js asks for ids that index.html does not define: {missing}"


def test_every_label_and_aria_reference_points_at_a_real_element() -> None:
    """A dangling reference costs the accessible name, and nothing complains."""
    markup = read("index.html")
    defined = set(MARKUP_IDS.findall(markup))
    referenced = {name for value in MARKUP_REFS.findall(markup) for name in value.split()}

    missing = sorted(referenced - defined)
    assert not missing, f"index.html points at ids it does not define: {missing}"


def test_the_focused_mode_display_is_defined_and_kept_up_to_date() -> None:
    """A twin the script never writes is worse than no twin at all."""
    defined = set(MARKUP_IDS.findall(read("index.html")))
    written = set(SCRIPT_IDS.findall(read("app.js")))

    undefined = sorted(name for name in HUD_IDS if name not in defined)
    assert not undefined, f"index.html does not define: {undefined}"

    stale = sorted(name for name in HUD_IDS if name not in written)
    assert not stale, f"app.js never writes to: {stale}"


def test_focused_mode_paints_no_colour_of_its_own_over_the_photo() -> None:
    """The verdict colour belongs to the card, and in here there is no card."""
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
    """A button the script never listens to looks like the way in and does nothing."""
    buttons = dict(BUTTONS.findall(read("index.html")))
    clicked = set(CLICKS.findall(read("app.js")))

    for name, key in POINTER_CONTROLS.items():
        assert name in buttons, f"index.html has no button `{name}`"
        assert name in clicked, f"app.js does not listen to clicks on `{name}`"
        assert f">{key}</kbd>" in buttons[name], f"`{name}` does not name its key, {key}"


def test_every_state_on_the_body_is_drawn_by_the_stylesheet() -> None:
    """A class name is the whole contract between the script and the stylesheet."""
    driven = set(BODY_CLASSES.findall(read("app.js")))
    stylesheet = read("style.css")

    absent = sorted(name for name in BODY_STATES if name not in driven)
    assert not absent, f"app.js never puts these on the body: {absent}"

    unstyled = sorted(name for name in driven if f"body.{name}" not in stylesheet)
    assert not unstyled, f"style.css has no rule for: {unstyled}"


def test_leaving_focused_mode_survives_a_browser_without_the_fullscreen_api() -> None:
    """Safari before 16.4 spells fullscreen with a `webkit` prefix only."""
    script = read("app.js")

    compared = re.findall(r"fullscreenElement\s*[!=]==?\s*null", script)
    assert not compared, f"app.js compares fullscreenElement with null: {compared}"
    assert "fullscreenElement" in script, "app.js no longer reads fullscreenElement at all"


def test_every_endpoint_the_script_calls_is_a_route_the_server_answers(tmp_path: Path) -> None:
    """A misspelled endpoint answers 404 only when someone presses the button."""
    app = create_app(Store(tmp_path / "state.json"))
    served = {
        route.path.removeprefix("/api/") for route in app.routes if route.path.startswith("/api/")
    }
    called = set(CALLED_ENDPOINTS.findall(read("app.js")))

    assert called, "no call to the API found in app.js"
    missing = sorted(called - served)
    assert not missing, f"app.js calls endpoints the server does not answer: {missing}"
