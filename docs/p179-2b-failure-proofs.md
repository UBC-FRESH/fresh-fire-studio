# P179.2b failure proofs: breach and late arrival

Status: diagnostic. These two runs test whether the time-aware P179 schedule can
represent a line that fails, rather than only a line that is present from the
start.

The runs use the same 60-minute chunked harness as
[`p179-2-proof.md`](p179-2-proof.md). The line is the same synthetic 100 m
north–south barrier.

## Breach

Scenario: `suppression/scenarios/2003-526-breach-proof.json`

- line built from minute 0 to 1,440;
- line held at 152 cells through minute 7,140;
- breached at minute 7,200;
- no line after the breach.

| Time | Line cells | Burned area |
| ---: | ---: | ---: |
| 1,440 min | 152 | 16 ha |
| 7,140 min | 152 | 609 ha |
| 7,200 min | 0 | 609 ha |
| 22,200 min | 0 | 5,323 ha |

The final area is **5,323 ha**, within **2 ha** of the 5,325 ha free burn. The
line delayed growth while it held, but once breached the fire recovered almost
the entire free-burn area.

## Late arrival

Scenario: `suppression/scenarios/2003-526-late-line-proof.json`

- line construction begins at minute 18,000;
- line reaches 152 cells at minute 19,440;
- the fire has already crossed the barrier by then.

| Time | Line cells | Burned area |
| ---: | ---: | ---: |
| 18,000 min | 0 | 3,556 ha |
| 19,440 min | 152 | 4,525 ha |
| 22,200 min | 152 | 5,323 ha |

The late line reduces final area by only **2 ha (0.04%)** relative to free
burn. A line that arrives after the fire front has passed does not contain it.

## What this proves

- The schedule represents a line that holds and is then breached.
- Removing a line cell at a breach time changes the fire trajectory.
- The schedule represents a line that is built after the fire has grown.
- Late arrival produces essentially no containment benefit in this case.

## Limits

- The P177 kernel is static inside each 60-minute chunk.
- The harness seeds every chunk with all previously burned cells.
- The line is synthetic and the breach is scripted.
- Drop moisture and decay are not coupled to growth.
- The 2 ha difference from free burn is a chunking artifact; it is not a
  validated effectiveness estimate.

## Reproduce

```bash
python scripts/prove_temporal_suppression_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177 \
  --scenario suppression/scenarios/2003-526-breach-proof.json \
  --out suppression/proofs/2003-526-breach.json

python scripts/prove_temporal_suppression_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177 \
  --scenario suppression/scenarios/2003-526-late-line-proof.json \
  --out suppression/proofs/2003-526-late-line.json

pytest -q tests/
```

Artifacts:

- `suppression/proofs/2003-526-breach.json`
- `suppression/proofs/2003-526-late-line.json`

## Next

The failure proofs make the case for a native time-dependent growth kernel.
The chunked seed approximation is adequate for diagnostics, but it cannot model
arrival times, fireline intensity along a moving front, or re-ignition
precisely.
