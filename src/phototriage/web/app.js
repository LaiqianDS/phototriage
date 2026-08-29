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
  // A crash inside the server answers with plain text instead of `detail`, and
  // the parser error would otherwise reach the user in place of the failure.
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(payload?.detail ?? response.statusText);
  }
  return payload;
}

// Written to both places, because focused mode hides the bar the first one
// lives in and an error nobody can see is the same as no error at all. Only one
// of the two is ever in the accessibility tree, so nothing is announced twice.
function report(message, isError = false) {
  el("status").textContent = message;
  el("status").classList.toggle("error", isError);
  el("hud-status").textContent = message;
  el("hud-status").classList.toggle("error", isError);
}

/**
 * Run one API action at a time.
 *
 * A burst of keystrokes would otherwise send several decisions against the
 * same image before the first response arrives.
 */
let pending = false;
async function run(action) {
  if (pending) return;
  pending = true;
  document.body.setAttribute("aria-busy", "true");
  // The previous message belonged to the previous action. Clearing it here also
  // lets the chrome rest again, which a message on screen holds back.
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
  // The tally and the kept count reach the bar and the focused-mode pill alike.
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

  const chosen = state.source !== null;
  el("idle").hidden = chosen;
  el("empty").hidden = !chosen || state.total > 0;
  el("done").hidden = !chosen || state.total === 0 || state.current !== null;
  el("viewer").hidden = state.current === null;
  el("filename").textContent = state.current ?? "";
  el("hud-filename").textContent = state.current ?? "";

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
  el("undo").disabled = state.reviewed === 0;
  el("apply").disabled = state.kept === 0;
  el("destination").disabled = !chosen;
}

const decide = (verdict) => run(() => call("decide", { verdict }));
const undo = () => run(() => call("undo", {}));

const setSource = (path) => run(() => call("source", { path }));
const setDestination = (path) => run(() => call("destination", { path }));
const setPairRaws = (pairRaws) => run(() => call("settings", { pair_raws: pairRaws }));

function apply() {
  const mode = el("mode-move").checked ? "move" : "copy";
  const verb = mode === "copy" ? "Copiar" : "Mover";
  if (!confirm(`¿${verb} las imágenes mantenidas al destino?`)) return;
  run(async () => {
    report("Procesando...");
    const { transferred, destination } = await call("apply", { mode });
    report(`${transferred} archivos en ${destination}`);
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
    theme === "dark" ? "Cambiar a tema claro" : "Cambiar a tema oscuro",
  );
}

// Until the button is used the system decides, and keeps deciding when it
// changes. A stored choice wins from then on.
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

/**
 * Reserve the room the chrome occupies.
 *
 * The bars and the verdict buttons float, so without this the photo would run
 * underneath them and lose its top and bottom edges. Their heights depend on
 * their contents and on how the text wraps, so they are measured rather than
 * guessed.
 */
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

// --------------------------------------------------------- focused mode ---

/**
 * Give the photo the whole window.
 *
 * The bars rest; here they go. What is left is what the decision in front of
 * the user needs, so the controls that belong to before it and after it, the
 * source folder and the transfer, stay behind.
 *
 * The browser goes fullscreen along with it when it will. The request needs a
 * user gesture and a document that is allowed to ask, and neither is worth
 * refusing focused mode over: a maximised window is the fallback.
 */
async function enterFocused() {
  document.body.classList.add("focused");
  try {
    await document.documentElement.requestFullscreen();
  } catch {
    // Windowed focused mode is the fallback, not a failure to report.
  }
}

function leaveFocused() {
  document.body.classList.remove("focused");
  if (document.fullscreenElement !== null) document.exitFullscreen();
}

// Escape leaves fullscreen without the keypress ever reaching the page, and the
// window chrome offers its own way out as well. So the class follows the
// browser rather than the other way round.
document.addEventListener("fullscreenchange", () => {
  if (document.fullscreenElement === null) document.body.classList.remove("focused");
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
    el("explorer-count").textContent = `${listing.images} imágenes aquí`;
    el("explorer-count").classList.remove("error");
    const items = listing.folders.map((name) => folderItem(name, join(listing.path, name)));
    if (listing.parent !== null) {
      items.unshift(folderItem("Subir un nivel", listing.parent, true));
    }
    if (listing.folders.length === 0) {
      items.push(emptyItem("No hay subcarpetas."));
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

/** Whether hiding the bars right now would take something away from the user.
 *
 * A focus ring is not on this list. Closing a dialog restores focus to the
 * button that opened it and leaves it `:focus-visible`, which here would have
 * kept the chrome up for good; the stylesheet holds up only the one bar that
 * carries the ring, and stops as soon as the ring moves.
 */
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
  // Re-armed rather than dropped, so the bars still go once the dialog closes,
  // the field is left, or the message is replaced.
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
el("pair-raws").addEventListener("change", (event) => setPairRaws(event.target.checked));

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
el("settings-close").addEventListener("click", () => settings.close());

document.addEventListener("keydown", (event) => {
  if (explorer.open || settings.open || event.target.matches("input, select, textarea")) return;
  const shortcuts = {
    ArrowLeft: () => decide("discard"),
    ArrowRight: () => decide("keep"),
    u: undo,
    // Nothing to look at closely when there is no photo, which is the same
    // condition that leaves the verdict buttons disabled.
    f: () => {
      if (!el("keep").disabled) enterFocused();
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
