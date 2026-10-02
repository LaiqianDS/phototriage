/* The table at the top of the page is a review the visitor runs with their own arrow keys: a roll
   of 480 frames, opened mid-way, the same figures the rest of the page quotes. */

const TOTAL = 480;

/* Where the visitor finds the roll: 208 reviewed, 13 of them kept. */
const REVIEWED_AT_START = 208;
const KEPT_AT_START = 13;

/* File name and plate. The plates are the <symbol> ids in the page. */
const FRAMES = [
  ["IMG_0412.JPG", "p1"],
  ["IMG_0413.JPG", "p2"],
  ["IMG_0414.JPG", "p3"],
  ["IMG_0415.JPG", "p4"],
  ["IMG_0416.JPG", "p5"],
  ["IMG_0417.JPG", "p6"],
  ["IMG_0418.JPG", "p7"],
  ["IMG_0419.JPG", "p8"],
  ["IMG_0420.JPG", "p9"],
];

/* What each tray shows before the visitor has sent anything to it. */
const TRAY_AT_START = { true: "p10", false: "p11" };

const EASE_OUT = "cubic-bezier(0.16, 1, 0.3, 1)";

const el = (id) => document.getElementById(id);
const frame = (i) => FRAMES[i % FRAMES.length];
const calm = matchMedia("(prefers-reduced-motion: reduce)").matches || !Element.prototype.animate;

/* One entry per verdict taken on this page, true for a keep. */
const log = [];

const tray = (kept) => el(kept ? "demo-kept-plate" : "demo-left-plate");

/* The transform that lays the slide on a tray. */
function towards(kept) {
  const from = el("demo-slide").getBoundingClientRect();
  const to = tray(kept).closest(".mount").getBoundingClientRect();
  const x = to.left + to.width / 2 - (from.left + from.width / 2);
  const y = to.top + to.height / 2 - (from.top + from.height / 2);
  return `translate(${x}px, ${y}px) scale(${to.width / from.width})`;
}

/* A count that changes comes up from below, so the eye finds which tray took the slide. */
function count(id, value) {
  const node = el(id);
  if (node.textContent === String(value)) return;
  node.textContent = value;
  if (!calm) {
    node.animate(
      { transform: ["translateY(45%)", "none"], opacity: [0, 1] },
      { duration: 200, easing: EASE_OUT },
    );
  }
}

/* The table: the slide, the one under it and the keys. */
function render() {
  const reviewed = REVIEWED_AT_START + log.length;
  const done = reviewed >= TOTAL;

  el("demo-name").textContent = done ? "Review finished" : frame(log.length)[0];
  el("demo-plate").setAttribute("href", "#" + frame(log.length)[1]);
  el("demo-next").setAttribute("href", "#" + frame(log.length + 1)[1]);
  el("demo-count").textContent = reviewed + " / " + TOTAL;

  el("demo-keep").disabled = done;
  el("demo-leave").disabled = done;
  el("demo-undo").disabled = log.length === 0;
}

/* The trays, drawn apart from the table because a slide takes a moment to reach one. */
function renderTrays() {
  for (const kept of [true, false]) {
    const i = log.lastIndexOf(kept);
    tray(kept).setAttribute("href", "#" + (i < 0 ? TRAY_AT_START[kept] : frame(i)[1]));
  }
  const kept = KEPT_AT_START + log.filter(Boolean).length;
  count("demo-kept", kept);
  count("demo-left", REVIEWED_AT_START + log.length - kept);
}

function decide(kept) {
  if (REVIEWED_AT_START + log.length >= TOTAL) return;

  el("demo-status").textContent = frame(log.length)[0] + (kept ? " kept" : " discarded");
  const slide = el("demo-slide");

  /* A copy of the slide makes the trip, so the table is free for the next verdict at once. */
  let flying;
  if (!calm) {
    flying = slide.cloneNode(true);
    flying.removeAttribute("id");
    flying.querySelectorAll("[id]").forEach((node) => node.removeAttribute("id"));
    flying.classList.add("mount-flying");
    flying.setAttribute("aria-hidden", "true");
    slide.before(flying);
  }

  log.push(kept);
  render();
  if (calm) return renderTrays();

  /* The frame that waited underneath comes up straight. */
  slide.animate(
    { transform: ["translate(3%, 3%) rotate(2deg)", "none"] },
    { duration: 220, easing: EASE_OUT },
  );
  flying
    .animate(
      { transform: ["none", towards(kept)] },
      { duration: 320, easing: "cubic-bezier(0.5, 0, 0.2, 1)" },
    )
    .finished.then(() => {
      flying.remove();
      renderTrays();
    });
}

function undo() {
  if (!log.length) return;
  const kept = log.pop();
  el("demo-status").textContent = frame(log.length)[0] + " back on the table";
  render();
  renderTrays();

  /* The slide comes back from the tray it went to. */
  if (!calm) {
    el("demo-slide").animate(
      { transform: [towards(kept), "none"] },
      { duration: 280, easing: EASE_OUT },
    );
  }
}

el("demo-keep").addEventListener("click", () => decide(true));
el("demo-leave").addEventListener("click", () => decide(false));
el("demo-undo").addEventListener("click", undo);

/* The page is complete without the script, so the controls only appear once they work. */
el("demo-keys").hidden = false;
el("demo-hint").hidden = false;

/* The keys only act on a table the visitor can see. */
let onScreen = true;
new IntersectionObserver(([entry]) => (onScreen = entry.isIntersecting)).observe(el("demo-bench"));

/* The same three keys as the app. */
document.addEventListener("keydown", (event) => {
  if (!onScreen || event.metaKey || event.ctrlKey || event.altKey) return;
  if (event.key === "ArrowRight") decide(true);
  else if (event.key === "ArrowLeft") decide(false);
  else if (event.key === "u" || event.key === "U") undo();
});

/* The three kept frames arrive when the result is on screen. Without the script they are there
   from the start. */
if (!calm) {
  const payoff = el("demo-payoff");
  payoff.classList.add("is-waiting");
  new IntersectionObserver(
    ([entry], watch) => {
      if (!entry.isIntersecting) return;
      payoff.classList.remove("is-waiting");
      watch.disconnect();
    },
    { threshold: 0.3 },
  ).observe(payoff);
}
