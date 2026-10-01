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
const TRAY_AT_START = { true: "p3", false: "p6" };

const el = (id) => document.getElementById(id);
const frame = (i) => FRAMES[i % FRAMES.length];
const calm = matchMedia("(prefers-reduced-motion: reduce)").matches;

/* One entry per verdict taken on this page, true for a keep. */
const log = [];

function trayPlate(kept) {
  const i = log.lastIndexOf(kept);
  return i < 0 ? TRAY_AT_START[kept] : frame(i)[1];
}

function render() {
  const reviewed = REVIEWED_AT_START + log.length;
  const kept = KEPT_AT_START + log.filter(Boolean).length;
  const done = reviewed >= TOTAL;

  el("demo-name").textContent = done ? "Review finished" : frame(log.length)[0];
  el("demo-plate").setAttribute("href", "#" + frame(log.length)[1]);
  el("demo-next").setAttribute("href", "#" + frame(log.length + 1)[1]);
  el("demo-kept-plate").setAttribute("href", "#" + trayPlate(true));
  el("demo-left-plate").setAttribute("href", "#" + trayPlate(false));

  el("demo-count").textContent = reviewed + " / " + TOTAL;
  el("demo-kept").textContent = kept;
  el("demo-left").textContent = reviewed - kept;

  el("demo-keep").disabled = done;
  el("demo-leave").disabled = done;
  el("demo-undo").disabled = log.length === 0;
}

function decide(kept) {
  if (REVIEWED_AT_START + log.length >= TOTAL) return;

  el("demo-status").textContent = frame(log.length)[0] + (kept ? " kept" : " left alone");
  log.push(kept);

  /* The slide leaves towards the tray it goes to, then the next one is there. */
  const slide = el("demo-slide");
  if (calm || !slide.animate) return render();
  slide
    .animate(
      { transform: ["none", `translateX(${kept ? 55 : -55}%)`], opacity: [1, 0] },
      { duration: 170, easing: "cubic-bezier(0.7, 0, 0.84, 0)" },
    )
    .finished.then(() => {
      render();
      /* The frame that waited underneath comes up straight. */
      slide.animate(
        { transform: ["translate(3%, 3%) rotate(2deg)", "none"] },
        { duration: 220, easing: "cubic-bezier(0.16, 1, 0.3, 1)" },
      );
    });
}

function undo() {
  if (!log.length) return;
  log.pop();
  el("demo-status").textContent = frame(log.length)[0] + " back on the table";
  render();
}

el("demo-keep").addEventListener("click", () => decide(true));
el("demo-leave").addEventListener("click", () => decide(false));
el("demo-undo").addEventListener("click", undo);

/* The same three keys as the app. */
document.addEventListener("keydown", (event) => {
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  if (event.key === "ArrowRight") decide(true);
  else if (event.key === "ArrowLeft") decide(false);
  else if (event.key === "u" || event.key === "U") undo();
});
