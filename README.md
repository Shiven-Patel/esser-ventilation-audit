# ESSER ventilation funding and industrial air emissions

Did the $189.5 billion in federal pandemic relief for schools reach the schools nearest
to industrial air emissions? This repository contains the full analysis behind that
question: the exposure model, the federal-record linkage, every table and figure in the
manuscript, and the audit that found what was wrong with the previous version of this work.

**Headline result.** Recorded ESSER ventilation funding rises with modelled industrial air
exposure across almost the entire distribution, from 54.2% of schools below the median to
70.0% in the 95th to 99th percentile, and then falls to 43.2% among the 81 most exposed
schools in the country. Adjusted for state, county income and county racial composition,
those 81 schools have 0.43 times the odds of funding (95% CI 0.27 to 0.70).

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
# place the four raw files in data/raw/ (see "Data" below), then:
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
| 6 | `src/05_math_doc.py`, `src/06_manuscript_docx.js` | Computation record and the Word manuscript | `output/math_workbook.html`, `docs/*.docx` |

`src/08_build_viewer.py` builds the interactive map separately; it is not part of the
manuscript chain and needs a network connection to load Leaflet and a basemap. It is
published at
[shiven-patel.github.io/esser-ventilation-audit/viewer/](https://shiven-patel.github.io/esser-ventilation-audit/viewer/).
`src/09_docs_html.py` re-emits the manuscript and the computation record as Google
Docs-ready HTML, and `src/10_viewer_figures.py` crops the viewer screenshots that become
Figures 9 and 10. Neither changes a number.

Step 4 reads only the CSVs step 3 wrote, so a figure cannot disagree with the number it
plots. `output/analysis_log.md` is the complete computed record: if a figure in the paper
is not traceable to a line in that file, it does not belong in the paper. No figure carries
a title of its own; captions live in the manuscript and are inserted next to the image when
the Word file is built.

## Data

Four public files, none redistributed here. Sizes are approximate.

| File | Source | Vintage |
|---|---|---|
| `EDGE_GEOCODE_PUBLICSCH_2425.TXT` (22 MB) | NCES EDGE public school geocodes | 2024-25 |
| `epa_tri_national.csv` (60 MB) | EPA TRI Basic Data Files, national | RY2024 |
| `esf_hvac_spending.xlsx` (37 MB) | ED ESSER Annual Performance Report, `crossact` and `prime` worksheets | FY2023 |
| `ACSDT5Y2024.B19013-Data.csv`, `ACSDT5Y2024.B03002-Data.csv` | Census ACS 5-year, county level | 2024 |

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
docs/         manuscript, METHODS (every formula and decision), data dictionary
data/raw/     the four public inputs (not tracked)
data/derived/ intermediate and analysis files (not tracked)
output/       tables, analysis_log.md, figures
```

## Citing

If you use the exposure index or the identifier-coverage table, please cite the
manuscript in `docs/manuscript.md`. If you use the identifier finding, please note that
it applies to the FY2023 APR specifically; the Department may publish a crosswalk, which
would be the single most useful thing it could do for school-level ESSER research.

## License

Code MIT. Derived data files are built from public federal sources and carry those
sources' terms.
