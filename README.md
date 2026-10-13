# ESSER ventilation funding and industrial air emissions

Did the $189.5 billion in federal pandemic relief for schools reach the schools nearest
to industrial air emissions? This repository holds the machinery behind that question and
nothing else: the exposure model, the federal-record linkage, every table and figure, the
worked computation record, and the audit that found what was wrong with the previous
version of this work. The paper written from it is not distributed here.

**Headline result.** Exposure is measured from 2019 TRI releases, before ESSER, and
demographics from the 2017-2021 ACS. Recorded ESSER ventilation funding rises with modelled
industrial air exposure from 53.8% of schools below the median to 67.7% and 67.0% in the
90th-95th and 95th-99th percentiles, and is 58.6% in the top 1% (804 schools). With state
fixed effects, county covariates and district-clustered standard errors, the 95th-99th band
has 1.32 times the odds of schools at or below the 95th percentile (95% CI 1.07 to 1.63);
the top 1% does not differ (0.93, 0.70 to 1.24). Adding tract income and racial composition
(Model D) leaves exposure with no detectable association (aOR per 10 points 1.015, 0.980
to 1.051).

**Second result, which may matter more.** Arizona, Connecticut, Texas and Washington
answered the ventilation question for all 2,297 of their school districts and left the
NCES district identifier blank on every row. 16,002 schools cannot be linked to their own
district's public answer. Any analysis that infers reporting status from a failed join will
read this as "these states did not report," which is false, and will most often read it as
neglect in Texas, which has both the most affected schools and among the highest industrial
exposure in the country.

---

## Run it

```bash
pip install -r requirements.txt
# place the raw files in data/raw/ (see "Data" below), then:
bash run.sh
```

Roughly four minutes end to end on a laptop, most of it in the spatial join and the
state fixed-effects logit. Everything is deterministic; there is no sampling and no seed.

| Step | Script | What it does | Writes |
|---|---|---|---|
| 1 | `src/01_build_exposure.py` | Aggregates TRI to facilities, computes four exposure indices | `data/derived/school_exposure.csv` |
| 2 | `src/02_build_dataset.py` | Links ESSER, validates district identifiers, joins ACS | `data/derived/analysis_dataset.csv` |
| 3 | `src/03_analysis.py` | Every table and model in the paper | `output/*.csv`, `output/analysis_log.md` |
| 4 | `src/04_figures.py` | Charts, read only from step 3's CSVs | `output/figures/fig1-5*.png` |
| 5 | `src/07_maps.py` | Maps, drawn from the analysis dataset with no basemap | `output/figures/fig6-8*.png` |
| 6 | `src/05_math_doc.py` | The computation record: every formula, cutpoint and intermediate quantity | `output/math_workbook.html` |

`output/math_workbook.html` is where the arithmetic lives. It carries the exposure formula
with its constants, the linkage rules, the model specifications and their outputs, and the
intermediate quantities behind each reported figure, so a reader can follow a number from
the raw file to the table without running anything.

`src/08_build_viewer.py` builds the interactive map separately; it is not part of the
analysis chain and needs a network connection to load Leaflet and a basemap. It is
published at
[shiven-patel.github.io/esser-ventilation-audit/viewer/](https://shiven-patel.github.io/esser-ventilation-audit/viewer/).
Three scripts here typeset rather than compute. `src/06_manuscript_docx.js` and
`src/09_docs_html.py` lay a written draft out as Word and as HTML, and
`src/10_viewer_figures.py` crops the viewer screenshots. They read a manuscript file that
is kept outside this repository and is ignored by `.gitignore`, so they will not run from a
fresh clone. None of them changes a number.

Step 4 reads only the CSVs step 3 wrote, so a figure cannot disagree with the number it
plots. `output/analysis_log.md` is the complete computed record: a figure not traceable to
a line in that file does not belong in the analysis. No figure carries a title of its own,
because titles are set alongside the image wherever it is placed.

## Data

Public files, none redistributed here. Sizes are approximate.

| File | Source | Vintage |
|---|---|---|
| `EDGE_GEOCODE_PUBLICSCH_2425.TXT` (22 MB) | NCES EDGE public school geocodes | 2024-25 |
| `tri_2019_us.csv` (63 MB) | EPA TRI Basic Data File, US, reporting year 2019 (`--tri`, `--year 2019`) | RY2019 |
| `esf_hvac_spending.xlsx` (37 MB) | ED ESSER Annual Performance Report, `crossact` and `prime` worksheets | FY2023 |
| `acs2021_5yr_county_tract.csv` (3 MB) | Census ACS 2017-2021 5-year table-based summary file, `acsdt5y2021-b19013.dat` and `acsdt5y2021-b03002.dat`, county (050) and tract (140) rows kept | 2017-2021 |
| `tracts/cb_2021_us_tract_500k.shp` (57 MB zip) | Census 2021 cartographic boundary file, census tracts | 2021 (2020 tracts) |

`acs2021_5yr_county_tract.csv` has columns `level, GEOID, B19013_001E, B03002_001E,
B03002_003E`. The earlier 2024-vintage files (`epa_tri_national.csv`, `ACSDT5Y2024.*`) still
run through the same scripts if passed explicitly.

## What changed from the earlier version, and why

This repository supersedes an earlier pipeline (`run_audit.py`, `run_audit_exclusion.py`,
`esser_ej_audit.py`). Four defects in that pipeline changed reported results. Each is
reproduced and quantified in `docs/METHODS.md`; the short version:

**The exposure index counted paperwork, not emissions.** `epa_tri_national.csv` is
chemical-release-form level: 77,295 rows describing 21,482 facilities, with one Arkansas
facility filing 218 forms. Treating each row as a source weighted every facility by how
many distinct chemicals it reports. Combined with a 50-neighbour cap, the cap bound for
77.5% of schools, so for three quarters of American schools the index saw the 50 nearest
chemical *filings*, often from a single facility, and nothing else within 50 km.

**The distance decay was cancelled by its own softening constant.** A term of `1e-5` was
added to a squared great-circle distance in radians. A facility 20 km away has d² ≈ 9.9e-6,
smaller than the constant, so the constant dominated across the near field. Over the full
0 to 50 km range the contribution ratio was about 7:1 where a true inverse square gives
roughly 10,000:1. Fixing the aggregation alone moves 56.8% of schools into a different
exposure tier; fixing the constant as well moves 94.4%.

**Blank was read as zero at the community scale.** The district ventilation field has three
states, and unmatched schools are missing rather than unfunded. Bronx County reads as 5.5%
funded under blank-as-zero and 44.8% over the 58 of 471 schools that actually link. The
district of record for New York City public schools, the NYC Chancellor's Office (LEAID
3620580, 827,736 students), reported `True`.

**A rule intended to catch non-reporting deleted a real zero.** States with a funded rate
below 2% were recoded to missing. All 540 Oklahoma agencies carry valid identifiers, all
540 answered, and all 540 answered `False`. Oklahoma is the clearest finding in the
dataset and the old rule was the reason it disappeared.

`src/00_audit_legacy.py` reproduces the published index (Pearson r = 0.99998 against the
shipped `EXPOSURE` column across the 82,986 schools common to both files, and r = 1.00000
when the school universe is held identical, the residual difference being the percentile
that the normalisation is anchored to) and then quantifies each defect, so the diagnosis is
checkable rather than asserted.

## Repository layout

```
src/          numbered pipeline, run in order
docs/         METHODS: every formula, cutpoint and decision, with the legacy audit
data/raw/     the four public inputs (not tracked)
data/derived/ intermediate and analysis files (not tracked)
output/       tables, analysis_log.md, math_workbook.html, figures
```

Written drafts are not tracked. `.gitignore` excludes them so that a stale copy of a paper
cannot end up sitting next to code that has moved on from it.

## Citing

If you use the exposure index or the identifier-coverage table, cite the paper this
analysis supports once it is published; until then, cite this repository and the commit you
used. If you use the identifier finding, please note that it applies to the
FY2023 APR specifically; the Department may publish a crosswalk, which would be the single
most useful thing it could do for school-level ESSER research.

## License

Code MIT. Derived data files are built from public federal sources and carry those
sources' terms.
