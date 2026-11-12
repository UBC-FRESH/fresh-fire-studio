# Paywalled fire-suppression literature: search prompt and retrieval queue

This is the copy-paste search brief for the fire-suppression papers the FRESH
Fire Studio project still needs. It is a **retrieval queue**, not a claim that
every item is paywalled.

Access rules:

- Use your own UBC Library session in your own browser.
- Do not paste CWL passwords, session cookies, API keys, or MFA codes into chat.
- Do not use Sci-Hub, shadow libraries, credential sharing, or publisher
  scraping that bypasses access control.
- Prefer a legal open copy, then UBC Library full text, then interlibrary loan.
- Keep licensed PDFs local in `data/martell/pdfs/`; do not commit them to the
  public repository.

Already read and excluded from the queue:

- Wheatley, M.J. 2024. *Forest Fire Suppression Effectiveness in the Canadian
  Boreal Forest.* PhD thesis, University of Toronto. Open.
- Martell, D.L. 2011. The development and implementation of forest fire
  management decision support systems in Ontario: personal reflections.
  *MCFNS* 3(1): 18–26. Open.
- Murphy, P.J. 1985. *Methods for evaluating the effects of forest fire
  management in Alberta.* PhD thesis, University of British Columbia.
  DOI: `10.14288/1.0075312`. Open through UBC Open Collections.

---

## Master search prompt

Copy this block into a research assistant or literature-search session.

```text
You are helping the UBC FRESH Fire Studio team build a legally accessible
reading queue for process-based wildland fire suppression and response.

Mission: for every target in the manifest below, find the best legal access
route and enough metadata to retrieve it through UBC Library.

Rules:
1. Do not bypass paywalls, logins, CAPTCHAs, or publisher access controls.
2. Do not ask for or use CWL passwords, session cookies, API keys, or MFA codes.
3. Search in this order:
   a. exact title and DOI in UBC Library;
   b. OpenAlex, Crossref, Unpaywall, and Google Scholar for legal open copies;
   c. publisher page for volume, issue, pages, licence, and author manuscript;
   d. interlibrary loan if no full text is available.
4. Distinguish "open access", "UBC full text", "publisher paywall", and
   "metadata only".
5. Do not invent DOIs, page ranges, or author lists. Mark uncertain metadata.

For each target return:
- full citation;
- DOI or stable URL;
- publisher and likely access route;
- one-sentence relevance to suppression modelling;
- exact search string that found it;
- whether a PDF is legally downloadable now.

Priorities:
1. Simulation and containment architecture.
2. Initial-attack success, control time, and crew productivity.
3. Airtanker and helicopter dispatch, queueing, and basing.
4. Drop effectiveness, water depth, and fireline hold.
5. Reviews that connect tactical effects to landscape outcomes.

Do not summarize papers you cannot access. Do not treat a search-result snippet
as full text.
```

---

## Search query pack

Use exact-title searches first, then DOI lookup in UBC Library.

### Simulation, containment, and decision support

```text
"A simulation model of the growth and suppression of large forest fires in Ontario" Podur Martell
"An evaluation of forest fire initial attack resources" Martell
"A review of operational research studies in forest fire management" Martell
"A review of recent forest and wildland fire management decision support systems research" Martell
```

### Initial attack, control time, and crews

```text
"A review of initial attack fire crew productivity and effectiveness" Hirsch Martell
"Using expert judgment to model initial attack fire crew effectiveness" Hirsch Corey Martell
"The use of survival analysis methods to model the control time of forest fires in Ontario" Wheatley
"Factors that affect the timing of the dispatch of initial attack resources" Wheatley
```

### Helicopters, airtankers, and dispatch

```text
"Time-dependent queueing approach to helicopter allocation for forest fire initial attack" Bookbinder Martell
"Basing airtankers for forest fire control in Ontario" MacLellan Martell
"The use of aircraft tracking GPS data to develop models of the use of airtankers" Wheatley
"Modelling decisions concerning the dispatch of airtankers for initial attack in Ontario" Wheatley
"Modelling initial attack success on forest fires suppressed by air attack in Ontario" Wheatley
"Predicting daily initial attack aircraft targets in British Columbia" Wheatley
```

### Drop effectiveness, water depth, and fireline hold

```text
"Assessing wildland fire suppression effectiveness with infrared imaging on experimental fires" Wheatley
"Reference Guide to the Drop Effectiveness of Skimmer and Rotary Wing Airtankers" McFayden
"Theoretical amounts of water to put out forest fires" Van Wagner Taylor
"Empirical models of initial attack fire behaviour reduction by skimmer" Wheatley Wotton
```

### Optional adjacent material

```text
"Large airtanker use and outcomes in suppressing wildland fires" Calkin
"airtanker drop" "fire behaviour" "drop effectiveness"
"initial attack" "fireline production" "suppression effectiveness" Canada
```

---

## Target manifest

The DOIs below are the current project list. Verify each record before use; a DOI
resolves metadata, not necessarily full text.

| Priority | Citation | DOI / identifier | Likely access | Why it matters |
| ---: | --- | --- | --- | --- |
| 1 | Podur & Martell 2007. A simulation model of the growth and suppression of large forest fires in Ontario. *IJWF* 16: 285–294. | `10.1071/wf06107` | CSIRO / UBC | Discrete-event escape, growth, suppression and resource scenarios. |
| 1 | Martell et al. 1984. An evaluation of forest fire initial attack resources. *Interfaces* 14(5): 20–32. | `10.1287/inte.14.5.20` | INFORMS / UBC | IA simulation and resource acquisition. |
| 1 | Bookbinder & Martell 1979. Time-dependent queueing approach to helicopter allocation for forest fire initial attack. *INFOR*. | `10.1080/03155986.1979.11731717` | Taylor & Francis / UBC | Queueing model for helicopter deployment. |
| 1 | MacLellan & Martell 1996. Basing airtankers for forest fire control in Ontario. *Operations Research* 44(5): 677–686. | `10.1287/opre.44.5.677` | INFORMS / UBC | Airtanker home-basing optimization. |
| 1 | Hirsch & Martell 1996. A review of initial attack fire crew productivity and effectiveness. *IJWF* 6: 199–215. | `10.1071/wf9960199` | CSIRO / UBC | Crew productivity and effectiveness thresholds. |
| 1 | Hirsch, Corey & Martell 1998. Using expert judgment to model initial attack fire crew effectiveness. *Forest Science* 44(4): 539–549. | `10.1093/forestscience/44.4.539` | Oxford / UBC | Elicited crew effectiveness and line production. |
| 1 | Wheatley et al. 2015. The use of survival analysis methods to model the control time of forest fires in Ontario. *IJWF*. | `10.1071/wf14158` | CSIRO / UBC | Control-time distributions and covariates. |
| 2 | Wheatley et al. 2018. Factors that affect the timing of the dispatch of initial attack resources. *IJWF*. | `10.1071/wf18058` | CSIRO / UBC | Dispatch delay and daily fire load. |
| 2 | Wheatley et al. 2022a. Modelling decisions concerning the dispatch of airtankers for initial attack in Ontario. *CJFR*. | `10.1139/cjfr-2022-0225` | Canadian Science Publishing / UBC | Hurdle dispatch models; FWI, fuel, ROS, size, cause. |
| 2 | Wheatley et al. 2022b. Modelling initial attack success on forest fires suppressed by air attack in Ontario. *IJWF*. | `10.1071/wf22006` | CSIRO / UBC | IA success; airtanker effort; ROC. |
| 2 | Wheatley et al. 2019. The use of aircraft tracking GPS data to develop models of the use of airtankers. *INFOR*. | `10.1080/03155986.2019.1706398` | Taylor & Francis / UBC | Spatial queueing, service times, turn-around. |
| 2 | 2022. Predicting daily initial attack aircraft targets in British Columbia. *IJWF*. | `10.1071/wf21090` | CSIRO / UBC | BC-specific aircraft IA demand. |
| 2 | 2025. Assessing wildland fire suppression effectiveness with infrared imaging on experimental fires. *IJWF*. | `10.1071/wf24161` | CSIRO / UBC | Water delivery, ROS/intensity reduction and hold time. |
| 3 | Martell 1982. A review of operational research studies in forest fire management. *CJFR* 12: 119–140. | `10.1139/x82-020` | Canadian Science Publishing / UBC | Classic OR framing. |
| 3 | Martell 2015. A review of recent forest and wildland fire management decision support systems research. *Current Forestry Reports* 1: 128–137. | `10.1007/s40725-015-0011-y` | Springer / UBC | Modern DSS lessons. |
| 3 | McFayden et al. 2023. Reference Guide to the Drop Effectiveness of Skimmer and Rotary Wing Airtankers. | Citation incomplete; verify | Report / web | Drop patterns and tanker-specific effectiveness. |
| 3 | Van Wagner & Taylor 2022. Theoretical amounts of water to put out forest fires. | Government of Canada publication; verify | Open government report | Water mass/depth needed for quenching, cooling and fuel wetting. |

Notes:

- The McFayden item may be a reference guide rather than a journal article.
  Verify the exact author list, year and publisher before citing it.
- The Van Wagner and Taylor item is a federal publication with a public
  catalogue record; confirm the exact title and date on the Government of
  Canada page. The project plan previously called it "water-depth models"; the
  catalogue title is *Theoretical amounts of water to put out forest fires*.
- The 2022 BC aircraft paper and the 2025 IR paper need full author lists from
  the publisher record.

---

## What to extract from each PDF

For the suppression module, extract:

- state variables, decision variables, and time step;
- IA escape or containment probability equation;
- control-time or survival model form and covariates;
- crew line-production rate, travel, setup, rest and safety constraints;
- helicopter and airtanker cycle time, service time, queue discipline and
  water-source distance;
- drop coverage, water depth, retardant/foam type, canopy penetration and
  evaporation;
- fireline hold time, suppression-induced ROS/intensity reduction, breach and
  re-ignition;
- dispatch rules, prioritization, and resource competition;
- validation data, sample size, performance metric and transferability to BC;
- assumptions that cannot be transferred to the public BC/CFS scenes.

For each item, also note which P179 layer it supports:

1. statistical IA/containment layer;
2. queueing/logistics layer;
3. spatial line/drop effect layer;
4. 3D playback layer.

---

## Download and handoff

1. Sign in to UBC Library in your own browser.
2. Search the exact title or DOI.
3. Download the PDF.
4. Name it:

   ```text
   author-year-short-title.pdf
   ```

5. Put it in:

   ```text
   fresh-fire/data/martell/pdfs/
   ```

6. Tell me the filenames only. Do not send credentials or session cookies.

I will read the local PDFs and extract the model forms, parameters and
validation limits into the suppression plan.

---

## Return template

```text
Citation:
DOI / stable URL:
Access route:
Licence / author manuscript:
Relevant P179 layer:
Key equations or parameters:
Validation data:
Assumptions that may not transfer:
Local filename:
```
