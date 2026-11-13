# Canadian wildfire studies: extraction notes

Local source files are in `data/ws4-studies/pdfs/` and are not committed.
These are adjacent to P179 suppression; they should not be mixed into the
suppression growth kernel without a separate design decision.

## Local files

| File | SHA-256 |
| --- | --- |
| `2023-Nicoletta-et-al-FireLossRate.pdf` | `ca2461c7d74bccb06aa7f54e547c5d4a617d2d52e51a368bf38386f98eb82f06` |
| `2026-Brunet-et-al-Helitack-Spatial-Optimization.pdf` | `e69f52efd35182eb5e928116a10f54d3988f3edaf46b850733a2eb1d3248feb2` |
| `2026-Moreno-et-al-Wildfire-Evacuation-Network.pdf` | `1d68f2c6b7c40c7ef45725d431c28ecccdf5c1ecfffa20299da37426472e624a` |
| `2026-Nicoletta-et-al-Fuel-Break-Placement.pdf` | `fe16ed22c50445a6748f7354500f83ebfbefdd364393c8b4e2422787e509f700` |

All four are open-access publications. The R package is public under the MIT
licence.

## FireLossRate — Nicoletta et al. 2023

Citation: Nicoletta, V., Chavardès, R.D., Abo El Ezz, A., Cotton-Gagnon, A.,
Bélanger, V., and Boucher, J. 2023. *FireLossRate: An R package to estimate the
loss rate of residential structures affected by wildfires at the Wildland Urban
Interface.* MethodsX 10:102238. DOI `10.1016/j.mex.2023.102238`.

Source code: <https://github.com/LFCFireLab/FireLossRate>.

### Loss-rate model

The package implements the Structural Wildfire Risk Framework from Abo El Ezz
et al. (2022).

Direct loss rate from fireline intensity (FLI):

```text
LR(%) = 4.94 × FLI^0.34
LR = 100 when FLI > 6,800 kW/m
```

For indirect exposure, the loss rate is multiplied by a normalized loss rate
based on distance from the fire edge (DFE):

```text
NLR = -0.21 × ln(DFE) + 1.37
```

Indirect exposure is limited to 500 m from the fire edge. The R code sets NLR
to 1 when distance is zero and uses the maximum LR among nearby fire cells for
each structure pixel.

The code defaults:

- `LRfactor = 4.94`
- `LRexp = 0.34`
- `NLRfactor = -0.21`
- `NLRcost = 1.37`
- `maxDist = 500 m`

### Outputs

For each fire or simulation:

- total structures;
- exposed structures;
- lost structures;
- average exposure loss rate;
- average community loss rate;
- spatial loss rate per structure pixel.

Worked example in the paper: 400 structures, 128 exposed, 25 lost, 20% average
exposure loss rate, 6% average community loss rate.

### Relevance to Fire Studio

This is a **community-impact layer**, not a suppression effect. It could later
consume the fire model's FLI and perimeter, but it must remain labelled as a
structure-loss estimate, not a validated prediction for a specific community.

The formula is simple enough to port to Python later if a structure layer is
added. The R package itself is MIT licensed.

## Helitack spatial optimization — Brunet et al. 2026

Citation: Brunet, F., Boucher, J., Bouchard, M., and Bélanger, V. 2026.
*Improving the efficiency of helitack crew deployment through spatial
optimization.* International Journal of Wildland Fire 35:WF26022.
DOI `10.1071/WF26022`. Open access, CC BY-NC-ND.

### Model

- maximal covering location problem (MCLP);
- fixed number of available deployment sites;
- maximize weighted coverage of pixels with high predicted head fire intensity
  (HFI);
- 113 km deployment radius, roughly a 30-minute flight for a Bell 206B;
- 60.25 km² pixels;
- HFI categories and weights, from low to extreme;
- 18 SOPFEU primary sites versus an extensive set of 94 potential sites.

The current SOPFEU heuristic deploys a crew when more than 40% of the area
within the 113 km radius has HFI above 2,001 kW/m. The optimization model
selects sites directly from predicted HFI.

### Evaluation

- 280 days in Quebec, 2018–2022;
- base scenario: 18 primary sites;
- extensive scenario: 94 sites;
- compared with historical deployment on the same days;
- blocked bootstrap confidence intervals.

Key results:

- base scenario total coverage increased by a mean daily difference of **473**
  (95% CI 409–546) and beat historical deployment on **261/280** days;
- extensive scenario increased by **1,132** (95% CI 987–1,282) over historical,
  and **659** (95% CI 515–817) over the base scenario;
- base scenario covered **133.7** more pixels per day than historical; the
  extensive scenario covered **225.7** more;
- the extensive scenario covered all 24 new fire starts in one example, versus
  21 for historical and base deployment.

### Relevance to P179

This directly supports the dispatch/basing layer:

- it is a **strategic site-selection** model, not a per-fire dispatch model;
- it uses HFI coverage as the objective, not suppression success;
- it demonstrates that expanding the candidate site set can matter more than
  reallocating among the existing sites;
- it is a good complement to Bookbinder–Martell queueing and MacLellan–Martell
  airtanker basing.

Do not turn the MCLP into a 3D animation. Use it to choose bases or evaluate a
base network, then let the dispatch queue assign individual tasks.

## Wildfire evacuation network — Moreno et al. 2026

Citation: Moreno, A., Bélanger, V., Cherkesly, M., and Rancourt, M.-È. 2026.
*Evacuation network design and planning under traffic congestion: An
application to wildfires in Canada.* Transportation Research Part E 213:104965.
DOI `10.1016/j.tre.2026.104965`. Open access, CC BY.

### Model

- Evacuation Network Design and Planning Problem under Traffic Congestion
  (ENDPT);
- mixed-integer programming;
- jointly chooses shelter locations, evacuation routes, lane allocations and
  evacuee flows;
- Cell Transmission Model for time-varying congestion, multiple periods,
  contraflow and capacity constraints;
- exact Branch-and-Benders-Cut solution.

### Findings

- static models that ignore traffic dynamics can underestimate evacuation time
  by up to **60%**;
- the 2023 Chibougamau evacuation is the case study;
- adding limited-capacity sheltering options can reduce traffic congestion by
  more than **95%** in the tested scenario;
- the model gives a lower bound on actual evacuation time because it assumes
  coordinated routing and traffic control.

### Relevance to Fire Studio

This is a separate **community evacuation layer**. It shares the fire perimeter
and road network but not the suppression resource queue. It should not be
rendered as suppression activity or presented as an operational evacuation
plan.

## Fuel break placement — Nicoletta et al. 2026

Citation: Nicoletta, V., Chavardès, R.D., Yemshanov, D., Bélanger, V.,
Cotton-Gagnon, A., and Boucher, J. 2026. *Optimizing fuel break placement to
mitigate wildland fire risk to communities.* Fire Ecology 22:133.
DOI `10.1186/s42408-026-00550-z`. Open access, CC BY.

### Model

Three coupled components:

1. Burn-P3 burn-probability simulation;
2. FireLossRate structural loss model;
3. network-based critical-node detection for fuel break placement.

The landscape is a graph of 2,510 fuel nodes. A fuel break removes a node and
its fire-spread connections. Costs vary by jurisdiction; the optimization
minimizes a weighted objective under a node-removal budget.

### Scenarios

- 198 scenarios;
- three spread-probability inputs: daily fire perimeters, escaping fires, final
  fire perimeters;
- three priorities: fire frequency, fire intensity, structure loss rate;
- two eligible areas: inside the jurisdiction only, or the whole landscape;
- eleven budgets: 10 to 250 nodes (0.4% to 10% of the network);
- no contiguity constraint on fuel breaks.

### Findings

- even modest budgets, around 10–50 treated nodes, can produce notable hazard
  or risk reduction;
- fuel breaks placed both inside and outside the jurisdiction generally
  outperform jurisdiction-only placement;
- optimal solutions tend to be nested as budgets increase, allowing incremental
  implementation;
- the model does not directly model fuel-break breaching by extreme fire or
  firebrand spotting; it uses a 50% fuel-cover assumption to address spotting.

### Relevance to Fire Studio

This is a **strategic fuel-treatment layer**, not suppression. It could later
generate treatment scenarios for the landscape or community view, but it should
not be conflated with a containment line built during an incident.

## Cross-cutting design notes

- Keep four layers separate:
  1. fire growth and suppression effects;
  2. resource dispatch and queueing;
  3. community structure loss;
  4. evacuation and fuel-break planning.
- The fireline intensity is the shared currency between Fire Studies 1–3.
- The road/network layer for evacuation is different from the suppression
  travel graph.
- All four papers are open access; the PDFs remain local and gitignored.

## Not yet retrieved

From the archive README:

- the earlier GERAD working paper record
  <https://www.gerad.ca/en/papers/G-2024-55>.

The other two listed as missing in the archive README are now present:
Brunet et al. 2026 and Moreno et al. 2026.
