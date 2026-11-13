# P179.2a time-aware effect schedule proof

Status: diagnostic. This adds a time dimension to the P179 line/drop effects and
checks that the mask changes over a simulation. It is not a calibrated
suppression result.

## What changed

P179.1 applied the whole containment line at minute zero. P179.2a adds:

- `suppression/temporal.py` — line progress, partial line geometry, held /
  breached / abandoned states, drop decay, active-effect queries and timeline
  breakpoints;
- `suppression/scenarios/2003-526-temporal-proof.json` — a synthetic line built
  over 1,440 minutes;
- `scripts/prove_temporal_suppression_2003_526.py` — a 60-minute chunked harness
  around the static P177 kernel;
- `suppression/proofs/2003-526-temporal.json` — the result artifact.

## Method

The P177 kernel still accepts only a static containment mask. The harness steps
the `2003_526` simulation in 60-minute chunks:

1. at the start of each chunk, ask the P179 schedule which line cells exist;
2. remove those cells from the burnable grid for that chunk;
3. seed the chunk with all previously burned cells;
4. run the P177 growth kernel for 60 minutes;
5. union the new burned cells into the next chunk's seed.

Seeding the whole burned area is an approximation. It preserves the burned
perimeter, but it resets the arrival time of boundary cells at each chunk.

## Line schedule

The diagnostic line runs north–south at x = 493,200 m, is 100 m wide, and is
built linearly over 24 hours.

| Time | Line cells | Burned area |
| ---: | ---: | ---: |
| 0 min | 0 | 1 ha |
| 60 min | 8 | 9 ha |
| 240 min | 28 | 16 ha |
| 720 min | 78 | 16 ha |
| 1,440 min | 152 | 16 ha |
| 22,200 min | 152 | 3,112 ha |

The line reaches full length well before the main growth phase. Most of the
growth happens after 18,000 minutes.

## Final comparison

| Run | Simulated area | IoU |
| --- | ---: | ---: |
| Free burn | 5,325 ha | 0.096 |
| Time-aware line | 3,112 ha | 0.134 |
| Static full line (P179.1) | 3,113 ha | 0.134 |
| Observed | 520 ha | — |

The time-aware run reduces area by **2,213 ha (41.6%)** relative to free burn.
It is within **1 ha** of the static full-line run, with an IoU difference of
**0.00004**.

That near-match is expected: the line is complete at 1,440 minutes, while most
growth occurs after 18,000 minutes. The proof validates the schedule and the
chunked hand-off, not a case where a late line fails to stop an arriving fire.

## What this proves

- A scenario can be queried for its active line and drop effects at any time.
- Line cells grow from 0 to 152 as construction proceeds.
- Drop masks disappear after their decay window.
- A time-aware effect mask reaches the fire kernel and changes final area.
- The chunked approximation stays within 1 ha of the static full-line result.

## What this does not prove

- It does not test a line that arrives after the fire front.
- It does not test a breach or re-ignition event.
- It does not feed drop moisture or coverage into fire growth.
- The P177 kernel is still static within each chunk.
- Seeding all burned cells at each chunk is not a native time-dependent kernel.
- The simulated fire remains far larger than the observed 520 ha fire.

## Reproduce

```bash
python scripts/prove_temporal_suppression_2003_526.py \
  --ws4-root ../.opencode/tmp/opencode/ws4-p177
pytest -q tests/
```


## P179.3 follow-up

The native single-run adapter in [`p179-3-native-proof.md`](p179-3-native-proof.md)
returns **5,183 ha** for the same 24-hour line build. The chunked result above
is **3,112 ha**, so the chunk harness overestimates containment when the line
is built slowly. Use the native run for timing conclusions; keep the chunked
run as a historical approximation.

## Next

- Add a native time-dependent containment mask to the growth kernel rather than
  rebuilding the seed every chunk.
- Couple drop moisture/coverage and decay to fuel availability.
- Add a deliberately late line and a breach to test failure modes.
- Then add resource dispatch and queueing on top of the effect schedule.
