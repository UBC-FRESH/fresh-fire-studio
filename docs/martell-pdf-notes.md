# P179 PDF extraction notes

Source archive: `tmp/P179-publications.zip` (outside the repository).
Extracted locally to `data/martell/pdfs/`; the PDFs are not committed.

Status: five verified PDFs mined on 2026-11-13. These notes are extraction
notes for the P179 data model. They are not a substitute for reading the full
papers.

## Local files and checksums

| File | SHA-256 |
| --- | --- |
| `1979-Bookbinder-Martell-Helicopter-Allocation.pdf` | `5cf435c14bc3f20e61426e05f958b95fb6d7fbb7d2929c5bc8ae8fd97b48e9da` |
| `2015-Martell-Decision-Support-Review.pdf` | `8d8b1ed7e81eb9aa5fe4d41a52ce8dff3ff93175c9f68434d70058ea15ed8c92` |
| `2022-Van-Wagner-Taylor-Theoretical-Amounts-of-Water.pdf` | `c77e7874f001b10f02695fa081290e521419490ba8cbfa860b34bb359a18d3cd` |
| `2022-Wheatley-et-al-Airtanker-Dispatch-Author-Manuscript.pdf` | `e8db216a3d5b18b7d6caac77c362e6461eabbec7d79c6bfa9907af30b46cf78b` |
| `2023-McFayden-et-al-Airtanker-Drop-Effectiveness.pdf` | `8a7e5a86ce44636568e4e40eac2c4d10feb00e168ec092106a1cd11dac9cf4cb` |

## Metadata corrections

- The 2015 control-time paper is **Morin, Albert-Green, Woolford and Martell**,
  not Wheatley et al. DOI `10.1071/WF14158`.
- McFayden et al. 2023 is the Canadian Forest Service information report
  **GLC-X-35**, *Reference Guide to the Drop Effectiveness of Skimmer and
  Rotary Wing Airtankers*.
- Van Wagner and Taylor 2022 is the Canadian Forest Service information report
  **BC-X-458**, *Theoretical Amounts of Water to Put Out Forest Fires*. It is
  an open Government of Canada publication.
- The Wheatley et al. airtanker-dispatch file is an author manuscript
  (`cjfr-2022-0225.R1`), not the publisher's final typeset version.

## Bookbinder & Martell 1979

*Time-dependent queueing approach to helicopter allocation for forest fire
initial attack.* INFOR 17(1), February 1979.

Model:

- each helitack base is a multi-channel queue;
- fires are customers; helicopters are servers;
- arrivals are a non-stationary Poisson process;
- service is approximately exponential and includes loading, transport to the
  fire, return to base and refuelling;
- service discipline is first-in, first-out;
- one queue operates at each base, served by the first available helicopter;
- a dynamic program allocates available helicopters to bases to minimize a
  damage-weighted maximum expected queue length.

The example allocates six helicopters among three bases. The paper explicitly
suggests extending the queue to land-based retardant bombers, with one sortie
per fire and multiple aircraft treated as one server.

**P179 use:** service times must include the whole aircraft/crew cycle, not just
the drop or line segment. The dispatch layer needs time-varying arrival rates
and resource competition, not a fixed response time.

## Martell 2015

*A Review of Recent Forest and Wildland Fire Management Decision Support
Systems Research.* Current Forestry Reports 1:128–137.

Main points for P179:

- separate strategic, tactical and operational decisions;
- airtanker acquisition and home-basing are strategic; daily deployment is
  tactical; dispatch and use on the fire line are operational;
- initial-attack simulation and optimization models exist, but many have only
  simple links to the subsequent suppression activities;
- the review calls for better integration between deployment models and
  fireline effectiveness, and for better data;
- initial attack is defined by the early suppression force; escaped fires move
  into large-fire management.

**P179 use:** keep the fast statistical/queueing layer separate from the spatial
fireline layer, but connect them through the same resource and task events.

## Morin, Albert-Green, Woolford & Martell 2015

*The use of survival analysis methods to model the control time of forest fires
in Ontario.* IJWF. DOI `10.1071/WF14158`.

This is the control-time paper previously misattributed to Wheatley. It belongs
in the IA/control-time layer, not the airtanker dispatch layer. The full PDF is
still missing from the local set.

## Wheatley et al. 2022 — airtanker dispatch

*Modelling decisions concerning the dispatch of airtankers for initial attack
on forest fires in Ontario, Canada.* CJFR, manuscript `cjfr-2022-0225.R1`.

Data:

- fire-report model: n = 10,546 observations, 3,670 fires with air attack;
- initial-attack model: n = 10,521 observations, 3,664 fires with air attack;
- two-part Poisson hurdle model: a binary zero hurdle and a zero-truncated
  Poisson count model.

Discrimination:

| Model | Training ROC | Testing ROC | Testing Brier |
| --- | ---: | ---: | ---: |
| Fire-report model | 0.70 | 0.68 | 0.20 |
| Initial-attack model | 0.83 | 0.82 | 0.16 |

The initial-attack model uses information available when IA begins: fire size,
observed rate of spread, cause, FWI and fuel volatility. The strongest
covariates in the zero-hurdle component include:

- `Fsize` (transformed size at IA): coefficient 1.98;
- observed ROS 2–5 m/min: 1.03;
- observed ROS 6–10 m/min: 1.42;
- observed ROS 11+ m/min: 2.27;
- lightning cause: 1.02;
- log FWI: 0.38;
- moderate fuel volatility: 0.53; high volatility: 0.72.

The model underpredicts when more than two airtankers are dispatched, which the
authors interpret as risk-averse dispatch behaviour.

**P179 use:** implement a two-stage dispatch probability/count model. Do not
regress success on water volume; harder fires receive more effort.

## Van Wagner & Taylor 2022 — water requirements

*Theoretical Amounts of Water to Put Out Forest Fires.* Canadian Forest Service
Information Report BC-X-458.

Three mechanisms:

1. quenching the flame;
2. cooling hot fuel in the flaming zone;
3. wetting unburned fuel ahead of the fire.

The report uses a heat balance in which most cooling comes from evaporation.
Key result: water depth increases much less than linearly with fireline
intensity. The approximate depth forms in Appendix 1 include:

- quenching: `Dw = 3.84 I^(2/3) × 10^-4`;
- cooling hot fuel: `Dw = 0.226 W1`;
- wetting fuel ahead: `Dw = 6.39 I^(2/3) i × 10^-5 / R`.

`I` is fireline intensity in kcal/s·m; convert to kW/m by multiplying by 4.184.
The report's nominal examples, at 100% efficiency:

| Intensity | Quench depth | Cool depth | Wet depth |
| ---: | ---: | ---: | ---: |
| 100 kcal/s·m (≈419 kW/m) | 0.008 mm | 0.28 mm | 0.31 mm |
| 1,000 kcal/s·m (≈4,184 kW/m) | 0.038 mm | 0.56 mm | 0.57 mm |
| 10,000 kcal/s·m (≈41,840 kW/m) | 0.18 mm | 1.13 mm | 1.07 mm |

**P179 use:** derive a required `coverage_l_m2` (1 mm = 1 L/m²) from intensity
and fuel load, then apply an efficiency factor. Do not use a fixed water depth
for every fire.

## McFayden et al. 2023 — airtanker drop effectiveness

*Reference Guide to the Drop Effectiveness of Skimmer and Rotary Wing
Airtankers.* Canadian Forest Service Information Report GLC-X-35.

Key structure:

- drop patterns are nested depth contours, not uniform rectangles;
- 1 mm water depth across 1 m² equals 1 L/m²;
- several drops may need to be stacked to achieve uniform coverage;
- a drop is assumed to hold for at least one hour when it reduces the
  combustion zone to smouldering and is not breached;
- breach occurs when the flame front is wider than half the drop width or the
  flame length is greater than half the drop width on the unburned side;
- effective drop size shrinks as fire intensity rises.

CL-415 cycle example from Table 7-1: blended speed 158 KIAS plus a
3.0-minute cycle increment. At 5 NM (9 km) from water, Table 7-2 gives about
12 drops/hour; Table 7-3 gives about 60,000 L/hour with no canopy loss.

C-2 full-canopy examples:

- at 300–900 kW/m, CL-415 effective drop is about 90 × 40 m;
- at 1,300 kW/m, about 70 × 30 m and requires 0.75 mm;
- one CL-415 drop can hold 100 m of C-2 line up to 900 kW/m;
- at 1,300 kW/m, two drops are needed for 100 m;
- at 3,200 kW/m, the guide indicates breaching for a single CL-415 drop.

**P179 use:** replace the single drop rectangle with nested coverage contours,
stacking and breach logic. The `coverage_l_m2` field is the right physical
quantity, but the rasterizer must preserve depth layers.

## What this changes in P179

1. **Dispatch:** use full resource cycles and time-varying queue arrival rates.
2. **Airtanker dispatch:** use two-stage probability/count models, not a fixed
   number of tankers.
3. **Drop effects:** model depth contours, stacking and breach thresholds.
4. **Water requirements:** derive required depth from fireline intensity and
   fuel load; keep efficiency factors explicit.
5. **Attribution:** cite Morin et al. for control time, McFayden et al. for the
   drop guide, and Van Wagner & Taylor for water depth.

## Still missing

The local set does not yet contain:

- Martell 1982, operational-research review;
- Martell et al. 1984, initial-attack resources;
- MacLellan & Martell 1996, airtanker basing;
- Hirsch & Martell 1996, crew productivity;
- Hirsch, Corey & Martell 1998, expert-judgment crew effectiveness;
- Podur & Martell 2007, growth/suppression simulation;
- Martell 2011, Ontario DSS reflections;
- Morin et al. 2015, control time;
- Wheatley et al. 2022, initial-attack success;
- Wheatley 2024, doctoral thesis.

The 2024 thesis and Martell 2011 are already available in the workspace outside
this local set; do not treat every missing item as paywalled.
