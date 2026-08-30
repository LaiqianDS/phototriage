/*
 * The counter in the hero, and the tally under "Nothing moves until you say so",
 * are one running model of a review: a roll of 480 frames that ends with 31
 * keepers, the same figures the rest of the page quotes.
 *
 * The markup already carries the opening frame of that model, so the page is
 * complete with this file blocked or missing. All the script does is keep the
 * numbers moving.
 */

const TOTAL = 480;
const KEPT_AT_END = 31;

/* Where the model starts, and where it returns to when the roll runs out. */
const FIRST_REVIEWED = 208;

/* One tick per verdict and one per advance, so a name stays long enough to read. */
const TICK_MS = 1150;

const NAMES = [
  "IMG_0412.JPG",
  "IMG_0413.JPG",
  "IMG_0414.JPG",
  "IMG_0415.JPG",
  "IMG_0416.JPG",
  "IMG_0417.JPG",
];

/* Which of those six frames is a keeper. */
const PATTERN = [true, false, true, true, false, true];

const el = (id) => document.getElementById(id);

const state = { i: 0, verdict: null, reviewed: FIRST_REVIEWED };

function step() {
  if (state.verdict === null) {
    state.verdict = PATTERN[state.i % PATTERN.length] ? "keep" : "discard";
    return;
  }
  state.verdict = null;
  state.i = (state.i + 1) % NAMES.length;
  state.reviewed = state.reviewed >= TOTAL ? FIRST_REVIEWED : state.reviewed + 1;
}

function render() {
  const kept = Math.round(state.reviewed * (KEPT_AT_END / TOTAL));
  const percent = Math.round((state.reviewed / TOTAL) * 100) + "%";

  el("demo-name").textContent = NAMES[state.i];
  el("demo-pct").textContent = percent;
  el("demo-fill").style.width = percent;
  el("demo-count").textContent = state.reviewed + " / " + TOTAL;

  el("verdict-keep").hidden = state.verdict !== "keep";
  el("verdict-discard").hidden = state.verdict !== "discard";
  el("verdict-waiting").hidden = state.verdict !== null;

  el("demo-kept").textContent = kept;
  el("demo-discarded").textContent = state.reviewed - kept;
  el("demo-left").textContent = Math.max(0, TOTAL - state.reviewed);
}

/* A reader who asks for less motion keeps the opening frame instead. */
if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
  setInterval(() => {
    step();
    render();
  }, TICK_MS);
}
