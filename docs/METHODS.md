# METHODS

Every decision, formula and threshold, with the line of code that implements it and the
reason it was chosen. This file is the audit trail for the manuscript: any number in the
paper should be locatable here, then in `output/analysis_log.md`, then in the script that
produced it.

Notation: *s* indexes schools, *f* indexes TRI facilities, *l* indexes local education
agencies (school districts).

---

## 1. Exposure

**Source.** EPA Toxics Release Inventory Basic Data File, reporting year 2024, national.
The file has 77,295 rows and 21,482 distinct facilities. A row is a chemical release form.
One facility in Union County, Arkansas files 218 of them.

**Aggregation** (`01_build_exposure.py`, `aggregate_tri`). Collapse to the facility by
`TRIFD`, taking first coordinates and summing releases:

    m_f = sum over that facility's forms of (5.1 fugitive air + 5.2 stack air), in pounds

Fugitive plus stack air is the airborne fraction. Total releases (column 107) includes
water, land and underground injection, which do not reach a school through its ventilation
system, and is retained in the derived file for sensitivity but not used in the canonical
index. Negative and missing values are clipped to zero; EPA occasionally reports negative
values as data-entry corrections.

**Index.**

    E_s = sum over f of  m_f / max(d_sf, 0.1 km)^2       for all f with d_sf <= 50 km

`d_sf` is the great-circle chord distance from a `scipy.spatial.cKDTree` query on
radian coordinates, converted to kilometres by multiplying by 6371. At 50 km the chord
understates the arc by under 0.1%, well inside the precision of the source coordinates.

Three parameters and why they take these values:

*50 km search radius.* Carried forward unchanged from the earlier work, so the correction
is attributable to the aggregation and the decay rather than to a changed catchment. It is
generous for a proximity surrogate; almost all of the mass in an inverse-square index comes
from the first few kilometres.

*100 m distance floor.* Replaces a softening constant. A school is a building with a
footprint, not a point, and no school sits inside a facility's fenceline. The floor caps
the maximum single-facility contribution at `m_f / 0.01`. It binds for a negligible number
of school-facility pairs and its only job is to keep the sum finite.

*k = 500 neighbours.* Chosen so the cap never binds. The median school has 50 facilities
within 50 km; the cap is reached by no school in the file. The earlier value of 50 bound
for 77.5% of schools once the point cloud was chemical forms rather than facilities.

**Normalisation.** The raw index is divided by its own 99th percentile and multiplied by
100, then clipped at 100. This preserves the tier cutpoints used in earlier work
(0.5 / 10 / 25 / 50 / 75) and makes the resulting scale explicitly relative. Because the
top percentile is clipped to a single value, the manuscript's percentile-band analysis
ranks on the *unnormalised* index (`E_air_raw_lbs_per_km2`); ranking on the clipped version
would collapse the top band.

**Variants.** All four are written to `data/derived/school_exposure.csv` and every
stratified result in `03_analysis.py` is recomputed under each.

| Column | Point cloud | Denominator | k | Weight |
|---|---|---|---|---|
| `E_forms` | chemical forms (77,295) | d² + 1e-5 (radians²) | 50 | none |
| `E_fac` | facilities (21,482) | d² + 1e-5 (radians²) | 50 | none |
| `E_isq` | facilities | max(d, 100 m)² in km² | 500 | none |
| `EXPOSURE` / `E_air` | facilities | max(d, 100 m)² in km² | 500 | air releases, lbs |

`E_forms` exists to reproduce the published index and is not used for inference.

**What this index is not.** It has no wind, no stack height, no terrain, no chemical-
specific toxicity, no atmospheric fate. EPA's RSEI model supplies all of those and is the
correct instrument for a dose question. This index answers an allocation question: was
money distributed with any regard to where emissions are.

---

## 2. Schools

**Source.** NCES EDGE public school geocode file, 2024-25, pipe-delimited, 102,178 records.

Records without usable coordinates are dropped. The remaining file is restricted to
latitude 15 to 72 and longitude -180 to -60, which covers the fifty states, DC, Puerto Rico
and the US Virgin Islands. This excludes 109 schools in American Samoa, Guam and the
Northern Mariana Islands, none of which has a TRI facility or an ESSER district record.
Excluding them is preferable to carrying them as zero-exposure, zero-coverage rows that
would enter denominators.

Final school universe: 102,069.

---

## 3. ESSER linkage

**Source.** ESSER Annual Performance Report FY2023, `crossact` worksheet. 18,804 rows,
of which 17,026 have `isLea = True`. The remaining 1,778 are non-district subgrantees
(universities, tribal organisations, nonprofits) and are excluded.

**Outcome.** `isEsserAUsedFundsVentilation`, mapped to 1 for True, 0 for False, and missing
for anything else. `isEsserAUsedFundsCleaning` and `isEsserAUsedFundsMasks` are mapped the
same way and used for the grant-portfolio description.

Blank is missing. It is not zero. A blank means the district did not answer, which is not
the same event as answering no, and the two cannot be distinguished from this file.

**Identifier validation** (`02_build_dataset.py`, `clean_leaid`). Zero-pad `ncesNumber` to
seven digits, then keep the identifier only if its leading two digits equal the reporting
state's FIPS code. Otherwise discard it and treat the district as unlinkable.

The prefix check is necessary because several states submitted non-NCES identifiers.
New Hampshire submitted six-digit local codes; zero-padded, `502960` becomes `0502960`,
which is a real Arkansas LEAID, so New Hampshire's Benton was being merged onto Arkansas's
Benton. California submitted identifiers of two to five digits for many charter and
county-office entities, which pad to a nonexistent FIPS 00. Nevada's State Public Charter
School Authority appears under one identifier shared by several member charters.

Effect: duplicate identifiers fall from 2,416 rows to 16, and the duplication that was
inflating the analysis file from 102,178 to 102,866 school rows disappears. 869
identifiers are rejected.

**Collapse to district.** Group validated identifiers, taking the maximum of each grant
flag. Where a shared identifier carries disagreeing answers, this resolves to "funded if
any constituent record reported funded," which is the conservative direction for a paper
arguing that funding did not reach some places. One identifier required that arbitration.

**Join.** Left join district records onto schools by LEAID. The row count is asserted
unchanged; a growing row count means duplicate identifiers survived validation.

**States that cannot be linked at all.** Arizona, Connecticut, Texas and Washington have
zero validated identifiers across 2,297 districts, and answered the ventilation question
for all 2,297. Their district-level funded rates (41.4%, 41.0%, 23.4%, 52.3%) are reported;
their schools are excluded from school-level models. No name-based crosswalk is attempted.
Fuzzy matching district names to NCES would introduce an error whose direction and
magnitude could not be characterised, in exactly the states with the most schools at stake.

**Oklahoma.** Retained. All 540 agencies carry valid identifiers, all answered, all
answered False. Earlier work recoded any state under a 2% funded rate to missing; that rule
is not applied here, because it cannot distinguish a state that failed to report from a
state that reported zeros, and Oklahoma is demonstrably the latter.

**Unmatched schools inside linkable states.** Missing, never zero. School-level coverage is
78.7% nationally and is reported per state in `output/coverage_by_state.csv`, because the
coverage rate is itself a result. New York links 63.1% because NYC public schools carry
geographic community district identifiers in NCES while the city reports ESSER as a single
agency; Vermont links 3.3% because it reports through supervisory unions.

---

## 4. County covariates

**Income.** ACS 5-year 2024, table B19013, county median household income. Joined on
5-digit county FIPS from the NCES `CNTY` field. Matched for 102,045 of 102,069 schools.

**Race.** ACS 5-year 2024, table B03002. Percent people of color is

    pct_poc = (1 - B03002_003E / B03002_001E) * 100

that is, one minus the non-Hispanic White alone share. B03002 rather than B02001 because
Hispanic origin is an ethnicity in the Census framework and B02001 counts many Hispanic
respondents as White alone, which would understate the people-of-color share substantially
in the Southwest and in south Florida. Matched for 102,048 schools.

Both are county-level and therefore ecological. Every coefficient on them describes a
county, not a school, and the manuscript says so wherever they appear.

---

## 5. Analysis

**Analytic sample.** Schools in linkable states with a non-missing ventilation answer, a
computed exposure value, county income and county race. n = 80,308 across 48 states.
Listwise deletion; no imputation.

**Confidence intervals on proportions.** Wilson score, not Wald. Several state and tail
cells are small and a few sit at 0% or 100%, where the normal approximation runs outside
the unit interval.

**Models.** Logistic regression, `statsmodels`.

    A:  HAS_VENT ~ exp10
    B:  HAS_VENT ~ exp10 + inc10k + poc10
    C:  HAS_VENT ~ exp10 + inc10k + poc10 + C(STATE)

`exp10` is the normalised index divided by 10, `inc10k` is county median income divided by
10,000, `poc10` is percent people of color divided by 10. Model C is primary. It is
estimated on the 44 states with within-state variation in the outcome; states at 0% or 100%
(Oklahoma, Hawaii, Maryland, Puerto Rico) drop by perfect separation, which is reported
rather than worked around.

Confidence intervals are Wald on the log-odds scale, exponentiated. The C-statistic is the
Mann-Whitney form of the area under the ROC curve. McFadden's pseudo-R² is reported as an
index only and is never described as variance explained.

**The tail specification.** Three indicator variables for percentile bands of the
unnormalised index, with everything below the 95th percentile as reference:

    HAS_VENT ~ t95 + t99 + t999 + inc10k + poc10 + C(STATE)

where `t95` is p95 to p99, `t99` is p99 to p99.9, and `t999` is above p99.9. Quintile and
tier contrasts average over too many schools to detect a phenomenon confined to a few dozen.

A quadratic in log10 of the unnormalised index is fitted as a check on whether the pattern
is smooth curvature. It is not: the squared term is not distinguishable from zero
(*b* = 0.004, *p* = 0.37), so the manuscript describes a rising association with a tail
break, not an inverted U.

**Within-state gradient.** For each state, the funded rate in its own top exposure quintile
minus the rate in its own bottom quintile. Within-state quintiles, so a state is compared
only against itself and the comparison is unaffected by a state's position in the national
exposure distribution. States with fewer than 50 schools in either band are omitted, which
leaves 45.

**Clustering.** Not modelled. Each district makes one funding decision covering all of its
schools, so school-level observations are not independent within districts and the reported
standard errors are too small. State fixed effects absorb part of this. The direction of
the bias is known and the tail result, whose confidence interval is wide even without a
cluster correction, is the least affected by it. A district-clustered specification is the
obvious next robustness check and is not run here.

---

## 6. Funding position

`prime` worksheet of the same APR file, 52 state and territory grantees, summed across
grantees. Allocation figures are pre-filled by the Department from its G5 grant management
system as of 30 September 2023; expenditure figures are grantee-reported and may be on a
cash or accrual basis, which the Department's own data notes flag as inconsistent across
grantees but consistent within a grantee over time.

---

## 7. Known limitations

The outcome is a binary flag, not a dollar amount. A district that spent $40,000 on filters
and one that spent $12 million on air handlers are recorded identically. The district
expenditure worksheets contain dollar amounts and are not used here.

County covariates are ecological, and county income is entangled with urbanicity to the
point where its negative coefficient should not be read as a statement about wealth and
need. School-level demographics from the Common Core of Data would replace both covariates
with the population actually inside the building, and are the highest-value next addition.

The exposure index has no wind, no toxicity weighting and no dispersion. Facilities that
report to TRI are a subset of emitters, bounded by reporting thresholds and covered
industry sectors, so schools near a large non-reporting source score as unexposed.

The design is cross-sectional and every estimate is associational.

The tail result rests on 81 schools. Its Wilson interval runs from 33.0% to 54.1%. It
should be treated as a well-supported hypothesis rather than a settled quantity.
