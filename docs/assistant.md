# Assistant

The three main pages (`/`, `/bc`, `/cfs`) have a `+ Ask` button that opens the
same-page assistant drawer.

## Behaviour

- Same-origin on the edge: `POST /api/ask`.
- On the GitHub Pages build: `POST https://fresh-fire.01101.dev/api/ask`.
- No provider key is sent to the browser.
- The backend runs the local `opencode` CLI with the read-only `fire-guide`
  agent in `opencode.json`.
- The agent can read the public workspace but cannot edit files, run shell
  commands, fetch the web, or delegate.
- Questions are capped at 1,200 characters and clients are rate-limited to
  8 questions per minute.
- If the edge is unavailable, the drawer shows a clear error and the static
  portal continues to work.

## Context

The assistant prompt covers:

- the six benchmark fires;
- observed extent versus model extent;
- synthetic tree placement and LOD;
- model limits and validation caveats;
- the G50872 and G50266 VRI pilots;
- public contact details.

It is explicitly told not to invent numbers or claim operational prediction,
regional calibration, or measured inventory.

## Files

- `portal/assistant.py` — subprocess bridge and prompt context
- `portal/static/assistant.js` — drawer, history, quick prompts, fallback
- `opencode.json` — read-only `fire-guide` agent
- `portal/app.py` — `/api/ask`, CORS, and rate limiting
