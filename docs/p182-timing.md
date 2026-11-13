# P182.4 full-height water line timing

Status: diagnostic timing and duration test.

## Results

All cases use the 76-row line at x = 493,600 m, 3 stacks per cell and 200
aircraft.

| Hold after drop | Wet cells | Native area |
| ---: | ---: | ---: |
| 60 min | 76 | 5,325 ha |
| 600 min | 76 | 5,325 ha |
| 22,200 min | 76 | 5,254 ha |
| Static non-burnable barrier | 76 | **3,504 ha** |

## Interpretation

A full-height water line does not reproduce the static barrier even when the
water is nominally permanent from the drop time.

The static barrier is applied from the beginning of the run. The water line is
built around the 1,800-minute front. The fire can reach and cross parts of the
line before the water is present, and the finite duration cases dry out before
the later growth.

The result is not a width problem. It is a **timing and persistence** problem:

- water must be present before the fire arrives;
- the line must remain closed through the entire arrival window;
- a one-time drop mission is not equivalent to a permanent firebreak.

## Artifacts

- `suppression/scenarios/2003-526-closed-barrier-76rows.json`
- `suppression/scenarios/2003-526-closed-barrier-76rows-600.json`
- `suppression/scenarios/2003-526-closed-barrier-76rows-permanent.json`
- corresponding native artifacts

## Next

The next experiment is a **sustained line-wetting schedule** from before the
first arrival through the last relevant arrival. If that still fails, the
native wet branch is the issue. If it contains, the requirement is operational
persistence, not a larger single mission.
