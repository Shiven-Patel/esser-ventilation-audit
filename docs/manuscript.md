# ESSER Ventilation Funding and Industrial Air Emissions at US Public Schools

**Target journal:** *Environmental Justice* (Sage), Research Article, 4,000-word limit, Chicago style.

---

## Structured abstract

**Background.** Between 2020 and 2021 Congress appropriated $189.5 billion through the Elementary and Secondary School Emergency Relief (ESSER) funds. The associated federal reporting asked each district whether it had used ESSER money for ventilation. Whether that spending was associated with proximity to industrial air emissions has not been examined.

**Methods.** We linked the geocoded universe of US public schools (NCES EDGE, 2024-25, n = 102,069) to district-level ESSER use-of-funds reporting (FY2023 Annual Performance Report, 17,026 local education agencies), to an industrial air-emissions exposure index built from the 2024 EPA Toxics Release Inventory, and to county income and racial composition from the 2024 ACS five-year estimates. The index weights each of 21,482 facilities by its reported fugitive and stack air releases and by inverse-square distance within 50 km. We estimated logistic models with state fixed effects.

**Results.** In the analytic sample (80,308 schools across 46 states, the District of Columbia and Puerto Rico), 57.7% of schools were in districts that recorded ventilation spending. The recorded rate rose across the exposure distribution, from 54.2% below the median to 70.0% in the 95th to 99th percentile, and was lower in the highest band: 43.2% among the 81 schools above the 99.9th percentile. Adjusted for county income, county racial composition and state, those schools had 0.43 times the odds of the reference group (95% CI 0.27 to 0.70).

**Conclusions.** Recorded ventilation spending was positively associated with modelled industrial exposure over most of its range, and negatively associated at the extreme. Four states answered the ventilation question for every district while leaving the federal district identifier blank, which leaves 16,002 schools unlinkable and has been read as non-reporting.

---

## Introduction

School buildings modify children's exposure to outdoor air pollution. The infiltration factor and penetration factor that govern how much of an ambient particle concentration reaches indoor air are properties of the building envelope and the ventilation system, not of the ambient concentration alone.[^1] Field measurement bears this out at schools specifically: filtration upgrades at near-roadway schools in Las Vegas raised the indoor reduction of black carbon from a range of 31 to 66 percent up to 74 to 97 percent, while gas-phase toxics were not reduced because indoor sources dominated them.[^2] A block-randomised crossover trial across 186 classrooms in 17 Los Angeles elementary schools found that portable HEPA units added on top of MERV-13 filtration lowered school-year average classroom PM2.5 by 39.9 percent and cut outdoor infiltration by between 13.8 and 82.4 percent depending on the school.[^3] Ventilation is an exposure control, in other words, and one many US classrooms lack: a review of the measurement literature found average ventilation rates spanning roughly 1 to 8.8 L/s per person against a requirement near 7, with peak CO2 above 1,000 ppm in every study reviewed.[^4]

Schools also sit close to industrial sources, and not at random. A national analysis published in 2026 found that roughly half of US pre-K through 12 schools are near an environmental hazard site.[^5] Modelled air-neurotoxicant burdens at US public schools are higher where more students of color are enrolled,[^6] and the same pattern holds for ambient NO2 measured at school sites, independent of income.[^7] Work in Los Angeles established two decades ago that school-site air-toxics risk is racially patterned and associated with lower academic performance net of demographics,[^8] and Michigan schools in higher industrial-pollution locations show higher absenteeism and lower test scores.[^9]

Federal support for school ventilation was, until recently, close to absent. The Government Accountability Office estimated in 2020 that 41 percent of districts needed to update or replace heating, ventilation and air conditioning systems in at least half of their schools, roughly 36,000 buildings.[^10] A practitioner census of facilities spending puts national underinvestment in PK-12 facilities near $85 billion a year, concentrated in districts serving Hispanic, Black and Native American students.[^11] ESSER changed that position temporarily. Congress appropriated $13.2 billion through the CARES Act, $54.3 billion through the Coronavirus Response and Relief Supplemental Appropriations Act, and $121.97 billion through the American Rescue Plan.[^12] Because ESSER rode the Title I formula, its adequacy relative to pandemic costs varied by district poverty rather than by facility need,[^13] and the available evidence indicates most of it went to staffing rather than capital.[^14]

What is missing is an account of where the ventilation share went. To our knowledge there is no peer-reviewed evaluation of ESSER ventilation spending, and none of disparities in the condition of school ventilation systems by race or income. The exposure disparity at schools is documented and the funding is documented; the join between them is not. This paper makes that join, asking whether recorded ventilation spending was associated with the industrial emissions near a school, and in what direction.

## Data and methods

### Sources

Four public files. School locations and identifiers come from the NCES EDGE geocode file for 2024-25, which places 102,178 public schools. We retained the 102,069 falling inside the geographic footprint that EPA's Toxics Release Inventory covers, excluding 109 schools in American Samoa, Guam and the Northern Mariana Islands, where no TRI facility reports and no ESSER district record exists. Funding status comes from the `crossact` worksheet of the FY2023 ESSER Annual Performance Report, which carries 17,026 local education agency records. County median household income comes from ACS table B19013 and county racial composition from B03002, both 2024 five-year estimates. We use B03002 rather than B02001 because Hispanic origin is an ethnicity in the Census framework and B02001 records many Hispanic residents as White alone, which would understate the people-of-color share in several of the regions this analysis covers.

### Exposure

Exposure comes from the 2024 TRI Basic Data File. The unit of that file is the chemical release form rather than the facility: 77,295 rows describe 21,482 facilities, and one hazardous-waste treatment facility in Union County, Arkansas accounts for 218 of them. A distance-weighted index computed over the raw rows would weight each facility by the number of chemicals it reports, which reflects its product mix and its reporting obligations rather than its emissions. We therefore aggregated to the facility before computing anything, and summed reported fugitive and stack air releases in pounds.

The exposure index for school *s* is

$$E_s = \sum_{f} \frac{m_f}{\max(d_{sf},\ 0.1\ \text{km})^2}$$

summed over facilities *f* within 50 km, where *m_f* is 2024 air releases in pounds and *d_sf* is the great-circle distance from school *s* to facility *f*. The 100-metre floor keeps the sum finite for schools adjacent to a reporting facility. We retained the 500 nearest facilities, a cap that does not bind, since the median school has 50 TRI facilities within 50 km. We then scaled the index so that its 99th percentile equals 100. That normalisation is relative by construction, so a school in the top band is in the top percentiles of US schools rather than above any absolute health threshold, and we report percentile position rather than index value wherever the distinction matters. Proximity surrogates of this kind carry known geocoding and buffer-choice error, which is a further reason to report rank position rather than treat the index as a concentration.[^15]

The index does not model wind, stack height, terrain, chemical-specific toxicity, or atmospheric fate, all of which EPA's Risk-Screening Environmental Indicators model does and which would be required for a study of delivered dose.[^16] For the allocation question addressed here, a mass-weighted proximity measure is adequate and its limitations are identifiable.

Specification matters more than is usual for this kind of index, so we computed four variants and report every stratified result under all of them (Figure 2). The variants differ in whether the point cloud is chemical forms or facilities, whether the denominator carries a softening constant or a physical distance floor, and whether facilities are weighted by released mass.

### Linkage

Districts report an `ncesNumber` field. We zero-padded it to seven digits and retained an identifier only where its leading two digits matched the reporting state's FIPS code, treating the district as unlinkable otherwise. The check is needed because several states submitted identifiers that are not NCES district codes. New Hampshire, for example, submitted six-digit local codes, one of which pads to a valid Arkansas district identifier. Validation reduced duplicate identifiers from 2,416 rows to 16 and rejected 869 identifiers.

Ventilation status was coded 1 for True, 0 for False, and missing otherwise. A blank records that the district did not answer, which the file does not distinguish from a district that answered and reported no spending. Treating blanks as zeros is the coding decision with the largest consequences in this analysis, and we return to it below.

### Analysis

The analytic sample is schools in linkable states with a non-missing ventilation answer, a computed exposure value, and county income and racial composition: 80,308 schools. Confidence intervals on proportions are Wilson score intervals, since several state and tail cells sit near 0% or 100%. We fitted three nested logistic models: exposure alone; exposure with county income and county percent people of color; and the same with state fixed effects, which is the primary specification and is estimated on the 44 states with within-state variation. County-level covariates are a compromise the data force on us, and one with a known direction: areal aggregates used as proxies for the exposed population understate disparities relative to distance-based methods.[^17] To examine the top of the exposure distribution, where quintile contrasts average over too many schools to be informative, we coded three percentile-band indicators against a reference of everything below the 95th percentile. Full model specifications, formulas and outputs are in the supplementary computation record.

## Results

### Reporting coverage

Arizona, Connecticut, Texas and Washington answered the ventilation question for every one of their local education agencies. Arizona reported for 601, Connecticut for 200, Texas for 1,186 and Washington for 310, with district-level recorded rates of 41.4%, 41.0%, 23.4% and 52.3%. All four left the `ncesNumber` field blank on every row. The consequence is that 16,002 schools in those states cannot be linked to their own district's answer, even though the answer was submitted and is public; Figure 4 gives identifier coverage for the 24 lowest states, and Figure 6 shows the same gap geographically, with the four states appearing as neutral blocks.

An analysis that joins on the identifier and infers reporting status from the join result will record these states as non-reporting. Harris County, Texas, which contains 1,201 schools and sits in the top decile of our exposure index, has been described in earlier work on these data as a case where a targeting deficit could not be measured. Houston Independent School District recorded ventilation spending, as did Alief ISD; Aldine, Spring Branch and Cypress-Fairbanks did not. The Texas record is complete at the district level and cannot be assigned to individual schools.

The same mechanism operates inside states that do supply identifiers. New York's public schools carry geographic community district identifiers in NCES, while New York City reports ESSER as one agency, the NYC Chancellor's Office, enrolling 827,736 students under an identifier that does not appear in the NCES geocode file. Of 471 schools in Bronx County, 58 link to a district record, and the Chancellor's Office recorded ventilation spending. Vermont links 10 of 305 schools, because its submissions come from supervisory unions. Indiana links 82% and New Mexico 87%.

Coding unmatched schools as unfunded moves the national rate from 57.7% to 53.9%. At community scale the same choice matters considerably more. Bronx County reads as 5.5% under blank-as-zero and 44.8% over the schools that link, and the lower figure has circulated as evidence of neglect in a borough whose district recorded the spending. Figure 8 shows the three counties where this distinction is clearest.

Oklahoma is the opposite case. All 540 of its agencies carry valid identifiers, all 540 answered, and all 540 answered False, including Oklahoma City Public Schools and every district and charter in Tulsa County. Earlier work applied a rule recoding any state with a recorded rate below 2% to missing, on the reasoning that a true zero across hundreds of districts is implausible; that rule removes the one state that appears to have recorded no ventilation spending at all, and removing true zeros biases the national rate upward. We retained Oklahoma. No fixed-effects specification can use it, since a state without within-state variation drops by construction.

### Exposure and recorded funding

The analytic sample records ventilation spending for 57.7% of schools (Wilson 95% CI 57.4 to 58.1). Cleaning was recorded more often, at 64.8%, and personal protective equipment less often, at 27.8%.

The recorded rate rises across most of the exposure distribution (Figure 1). Below the median it is 54.2%; between the 50th and 80th percentiles, 59.0%; from the 80th to the 90th, 63.1%; from the 90th to the 95th, 64.9%; and from the 95th to the 99th, 70.0%. The rate is lower in the two highest bands: 59.2% between the 99th and 99.9th percentiles, and 43.2% among the 81 schools above the 99.9th percentile (Wilson 95% CI 33.0 to 54.1). Those 81 schools are distributed across 26 states, with the largest counts in Florida, Illinois, Louisiana and Oklahoma, so the pattern is not one state's reporting practice; their median index value is 44 times that of schools in the 95th to 99th band. Figure 7 shows where they are.

The pattern persists after adjustment. In a logistic model with state fixed effects, county median household income and county percent people of color, taking everything below the 95th percentile as reference, schools in the 95th to 99th band had 1.44 times the odds of recorded funding (95% CI 1.32 to 1.57, *p* = 1.5 × 10^-16^); schools in the 99th to 99.9th band were not distinguishable from the reference (aOR 1.04, 95% CI 0.88 to 1.23); and schools above the 99.9th percentile had 0.43 times the odds (95% CI 0.27 to 0.70, *p* = 5.8 × 10^-4^). That last estimate is fitted on 76 of the 81 schools, since five are in states that separate perfectly and drop from any fixed-effects model.

We would not describe this as an inverted U. A quadratic term in log exposure is not distinguishable from zero (*b* = 0.004, *p* = 0.37) once state and county covariates are included, so the data are consistent with a rising association together with a departure confined to the extreme tail, rather than with smooth curvature across the range.

The gradient's presence is not sensitive to the exposure specification, but its shape is. All four variants show recorded funding rising across quintiles. Under the two corrected specifications the top of the distribution turns down; under the published chemical-form index it does not. The variants also disagree sharply about how many schools are highly exposed: the count in the highest fixed tier ranges from 28,200 under the published index to 1,052 under the mass-weighted one (Figure 2). Any absolute statement about how many US schools sit in a high-exposure band is therefore a statement about the index rather than about the country.

### Community composition

The steepest gradient in these data is county racial composition, and it runs upward (Figure 5). Schools in counties in the lowest quintile of people-of-color share recorded ventilation spending at 47.3%; in the highest quintile, 79.6%. County income runs in the opposite direction and less steeply, from 61.0% in the lowest income quintile to 51.3% in the highest.

In the fixed-effects model, each additional ten percentage points of county people-of-color share is associated with 1.26 times the odds of recorded funding (95% CI 1.25 to 1.28); each additional $10,000 of county median household income with 0.86 times the odds (95% CI 0.86 to 0.87); and each ten points of exposure with 1.04 (95% CI 1.03 to 1.06). Adding county race attenuates the exposure coefficient from 1.083 to 1.043, so some of the exposure association operates through racial composition, although under the mass-weighted index the two variables are close to independent at the school level (*r* = 0.046, against *r* = 0.32 under the chemical-form-count index used in earlier work).

Estimated on the same 75,961 schools, state indicators alone give a C-statistic of 0.70, the three covariates alone 0.66, and all four together 0.73. Which state a school is in therefore predicts whether its district recorded ventilation spending somewhat better than the school's own exposure and community characteristics do, which is worth stating plainly because state effects absorb reporting and application practice alongside need. The result is about the record as much as the allocation.

Both county covariates are ecological. County income in particular is confounded with urbanicity, and we would not read its negative coefficient as a statement about wealth and need.

### Variation within states

National averages conceal state patterns running in both directions (Figure 3). Comparing each state's own top exposure quintile against its own bottom quintile, 11 of the 45 jurisdictions with enough schools in both bands show a negative gap. New Mexico is the widest at 35.4 points (20.5% at high exposure against 55.9% at low), followed by South Carolina at 29.4, Arkansas at 20.3, West Virginia at 19.4 and Alabama at 19.1. Thirty run in the other direction, several steeply: Georgia at plus 34.3, Nebraska at plus 33.6, New Hampshire at plus 33.3. Four have a gap of exactly zero for want of within-state variation: Hawaii, Maryland and Puerto Rico recorded spending for every school, Oklahoma for none.

Two community-level results survive the coverage problem. Bernalillo County, New Mexico links 191 of 208 schools, and records 2.1% funded; the blank-as-zero figure is 1.9%, so the two codings agree. Albuquerque Public Schools, which enrolls most of those schools, recorded no ventilation spending in its own federal filing. Oklahoma County is the same case at a smaller scale, with 216 of 220 schools linked and none funded. One result runs the other way: Gary Community School Corporation, the largest majority-Black district in northwest Indiana, recorded ventilation spending and submitted without an identifier, so its schools are absent from the Lake County figure entirely.

## The funding position

The three ESSER funds carried obligation deadlines of September 30, 2022, 2023 and 2024, set by the Tydings carryover provision at 20 U.S.C. § 1225(b), with liquidation due 120 days later.[^18] As of the FY2023 Annual Performance Report, states reported $72.5 billion of the $189.5 billion still unspent, including $64.7 billion of ARP ESSER, or 53.1% of that fund, twelve months before its obligation deadline. The Department of Education granted late-liquidation extensions of up to fourteen additional months; by February 2025 it had approved 164 requests covering 47 states, the District of Columbia, Puerto Rico and the outlying areas, authorising $4.8 billion, of which $3.3 billion was ARP ESSER.[^19] On March 28, 2025, the Secretary revoked those extensions effective the same day.[^20] Sixteen states and the District of Columbia sued; the Southern District of New York enjoined the revocation on May 6 and again on June 3, 2025, and the Department restored access in June.[^21]

No comparable program has followed. The Inflation Reduction Act's school indoor air quality provision appropriated $50 million once, of which EPA competed $34 million to five intermediary grantees in August 2024, roughly 0.7% of the late-liquidation authority alone.[^22] There is no standing federal K-12 facilities program, as there was not before 2020.[^23]

This bears on the results in one specific way. Ventilation is capital work with procurement and construction timelines measured in quarters, unlike the tutoring and staff retention that absorbed most ESSER spending. A district weighing a mechanical upgrade against an obligation deadline it might not meet, with no successor program to complete the work, faced a different decision from one purchasing supplies. That reasoning predicts under-investment in ventilation generally. It does not predict under-investment concentrated among the most exposed schools, and we do not offer it as an explanation for the tail result. It does mean that whatever produced the tail will not be addressed by a subsequent allocation.

## Discussion

The claim we would defend is narrow. Recorded ESSER ventilation spending was positively associated with modelled industrial air emissions across most of the exposure distribution and negatively associated at the extreme. The second half of that claim rests on 81 schools, with a confidence interval on their recorded rate running from 33% to 54%, and a competent reader should treat it as a well-supported hypothesis rather than a settled quantity.

Three features make it worth reporting. The sign is opposite to the trend it terminates, and the estimate survives state fixed effects and county covariates. A mechanism is also available: schools above the 99.9th percentile are, by construction, adjacent to the largest single emitters in the country, which is the configuration the literature on fenceline communities describes.[^24] Communities economically dependent on one dominant industry develop what Freudenburg called an addictive economy, in which opposition to the facility's harms is structurally suppressed,[^25] and a dominant employer can cultivate a local economic identity that outlasts the employment itself.[^26] Facility organisational characteristics also combine with community demographics in ways a simple demographic gradient does not capture.[^27] This analysis cannot test any of that, having no measure of local political economy, and constructing one is the obvious next step. A reviewer may raise the direction of causation, on which the standing evidence favours disparate siting over subsequent demographic change.[^28]

The linkage finding is separable from the exposure finding and may be more consequential. Four states with 16,002 schools cannot enter a school-level analysis of these data, and the federal record does not indicate this. A researcher who joins on the NCES identifier and infers reporting status from the join will reproduce the error, and will most often reproduce it as apparent neglect in Texas, which has both the largest number of affected schools and high industrial exposure. The bias runs toward a conclusion the data do not support.

The strongest objection to that framing comes from GAO's own handling of the same file. Its 2024 review matched districts first on the NCES identifier, then on the Unique Entity ID, then on the DUNS number, then by hand, excluding 13 districts and certifying the data sufficiently reliable.[^29] GAO would say the problem is solvable with effort rather than structural. Two considerations qualify that. GAO worked at the district level, where UEI and DUNS are available; the school-level join has no such fallback, since neither field appears in any NCES school file. And GAO does not report how many records lacked a usable NCES identifier or break the shortfall out by state, so a reader has no way to learn that four states are absent from any school-level analysis.

The racial composition result deserves more scrutiny than a first reading suggests. Districts in the most racially diverse counties recorded ventilation spending at 79.6% against 47.3% in the least diverse, a gradient considerably steeper than exposure produces, which a straightforward reading would call equitable targeting. We are not confident in that reading, for three reasons that compound. County racial composition is a weak proxy for school racial composition, and areal proxies of this kind are known to understate disparity rather than invent it.[^30] The outcome is a binary flag rather than a dollar amount, so a district that spent $40,000 on filter upgrades and one that spent $12 million on air handlers are recorded identically. And recorded spending is not delivered ventilation: a field study of 104 recently retrofitted California classrooms found average ventilation of 5.2 L/s per person, still below standard, with equipment, control or filter faults in 51 percent of them.[^31] A funding flag sits three steps away from an exposure outcome.

That distance is worth closing, because the intervention is inexpensive relative to what it buys. Enhanced school filtration has been estimated to cut the PM2.5-attributable asthma burden by 13 percent annually at roughly $63 per classroom per year, cheaper per child than the residential equivalent.[^32] Classroom ventilation is associated with lower illness absence, with one California study estimating that meeting the state standard would cut absence 3.4 percent for about $4 million in annual cost against $33 million in attendance-linked funding,[^33] and capital investment in HVAC specifically, unlike investment in athletic facilities, raises test scores.[^34] Whether ESSER money reached the buildings where those returns are largest is the question this paper opens rather than settles.

Two additions would resolve much of what is unsettled here. School-level demographics from the Common Core of Data would replace the ecological county covariates with the population inside the building. District-level dollar amounts, which exist in the ESSER expenditure worksheets, would replace the binary flag, and would let the analysis address the possibility that federal dollars displaced local ones rather than adding to them, which is the standard finding for targeted education aid and has been reported for ESSER itself.[^35] Neither requires new data collection. Both would benefit from the Department publishing an identifier crosswalk for the four states currently outside any school-level analysis, which is a small administrative step with a large effect on what the federal record can be asked.

---

## Figures

**Figure 1.** Recorded ventilation funding by percentile band of the exposure index. Bars show Wilson 95% confidence intervals; the sample size in each band is printed below its point.

**Figure 2.** Number of schools falling in each exposure tier under four specifications of the index, at identical cutpoints on the normalised scale.

**Figure 3.** Difference in recorded funding between each state's own top and bottom exposure quintile, in percentage points. States with fewer than 50 schools in either band are omitted.

**Figure 4.** Share of schools linkable to their district's ESSER record, for the 24 states with the lowest coverage. Every state shown answered the ventilation question for every district; the annotation gives the district-level rate.

**Figure 5.** Recorded funding by quintile of county people-of-color share, with Wilson 95% confidence intervals. The mean share for each quintile is printed on the axis.

**Figure 6.** Recorded ESSER ventilation spending, by school. Albers equal-area projection; each point is one school and no basemap is drawn, so the outline is the school distribution itself. Arizona, Connecticut, Texas and Washington carry no linkable district record; Oklahoma recorded none.

**Figure 7.** Schools above the 99.9th percentile of the exposure index, shown against the TRI facilities that place them there. All schools and all reporting facilities appear in grey behind.

**Figure 8.** Bernalillo, Oklahoma and Bronx counties, coloured as in Figure 6. Each panel is a square window centred on its own county and carries its own scale bar, so areas should not be compared across panels.

---

## Notes

[^1]: Chen, C., and B. Zhao. "Review of Relationship between Indoor and Outdoor Particles: I/O Ratio, Infiltration Factor and Penetration Factor." *Atmospheric Environment* 45, no. 2 (2011): 275-88. https://doi.org/10.1016/j.atmosenv.2010.09.048.

[^2]: McCarthy, M. C., J. F. Ludwig, S. G. Brown, D. L. Vaughn, and P. T. Roberts. "Filtration Effectiveness of HVAC Systems at Near-Roadway Schools." *Indoor Air* 23, no. 3 (2013): 196-207. https://doi.org/10.1111/ina.12015.

[^3]: Simona, S. C., S. M. Bartell, and V. M. Vieira. "Classroom Air Quality in a Randomized Crossover Trial with Portable HEPA Air Cleaners." *Journal of Exposure Science and Environmental Epidemiology* 35, no. 4 (2025): 644-48. https://doi.org/10.1038/s41370-025-00743-9.

[^4]: Fisk, W. J. "The Ventilation Problem in Schools: Literature Review." *Indoor Air* 27, no. 6 (2017): 1039-51. https://doi.org/10.1111/ina.12403.

[^5]: Malik, S., M. A. Kraft, and G. T. Falken. "US Schools' Proximity to Environmental Hazard Sites: A National Analysis." *Proceedings of the National Academy of Sciences* 123, no. 33 (2026): e2609567123. https://doi.org/10.1073/pnas.2609567123.

[^6]: Grineski, S. E., and T. W. Collins. "Geographic and Social Disparities in Exposure to Air Neurotoxicants at U.S. Public Schools." *Environmental Research* 161 (2018): 580-87. https://doi.org/10.1016/j.envres.2017.11.047.

[^7]: Bechle, M. J., D. B. Millet, and J. D. Marshall. "Ambient NO2 Air Pollution and Public Schools in the United States: Relationships with Urbanicity, Race-Ethnicity, and Income." *Environmental Science and Technology Letters* 10, no. 10 (2023): 844-50. https://doi.org/10.1021/acs.estlett.3c00507.

[^8]: Pastor, M., Jr., J. L. Sadd, and R. Morello-Frosch. "Reading, Writing, and Toxics: Children's Health, Academic Performance, and Environmental Justice in Los Angeles." *Environment and Planning C: Government and Policy* 22, no. 2 (2004): 271-90. https://doi.org/10.1068/c009r.

[^9]: Mohai, P., B.-S. Kweon, S. Lee, and K. Ard. "Air Pollution around Schools Is Linked to Poorer Student Health and Academic Performance." *Health Affairs* 30, no. 5 (2011): 852-62. https://doi.org/10.1377/hlthaff.2011.0077.

[^10]: U.S. Government Accountability Office. *K-12 Education: School Districts Frequently Identified Multiple Building Systems Needing Updates or Replacement*. GAO-20-494. Washington, DC, June 2020. https://www.gao.gov/products/gao-20-494.

[^11]: Filardo, M. *2021 State of Our Schools: America's PK-12 Public School Facilities*. Washington, DC: 21st Century School Fund, International WELL Building Institute, and National Council on School Facilities, 2021. Practitioner report, not peer reviewed.

[^12]: U.S. Department of Education, Office of Elementary and Secondary Education. *Elementary and Secondary School Emergency Relief Fund Annual Performance Report, Fiscal Year 2023*. Allocation and expenditure figures computed by the authors from the `prime` worksheet, 52 state and territory grantees, position as of September 30, 2023.

[^13]: Gordon, N., and S. Reber. "Were Federal COVID Relief Funds for Schools Enough?" *Tax Policy and the Economy* 36 (2022): 123-57. https://doi.org/10.1086/718952.

[^14]: Goldhaber, D., G. Falken, and R. Theobald. *ESSER Funding and School System Jobs: Evidence from Job Posting Data*. CALDER Working Paper 297-0225-2, February 2025. Working paper, not peer reviewed.

[^15]: Zandbergen, P. A., and J. W. Green. "Error and Bias in Determining Exposure Potential of Children at School Locations Using Proximity-Based GIS Techniques." *Environmental Health Perspectives* 115, no. 9 (2007): 1363-70. https://doi.org/10.1289/ehp.9668.

[^16]: U.S. Environmental Protection Agency. *EPA's Risk-Screening Environmental Indicators (RSEI) Methodology*, version 2.3.11. March 2023.

[^17]: Mohai, P., and R. Saha. "Reassessing Racial and Socioeconomic Disparities in Environmental Justice Research." *Demography* 43, no. 2 (2006): 383-99. https://doi.org/10.1353/dem.2006.0017.

[^18]: 20 U.S.C. § 1225(b); U.S. Department of Education. *Grantee Communication: ARP ESSER and ARP EANS Obligation Deadlines and Extensions*, June 12, 2024.

[^19]: Congressional Research Service. *Late Liquidation Period for Elementary and Secondary Education Funds Provided during COVID-19 Pandemic*. IF12978, updated July 3, 2025.

[^20]: Letter from Secretary Linda McMahon to Chief State School Officers, March 28, 2025.

[^21]: *State of New York v. U.S. Department of Education*, No. 1:25-cv-02990 (S.D.N.Y.), preliminary injunction orders of May 6 and June 3, 2025; U.S. Department of Education, Dear Colleague Letter, June 26, 2025.

[^22]: Inflation Reduction Act of 2022, Pub. L. No. 117-169, § 60106; U.S. Environmental Protection Agency, press release, August 22, 2024.

[^23]: Congressional Research Service. *School Construction and Renovation: A Review of Federal Programs and Legislation*. R41142.

[^24]: Johnston, J., and L. Cushing. "Chemical Exposures, Health, and Environmental Justice in Communities Living on the Fenceline of Industry." *Current Environmental Health Reports* 7, no. 1 (2020): 48-57. https://doi.org/10.1007/s40572-020-00263-8.

[^25]: Freudenburg, W. R. "Addictive Economies: Extractive Industries and Vulnerable Localities in a Changing World Economy." *Rural Sociology* 57, no. 3 (1992): 305-32. https://doi.org/10.1111/j.1549-0831.1992.tb00467.x.

[^26]: Bell, S. E., and R. York. "Community Economic Identity: The Coal Industry and Ideology Construction in West Virginia." *Rural Sociology* 75, no. 1 (2010): 111-43. https://doi.org/10.1111/j.1549-0831.2009.00004.x.

[^27]: Grant, D., M. N. Trautner, L. Downey, and L. Thiebaud. "Bringing the Polluters Back In: Environmental Inequality and the Organization of Chemical Production." *American Sociological Review* 75, no. 4 (2010): 479-504. https://doi.org/10.1177/0003122410374822.

[^28]: Pastor, M., J. Sadd, and J. Hipp. "Which Came First? Toxic Facilities, Minority Move-In, and Environmental Justice." *Journal of Urban Affairs* 23, no. 1 (2001): 1-21. https://doi.org/10.1111/0735-2166.00072.

[^29]: U.S. Government Accountability Office. *K-12 Education: School Districts Reported Spending Initial COVID Relief Funds on Meeting Students' Needs and Continuing School Operations*. GAO-24-106913. Washington, DC, September 23, 2024. https://www.gao.gov/products/gao-24-106913.

[^30]: Chakraborty, J., J. A. Maantay, and J. D. Brender. "Disproportionate Proximity to Environmental Health Hazards: Methods, Models, and Measurement." *American Journal of Public Health* 101, no. S1 (2011): S27-S36. https://doi.org/10.2105/AJPH.2010.300109. See also Baden, B. M., D. S. Noonan, and R. M. R. Turaga. "Scales of Justice: Is There a Geographic Bias in Environmental Equity Analysis?" *Journal of Environmental Planning and Management* 50, no. 2 (2007): 163-85. https://doi.org/10.1080/09640560601156433.

[^31]: Chan, W. R., X. Li, B. C. Singer, T. Pistochini, D. Vernon, S. Outcault, A. Sanguinetti, and M. Modera. "Ventilation Rates in California Classrooms: Why Many Recent HVAC Retrofits Are Not Delivering Sufficient Ventilation." *Building and Environment* 167 (2020): 106426. https://doi.org/10.1016/j.buildenv.2019.106426.

[^32]: Martenies, S. E., and S. A. Batterman. "Effectiveness of Using Enhanced Filters in Schools and Homes to Reduce Indoor Exposures to PM2.5 from Outdoor Sources and Subsequent Health Benefits for Children with Asthma." *Environmental Science and Technology* 52, no. 18 (2018): 10767-76. https://doi.org/10.1021/acs.est.8b02053.

[^33]: Mendell, M. J., E. A. Eliseeva, M. M. Davies, M. Spears, A. Lobscheid, W. J. Fisk, and M. G. Apte. "Association of Classroom Ventilation with Reduced Illness Absence: A Prospective Study in California Elementary Schools." *Indoor Air* 23, no. 6 (2013): 515-28. https://doi.org/10.1111/ina.12042.

[^34]: Biasi, B., J. Lafortune, and D. Schönholzer. "What Works and for Whom? Effectiveness and Efficiency of School Capital Investments across the U.S." *Quarterly Journal of Economics* 140, no. 3 (2025): 2329-79. https://doi.org/10.1093/qje/qjaf013.

[^35]: Gordon, N. "Do Federal Grants Boost School Spending? Evidence from Title I." *Journal of Public Economics* 88, no. 9-10 (2004): 1771-92. https://doi.org/10.1016/j.jpubeco.2003.09.002; Clemens, J., P. G. Hoxie, and S. Veuger. *Intergovernmental Grants to School Districts and Educational Outcomes during the COVID-19 Pandemic*. NBER Working Paper 35447, July 2026. Working paper, not peer reviewed.

---

## Data and code availability

All analysis is reproducible from public files. Scripts, the derived analysis dataset, every output table and the figures are at [REPOSITORY URL]. The pipeline runs in ordered steps and regenerates every number in this manuscript from the raw NCES, EPA, ED and Census files.

## Declaration of AI use

Anthropic's Claude was used as a coding and analysis aid: to build and debug the Python pipeline, to audit an earlier version of the analysis and identify the specification and linkage defects described above, to search for and verify the literature cited, and to assist in drafting. Every reported figure was computed from the source datasets by the scripts in the repository. Every citation was verified against the publisher record. All analytic decisions and the interpretation of results are the authors'.
