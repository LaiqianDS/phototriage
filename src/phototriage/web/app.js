const el = (id) => document.getElementById(id);

const imageUrl = (name) => `/api/image/${encodeURIComponent(name)}`;

/** Call the API. Passing a body makes it a POST. */
async function call(endpoint, body) {
  const options =
    body === undefined
      ? {}
      : {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        };
  const response = await fetch(`/api/${endpoint}`, options);
  // A crash inside the server answers with plain text instead of `detail`, and the parser error
  // would otherwise reach the user in place of the failure.
  const payload = await response.json().catch(() => null);
  if (response.ok) return payload;
  if (typeof payload?.detail === "string") throw new Error(payload.detail);
  // The validator answers a body it cannot read with a list in `detail`, which would read `[object
  // Object]`.
  if (response.status === 422) throw new Error("This page is from another version. Reload it.");
  throw new Error(response.statusText);
}

// Written to both places, because focused mode hides the bar the first one lives in and an error
// nobody can see is the same as no error at all.
function report(message, isError = false) {
  el("status").textContent = message;
  el("status").classList.toggle("error", isError);
  el("hud-status").textContent = message;
  el("hud-status").classList.toggle("error", isError);
}

/** Run one API action at a time. */
let pending = false;
async function run(action) {
  if (pending) return;
  pending = true;
  document.body.setAttribute("aria-busy", "true");
  // The previous message belonged to the previous action.
  report("");
  try {
    render(await action());
  } catch (error) {
    report(error.message, true);
  } finally {
    pending = false;
    document.body.removeAttribute("aria-busy");
  }
}

// ---------------------------------------------------------------- review ---

function render(state) {
  const tally = `${state.reviewed} / ${state.total}`;
  el("progress").textContent = tally;
  el("hud-progress").textContent = tally;
  el("kept").textContent = state.kept;
  el("hud-kept").textContent = state.kept;
  el("discarded").textContent = state.discarded;
  const done = state.total === 0 ? 0 : (state.reviewed / state.total) * 100;
  el("progress-fill").style.width = `${done}%`;

  // Only overwrite the fields the user may be editing when the server disagrees.
  if (document.activeElement !== el("source")) {
    el("source").value = state.source ?? "";
  }
  if (document.activeElement !== el("destination")) {
    el("destination").value = state.destination ?? "";
  }
  el("pair-raws").checked = state.pair_raws;
  el("search-subfolders").checked = state.search_subfolders;
  el("pair-videos").checked = state.pair_videos;

  const chosen = state.source !== null;
  el("idle").hidden = chosen;
  el("empty").hidden = !chosen || state.total > 0;
  el("done").hidden = !chosen || state.total === 0 || state.current !== null;
  el("viewer").hidden = state.current === null;
  el("filename").textContent = state.current ?? "";
  el("hud-filename").textContent = state.current ?? "";
  fitNewPhoto(state.current);

  if (state.current !== null) {
    el("photo").src = imageUrl(state.current);
    el("photo").alt = state.current;
  }

  // Warm the browser cache so the next photo appears without a wait.
  if (state.upcoming !== null) {
    new Image().src = imageUrl(state.upcoming);
  }

  el("keep").disabled = state.current === null;
  el("discard").disabled = state.current === null;
  el("enter-focused").disabled = state.current === null;
  el("toggle-zoom").disabled = state.current === null;
  el("undo").disabled = state.reviewed === 0;
  el("apply").disabled = state.kept === 0;
  el("destination").disabled = !chosen;
}

// The verdict names the photo on screen, and the server refuses it when that photo is no longer the
// next one.
function decide(verdict) {
  if (shown === null) return;
  run(() =>
    call("decide", { verdict, name: shown }).catch(async (error) => {
      render(await call("state"));
      throw error;
    }),
  );
}

const undo = () => run(() => call("undo", {}));

const setSource = (path) => run(() => call("source", { path }));
const setDestination = (path) => run(() => call("destination", { path }));

/** A size the way Finder writes it: powers of 1000, one decimal. */
function weight(bytes) {
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let unit = 0;
  while (value >= 1000 && unit < units.length - 1) {
    value /= 1000;
    unit += 1;
  }
  return `${value.toLocaleString("en", { maximumFractionDigits: 1 })} ${units[unit]}`;
}

/** The status line for a run in flight: the file it is on, and the bytes before it. */
function describe(progress) {
  const verb = progress.mode === "copy" ? "Copying" : "Moving";
  const files = `${progress.files} of ${progress.total_files}`;
  return `${verb} ${files} (${weight(progress.bytes)} of ${weight(progress.total_bytes)})`;
}

/** Report the run in flight on the status line, twice a second. */
function watchTransfer(onEnd) {
  let watching = true;
  const stop = () => {
    watching = false;
    clearInterval(timer);
  };
  const timer = setInterval(async () => {
    const progress = await call("progress").catch(() => null);
    if (!watching) return;
    if (progress !== null) {
      report(describe(progress));
    } else if (onEnd) {
      stop();
      onEnd();
    }
  }, 500);
  return stop;
}

function apply() {
  const mode = el("mode-move").checked ? "move" : "copy";
  const verb = mode === "copy" ? "Copy" : "Move";
  run(async () => {
    // Asked inside `run`, so a second press while the dialog is open is dropped instead of asking
    // twice.
    const plan = await call("plan");
    const files = `${plan.files} files (${weight(plan.bytes)})`;
    const question = `${verb} ${files} to ${plan.destination}?`;
    if (!confirm(question)) return call("state");
    report("Working...");
    const stopWatching = watchTransfer();
    const result = await call("apply", { mode }).finally(stopWatching);
    const { transferred, already_present, failed, destination } = result;
    // Without the second half, a repeated copy reads as `0 files`, which looks like a failure
    // rather than a selection that is already safe.
    const present = already_present > 0 ? `, ${already_present} already there` : "";
    const summary = `${transferred} files in ${destination}${present}`;
    // The line has room for one reason.
    const failures = Object.entries(failed);
    if (failures.length === 0) {
      report(summary);
    } else {
      const [name, reason] = failures[0];
      report(`${summary}. ${failures.length} failed. ${name}: ${reason}`, true);
    }
    return call("state");
  });
}

// ----------------------------------------------------------------- theme ---

const system = matchMedia("(prefers-color-scheme: dark)");

/** Apply a theme, and label the button with the one it switches to. */
function paint(theme) {
  document.documentElement.dataset.theme = theme;
  el("toggle-theme").setAttribute(
    "aria-label",
    theme === "dark" ? "Switch to light theme" : "Switch to dark theme",
  );
}

// Until the button is used the system decides, and keeps deciding when it changes.
system.addEventListener("change", () => {
  if (localStorage.getItem("theme") === null) {
    paint(system.matches ? "dark" : "light");
  }
});

el("toggle-theme").addEventListener("click", () => {
  const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
  localStorage.setItem("theme", next);
  paint(next);
});

// ----------------------------------------------------------------- stage ---

/** Reserve the room the chrome occupies. */
function fitStage() {
  const style = document.documentElement.style;
  style.setProperty("--bar-top", `${el("topbar").offsetHeight}px`);
  style.setProperty("--bar-bottom", `${el("bottombar").offsetHeight}px`);
  style.setProperty("--edge", `${el("keep").offsetWidth}px`);
}

const fitting = new ResizeObserver(fitStage);
for (const id of ["topbar", "bottombar", "keep"]) {
  fitting.observe(el(id));
}

// ------------------------------------------------------------------ zoom ---

const viewer = el("viewer");

/** The photo on screen, which a verdict names and a new photo is compared with. */
let shown = null;

/** Show the photo at one image pixel per screen pixel. */
function enterZoom() {
  const photo = el("photo");
  if (!photo.complete || photo.naturalWidth === 0) return;
  // Never smaller than the photo already is.
  const fitted = photo.clientWidth;
  document.body.classList.add("zoomed");
  el("toggle-zoom").setAttribute("aria-pressed", "true");
  photo.style.width = `${Math.max(photo.naturalWidth / devicePixelRatio, fitted)}px`;
  // The middle of the photo, which is where it was before.
  viewer.scrollLeft = (viewer.scrollWidth - viewer.clientWidth) / 2;
  viewer.scrollTop = (viewer.scrollHeight - viewer.clientHeight) / 2;
}

function leaveZoom() {
  document.body.classList.remove("zoomed");
  el("toggle-zoom").setAttribute("aria-pressed", "false");
  el("photo").style.width = "";
}

function toggleZoom() {
  if (document.body.classList.contains("zoomed")) leaveZoom();
  else enterZoom();
}

/** Fit a new photo to the window again. */
function fitNewPhoto(current) {
  if (current === shown) return;
  shown = current;
  leaveZoom();
}

/** Drag the photo under the pointer. */
let panFrom = null;

viewer.addEventListener("pointerdown", (event) => {
  if (!document.body.classList.contains("zoomed")) return;
  panFrom = { x: event.clientX, y: event.clientY };
  viewer.setPointerCapture(event.pointerId);
  event.preventDefault();
});

viewer.addEventListener("pointermove", (event) => {
  if (panFrom === null) return;
  viewer.scrollLeft -= event.clientX - panFrom.x;
  viewer.scrollTop -= event.clientY - panFrom.y;
  panFrom = { x: event.clientX, y: event.clientY };
});

for (const event of ["pointerup", "pointercancel"]) {
  viewer.addEventListener(event, () => {
    panFrom = null;
  });
}

// --------------------------------------------------------- focused mode ---

/** Give the photo the whole window. */
async function enterFocused() {
  document.body.classList.add("focused");
  releaseFocusFrom(".bar");
  try {
    await document.documentElement.requestFullscreen();
  } catch {
    // Windowed focused mode is the fallback, not a failure to report.
  }
}

function leaveFocused() {
  document.body.classList.remove("focused");
  releaseFocusFrom(".focus-hint");
  // Asked by truth, not against null.
  if (document.fullscreenElement) document.exitFullscreen();
}

/** Let go of a control that the mode change takes off the screen. */
function releaseFocusFrom(selector) {
  if (document.activeElement?.closest(selector)) document.activeElement.blur();
}

// Escape leaves fullscreen without the keypress ever reaching the page, and the window chrome
// offers its own way out as well.
document.addEventListener("fullscreenchange", () => {
  if (!document.fullscreenElement) leaveFocused();
});

// -------------------------------------------------------------- explorer ---

const explorer = el("explorer");
let browsing = null;

/** Join a folder and a child name without doubling the separator at the root. */
const join = (folder, name) => (folder.endsWith("/") ? folder + name : `${folder}/${name}`);

async function browse(path) {
  try {
    const listing = await call(`browse?path=${encodeURIComponent(path)}`);
    browsing = listing.path;
    el("explorer-path").textContent = listing.path;
    el("explorer-count").textContent = `${listing.images} images here`;
    el("explorer-count").classList.remove("error");
    const items = listing.folders.map((name) => folderItem(name, join(listing.path, name)));
    if (listing.parent !== null) {
      items.unshift(folderItem("Up one level", listing.parent, true));
    }
    if (listing.folders.length === 0) {
      items.push(emptyItem("No subfolders."));
    }
    el("explorer-list").replaceChildren(...items);
  } catch (error) {
    el("explorer-count").textContent = error.message;
    el("explorer-count").classList.add("error");
  }
}

function folderItem(label, path, up = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.className = up ? "folder up" : "folder";
  button.addEventListener("click", () => browse(path));
  const item = document.createElement("li");
  item.append(button);
  return item;
}

function emptyItem(message) {
  const item = document.createElement("li");
  item.className = "folder-empty";
  item.textContent = message;
  return item;
}

// --------------------------------------------------------------- resting ---

const settings = el("settings");

const REST_DELAY = 2500;
const stillness = matchMedia("(prefers-reduced-motion: reduce)");
let restTimer = 0;

/** Whether hiding the bars right now would take something away from the user. */
function chromeInUse() {
  const focused = document.activeElement;
  return (
    explorer.open ||
    settings.open ||
    el("status").textContent !== "" ||
    (focused !== null && focused.matches("input, select, textarea"))
  );
}

function rest() {
  // Re-armed rather than dropped, so the bars still go once the dialog closes, the field is left,
  // or the message is replaced.
  if (chromeInUse()) {
    restTimer = setTimeout(rest, REST_DELAY);
    return;
  }
  document.body.classList.add("resting");
}

function wake() {
  document.body.classList.remove("resting");
  clearTimeout(restTimer);
  // Reduced motion asks for no fading, so there the chrome simply stays.
  restTimer = stillness.matches ? 0 : setTimeout(rest, REST_DELAY);
}

// `pointerdown` covers the click that lands without the mouse having moved.
for (const event of ["mousemove", "pointerdown", "keydown", "focusin"]) {
  document.addEventListener(event, wake, { passive: true });
}

// ---------------------------------------------------------------- wiring ---

el("keep").addEventListener("click", () => decide("keep"));
el("discard").addEventListener("click", () => decide("discard"));
el("undo").addEventListener("click", undo);
el("apply").addEventListener("click", apply);
el("source").addEventListener("change", (event) => setSource(event.target.value));
el("destination").addEventListener("change", (event) => setDestination(event.target.value));
// Each switch sends only itself, so one control never carries a stale reading of another.
for (const id of ["pair-raws", "search-subfolders", "pair-videos"]) {
  el(id).addEventListener("change", (event) =>
    run(() => call("settings", { [id.replaceAll("-", "_")]: event.target.checked })),
  );
}

el("browse").addEventListener("click", () => {
  explorer.showModal();
  browse(el("source").value || "~");
});
el("explorer-close").addEventListener("click", () => explorer.close());
el("explorer-choose").addEventListener("click", () => {
  explorer.close();
  if (browsing !== null) setSource(browsing);
});

el("open-settings").addEventListener("click", () => settings.showModal());
el("enter-focused").addEventListener("click", enterFocused);
el("leave-focused").addEventListener("click", leaveFocused);
el("toggle-zoom").addEventListener("click", toggleZoom);
el("settings-close").addEventListener("click", () => settings.close());

document.addEventListener("keydown", (event) => {
  if (explorer.open || settings.open || event.target.matches("input, select, textarea")) return;
  // Space belongs to the button that holds the focus.
  if (event.key === " " && event.target.matches("button")) return;
  const shortcuts = {
    ArrowLeft: () => decide("discard"),
    ArrowRight: () => decide("keep"),
    u: undo,
    // Nothing to look at closely when there is no photo, which is the same condition that leaves
    // the verdict buttons disabled.
    f: () => {
      if (!el("keep").disabled) enterFocused();
    },
    " ": () => {
      if (!el("keep").disabled) toggleZoom();
    },
    // Harmless outside focused mode, where it removes a class that is not set.
    Escape: leaveFocused,
  };
  const shortcut = shortcuts[event.key.length === 1 ? event.key.toLowerCase() : event.key];
  if (shortcut) {
    event.preventDefault();
    shortcut();
  }
});

paint(document.documentElement.dataset.theme);
fitStage();
wake();
run(() => call("state"));

// A run started before a reload goes on in the server, and its response went to the page that is
// gone.
call("progress")
  .then((progress) => {
    if (progress === null) return;
    report(describe(progress));
    // After `run`, which clears the status line as it starts.
    watchTransfer(async () => {
      await run(() => call("state"));
      report("The transfer has finished.");
    });
  })
  .catch(() => {});
