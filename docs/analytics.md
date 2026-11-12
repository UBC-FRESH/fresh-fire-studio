# Anonymous analytics

The portal records only anonymous page and scene-open counts.

- No cookies.
- No user IDs, device IDs, or persistent identifiers.
- One count per tab/session for each event.
- Counting failure never blocks the portal.

Implementation: `portal/static/analytics.js`.

## Events

| Event key | Trigger |
|---|---|
| `portal` | landing page |
| `case-<slug>` | case page |
| `scene-<slug>` | 3D viewer |
| `methods` | methods page |
| `pilot` | pilot page |
| `bc` | BC landing variant |
| `cfs` | CFS landing variant |
| `reel` | 70-second reel page |

The counter service is Abacus:

```bash
curl https://abacus.jasoncameron.dev/get/ubc-fresh-fire-studio/portal
curl https://abacus.jasoncameron.dev/get/ubc-fresh-fire-studio/scene-cfsds-2003-526
```

The namespace is `ubc-fresh-fire-studio`. Counts are public aggregate integers;
there is no per-visitor data.
