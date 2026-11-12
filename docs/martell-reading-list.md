# Martell suppression reading list

Access note: use your own UBC Library session. Do not paste CWL credentials
into chat. Download PDFs into `data/martell/pdfs/` and I can read and mine them
locally. OpenAlex/Unpaywall were used to identify legal open copies.

## Read in full already

- **Wheatley, M.J. 2024.** *Forest Fire Suppression Effectiveness in the
  Canadian Boreal Forest.* PhD thesis, University of Toronto.
  Open: https://utoronto.scholaris.ca/bitstreams/122a90ea-f346-465a-8860-2632956ae1db/download
- **Martell, D.L. 2011.** The development and implementation of forest fire
  management decision support systems in Ontario: personal reflections.
  *MCFNS* 3(1): 18–26.
  Open: https://mcfns.com/index.php/Journal/article/download/3.3/2011.3


## UBC Open Collections result

Using the UBC Open Collections API (not CWL library login), I found and read
the full text of:

- **Murphy, P.J. 1985.** *Methods for evaluating the effects of forest fire
  management in Alberta.* PhD thesis, University of British Columbia.
  DOI: https://doi.org/10.14288/1.0075312
  UBC Open Collections: https://open.library.ubc.ca/collections/ubctheses/24/items/1.0075312

Relevant content: a historical fire-management cost/area-burned evaluation,
a fire-load index, and the `WHATIF.FIRE` potential-spread model. It is useful
for the strategic "area saved vs expenditure" layer, not for tactical crew or
airtanker simulation.

## Priority papers to retrieve through UBC Library

### Simulation and containment

- **Podur & Martell 2007.** A simulation model of the growth and suppression of
  large forest fires in Ontario. *IJWF* 16: 285–294.
  DOI: https://doi.org/10.1071/wf06107
  Why: discrete-event escape/growth/suppression model; resource scenarios.

- **Martell et al. 1984.** An evaluation of forest fire initial attack
  resources. *Interfaces* 14(5): 20–32.
  DOI: https://doi.org/10.1287/inte.14.5.20
  Why: IA simulation and resource acquisition.

- **Bookbinder & Martell 1979.** Time-dependent queueing approach to helicopter
  allocation for forest fire initial attack. *INFOR*.
  DOI: https://doi.org/10.1080/03155986.1979.11731717
  Why: queueing model for helicopter deployment.

- **MacLellan & Martell 1996.** Basing airtankers for forest fire control in
  Ontario. *Operations Research* 44(5): 677–686.
  DOI: https://doi.org/10.1287/opre.44.5.677
  Why: airtanker home-basing optimization.

### Initial attack, control time and productivity

- **Hirsch & Martell 1996.** A review of initial attack fire crew productivity
  and effectiveness. *IJWF* 6: 199–215.
  DOI: https://doi.org/10.1071/wf9960199
  Why: crew productivity, effectiveness thresholds and transferability.

- **Hirsch, Corey & Martell 1998.** Using expert judgment to model initial
  attack fire crew effectiveness. *Forest Science* 44(4): 539–549.
  DOI: https://doi.org/10.1093/forestscience/44.4.539
  Why: elicited crew effectiveness and line production.

- **Wheatley et al. 2015.** The use of survival analysis methods to model the
  control time of forest fires in Ontario. *IJWF*.
  DOI: https://doi.org/10.1071/wf14158
  Why: control-time distributions and covariates.

- **Wheatley et al. 2018.** Factors that affect the timing of the dispatch of
  initial attack resources. *IJWF*.
  DOI: https://doi.org/10.1071/wf18058
  Why: dispatch delay and daily fire load.

### Airtankers and aerial suppression

- **Wheatley et al. 2022a.** Modelling decisions concerning the dispatch of
  airtankers for initial attack in Ontario. *CJFR*.
  DOI: https://doi.org/10.1139/cjfr-2022-0225
  Why: hurdle dispatch models; FWI, fuel volatility, ROS, size, cause.

- **Wheatley et al. 2022b.** Modelling initial attack success on forest fires
  suppressed by air attack in Ontario. *IJWF*.
  DOI: https://doi.org/10.1071/wf22006
  Why: IA success models; airtanker effort; ROC.

- **Wheatley et al. 2019.** The use of aircraft tracking GPS data to develop
  models of the use of airtankers. *INFOR*.
  DOI: https://doi.org/10.1080/03155986.2019.1706398
  Why: spatial queueing, service times, turn-around.

- **2022.** Predicting daily initial attack aircraft targets in British
  Columbia. *IJWF*.
  DOI: https://doi.org/10.1071/wf21090
  Why: BC-specific aircraft IA demand.

- **2025.** Assessing wildland fire suppression effectiveness with infrared
  imaging on experimental fires. *IJWF*.
  DOI: https://doi.org/10.1071/wf24161
  Why: water delivery, ROS/intensity reduction and hold time.

### Reviews and DSS lessons

- **Martell 1982.** A review of operational research studies in forest fire
  management. *CJFR* 12: 119–140.
  DOI: https://doi.org/10.1139/x82-020

- **Martell 2015.** A review of recent forest and wildland fire management
  decision support systems research. *Current Forestry Reports* 1: 128–137.
  DOI: https://doi.org/10.1007/s40725-015-0011-y

## What I will extract from each PDF

- model state variables and decision variables;
- suppression-effect equations or statistical forms;
- resource productivity and service-time distributions;
- dispatch/queueing logic;
- validation data and performance metrics;
- assumptions that transfer to BC;
- assumptions that do not transfer.

## Download workflow

1. Sign in to UBC Library in your own browser.
2. Search the DOI or title.
3. Download the PDF.
4. Put it in `fresh-fire/data/martell/pdfs/`.
5. Tell me the filenames; I will read and summarize them locally.

Do not send your CWL password or session cookies.
