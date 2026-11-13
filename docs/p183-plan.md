# P183 plan: fleet sizing for a sustained wet line

Status: proposed and executable.

## Question

Given the now-working wet-cell kernel, what fleet is required to place a
full-height line before the fire arrives, with enough overlapping drops to
close the 100 m effect grid?

This is a logistics question, not a water-effect question.

## Reference

- 76-cell full-height line at x = 493,600 m.
- One drop covers about 0.39 of a 100 m cell at 1 mm.
- Two stacked drops per cell give about 0.78 mm, above the 0.75 mm target.
- Hold time: 60 min unless stated otherwise.
- Full-height prepositioned line control: **3,504 ha**.

## Experiment

For aircraft counts **3, 6, 12, 20, 50 and 100**:

1. schedule two drops per target around the 1,800-minute arrival;
2. measure per-cell wetness at arrival;
3. record mean/max lateness;
4. run native growth only at the smallest fleet that closes the line;
5. compare with the prepositioned 3,504 ha control.

## Metrics

- targets wet at arrival / 76;
- mean and maximum drop lateness;
- number of targets burned before wet;
- final area and area at fixed times.

## Falsification

- If no fleet up to 100 aircraft closes the line, the limiting factor is not
  fleet size but scheduling/effect geometry.
- If the line closes but native area does not fall, the native wet branch or
  barrier geometry is still wrong.
- If the line closes and area falls, fleet sizing is the operational question.

## Result

A 12-aircraft fleet is the smallest tested fleet that gets all 71 burnable
targets wet before arrival. Three aircraft reach 19/71; six reach 54/71. The
12-aircraft, 60-minute mission still ends at **5,325 ha**, so closure at arrival
is not persistence.

See [`p183-fleet.md`](p183-fleet.md).

## Stop rule

Stop when the minimum fleet that closes the line is identified. Do not run more
unordered delivery sweeps.
