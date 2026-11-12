/*
 * FRESH Fire Studio assistant drawer.
 * Same-origin on the edge; the permanent Pages build calls the public edge API.
 */
(() => {
  const endpoint =
    location.hostname === "ubc-fresh.github.io"
      ? "https://fresh-fire.01101.dev/api/ask"
      : "/api/ask";
  const panel = document.getElementById("assistant-panel");
  const log = document.getElementById("assistant-log");
  const backdrop = document.getElementById("assistant-backdrop");
  const input = document.getElementById("assistant-question");
  const form = document.getElementById("assistant-form");
  const submit = document.getElementById("assistant-submit");
  const status = document.getElementById("assistant-status");
  if (!panel || !log || !input || !form || !submit || !status) return;

  const history = [];
  let busy = false;

  function open() {
    panel.hidden = false;
    if (backdrop) backdrop.hidden = false;
    panel.classList.add("is-open");
    for (const button of document.querySelectorAll("[data-assistant-open]")) {
      button.setAttribute("aria-expanded", "true");
    }
    setTimeout(() => input.focus(), 50);
  }

  function close() {
    panel.hidden = true;
    if (backdrop) backdrop.hidden = true;
    panel.classList.remove("is-open");
    for (const button of document.querySelectorAll("[data-assistant-open]")) {
      button.setAttribute("aria-expanded", "false");
    }
  }

  function formatAnswer(text) {
    const holder = document.createElement("div");
    holder.textContent = text;
    return holder.innerHTML
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/^- (.+)$/gm, "• $1")
      .replace(/\n/g, "<br>");
  }

  function bubble(role, text) {
    const item = document.createElement("div");
    item.className = "assistant-message " + role;
    if (role === "assistant") item.innerHTML = formatAnswer(text);
    else item.textContent = text;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
    return item;
  }

  function ask(question) {
    if (busy) return;
    const cleaned = String(question || "").trim();
    if (cleaned.length < 3) {
      status.textContent = "Please enter a longer question.";
      return;
    }
    busy = true;
    submit.disabled = true;
    status.textContent = "Thinking…";
    bubble("user", cleaned);
    history.push({ role: "user", text: cleaned });
    input.value = "";

    fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: cleaned }),
    })
      .then(async (response) => {
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
          throw new Error(payload.detail || "assistant unavailable");
        }
        return payload;
      })
      .then((payload) => {
        const answer = payload.answer || "No answer returned.";
        bubble("assistant", answer);
        history.push({ role: "assistant", text: answer });
        status.textContent = "Answers are limited to the public portal context.";
      })
      .catch((error) => {
        status.textContent =
          "Assistant unavailable. Email gregory.paradis@ubc.ca if you need a reply.";
        bubble(
          "assistant error",
          "I could not reach the assistant. The portal pages and 3D scenes still work."
        );
        console.warn("FRESH assistant error", error);
      })
      .finally(() => {
        busy = false;
        submit.disabled = false;
      });
  }

  for (const button of document.querySelectorAll("[data-assistant-open]")) {
    button.addEventListener("click", (event) => {
      event.preventDefault();
      open();
      try {
        if (!sessionStorage.getItem("ff-ask-counted")) {
          sessionStorage.setItem("ff-ask-counted", "1");
          const image = new Image();
          image.referrerPolicy = "no-referrer";
          image.src =
            "https://abacus.jasoncameron.dev/hit/ubc-fresh-fire-studio/ask?t=" +
            Date.now();
        }
      } catch (_) {}
    });
  }

  document.getElementById("assistant-close")?.addEventListener("click", close);
  document.getElementById("assistant-backdrop")?.addEventListener("click", close);
  document.getElementById("assistant-clear")?.addEventListener("click", () => {
    history.length = 0;
    log.replaceChildren();
    status.textContent = "Ask about the fire, the model, the VRI pilots, or a pilot.";
    input.focus();
  });
  for (const prompt of document.querySelectorAll("[data-assistant-prompt]")) {
    prompt.addEventListener("click", () => {
      input.value = prompt.getAttribute("data-assistant-prompt") || "";
      input.focus();
    });
  }
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    ask(input.value);
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      ask(input.value);
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) close();
  });
})();
