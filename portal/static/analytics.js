/*
 * FRESH Fire Studio — anonymous event counters.
 *
 * No cookies, no user IDs, no persistent identifiers. One count per tab/session
 * for the page/scene class. If the counter service is unavailable, navigation
 * is unaffected.
 */
(() => {
  const namespace = "ubc-fresh-fire-studio";
  const path = window.location.pathname;
  let event = "portal";
  let slug = "";

  const scene = path.match(/\/scenes\/([^/]+)\/viewer\.html/);
  const caseMatch = path.match(/\/case\/([^/]+?)(?:\.html)?$/);
  if (scene) {
    event = "scene";
    slug = scene[1];
  } else if (caseMatch) {
    event = "case";
    slug = caseMatch[1];
  } else if (path.includes("/methods")) {
    event = "methods";
  } else if (path.includes("/pilot")) {
    event = "pilot";
  } else if (path.includes("/reel")) {
    event = "reel";
  }

  const key = "ff-hit-" + event + (slug ? "-" + slug : "");
  try {
    if (sessionStorage.getItem(key)) return;
    sessionStorage.setItem(key, "1");
  } catch (_) {
    // Private mode or disabled storage: still count once per page load.
  }

  const counter = event + (slug ? "-" + slug : "");
  const image = new Image();
  image.referrerPolicy = "no-referrer";
  image.src =
    "https://abacus.jasoncameron.dev/hit/" +
    encodeURIComponent(namespace) +
    "/" +
    encodeURIComponent(counter) +
    "?t=" +
    Date.now();
})();
