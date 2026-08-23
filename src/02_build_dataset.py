"""
02_build_dataset.py
-------------------
Join schools, ESSER ventilation reporting, and county context into the
analysis file. Everything about how a school gets an ESSER value is decided
here and nowhere else.

WHY THIS SCRIPT EXISTS
======================
The original pipeline joined the ED ESSER `crossact` sheet to NCES schools on
`str(ncesNumber).zfill(7)`, then applied a "reconstruction" rule: any state
whose observed funded rate fell below 2% was declared non-reporting and had
all of its schools recoded to missing. That produced a list of nine
"non-reporting jurisdictions" (AS, AZ, CT, GU, MP, OK, TX, VI, WA) which the
draft then treated as a transparency finding.

Checking the raw file, none of the three premises hold.

  1. AZ, CT, TX and WA reported ventilation status for every one of their
     LEAs (601, 200, 1,186 and 310 respectively; funded rates 41.4%, 41.0%,
     23.4%, 52.3%). What they omitted is the `ncesNumber` field, which is
     null for 100% of their rows. The join fails; the reporting did not.

  2. Oklahoma reported all 540 of its LEAs, with valid NCES identifiers, and
     every one of them answered False. That is a real statewide zero, and the
     <2% rule is precisely the rule that throws it away. Dropping true zeros
     biases the national funded rate upward.

  3. AS, GU, MP and VI are simply absent from the file.

`zfill(7)` also creates false matches. New Hampshire and Nevada rows carry
identifiers that are not NCES LEAIDs; zero-padded, some land on real Arkansas
LEAIDs, attaching New Hampshire's answers to Arkansas schools and adding 688
duplicate rows across 602 schools. This script validates that the first two digits of a
padded identifier equal the state's own FIPS code and discards the identifier
otherwise, which removes the collisions.

MISSING VS ZERO
===============
A school gets HAS_VENT = 1 or 0 only when its LEAID appears in the ESSER file
with a non-null ventilation answer. Every other school is missing, never zero.
This matters more than it sounds: the draft's regional table was computed with
blanks read as zeros, which is where "South Bronx, 5.5% funded" came from. Of
471 Bronx County schools, 58 match an ESSER record. NYC's public schools are
assigned to geographic-district LEAIDs in NCES, while NYC reports ESSER as a
single LEA (3620580, "NYC Chancellor's Office", 827,736 students) that does
not appear in the NCES geocode file at all. That LEA reported
isEsserAUsedFundsVentilation = True.

We do not crosswalk NYC's geographic districts onto 3620580 here. Doing so
would mean asserting a mapping the source files do not contain, and the same
argument would apply to Vermont's supervisory unions (10 of 305 schools match)
and to charter authorisers in several states. Unmatched schools stay missing
and the coverage rate is reported per state as a result in its own right.

INPUTS   data/derived/school_exposure.csv        (from 01_build_exposure.py)
         data/raw/esf_hvac_spending.xlsx         (ED ESSER APR, FY2023, 'crossact')
         data/raw/ACSDT5Y2024.B19013-Data.csv    (county median household income)
         data/raw/ACSDT5Y2024.B03002-Data.csv    (county race/ethnicity)
OUTPUTS  data/derived/analysis_dataset.csv
         data/derived/lea_level.csv              (join-free LEA panel, all 17,026 LEAs)
         output/coverage_by_state.csv
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np
import pandas as pd

STATE_FIPS = {
    'AL':'01','AK':'02','AZ':'04','AR':'05','CA':'06','CO':'08','CT':'09','DE':'10',
    'DC':'11','FL':'12','GA':'13','HI':'15','ID':'16','IL':'17','IN':'18','IA':'19',
    'KS':'20','KY':'21','LA':'22','ME':'23','MD':'24','MA':'25','MI':'26','MN':'27',
    'MS':'28','MO':'29','MT':'30','NE':'31','NV':'32','NH':'33','NJ':'34','NM':'35',
    'NY':'36','NC':'37','ND':'38','OH':'39','OK':'40','OR':'41','PA':'42','RI':'44',
    'SC':'45','SD':'46','TN':'47','TX':'48','UT':'49','VT':'50','VA':'51','WA':'53',
    'WV':'54','WI':'55','WY':'56','PR':'72','AS':'60','GU':'66','MP':'69','VI':'78',
}

GRANT_COLS = {
    'isEsserAUsedFundsVentilation': 'Ventilation',
    'isEsserAUsedFundsCleaning': 'Cleaning',
    'isEsserAUsedFundsMasks': 'PPE/Masks',
}

TRUTHY = {True: 1.0, 'True': 1.0, 1: 1.0, '1': 1.0}
FALSY = {False: 0.0, 'False': 0.0, 0: 0.0, '0': 0.0}


def to_binary(s: pd.Series) -> pd.Series:
    """Map the ESSER boolean fields to 1/0, leaving anything else missing.

    Blank means the LEA did not answer the question. It does not mean no.
    """
    return s.map(lambda v: TRUTHY.get(v, FALSY.get(v, np.nan)))


def clean_leaid(raw: pd.Series, state: pd.Series) -> pd.Series:
    """Zero-pad to seven digits, then keep only identifiers whose leading two
    digits match the reporting state's FIPS code.

    Rejecting on the prefix is what removes the AR/NH and NV collisions. It
    also correctly rejects California's short local identifiers, which pad to
    a nonexistent FIPS 00.
    """
    padded = (raw.astype('Float64').astype('Int64').astype(str)
                 .str.replace('<NA>', '', regex=False).str.zfill(7))
    expect = state.map(STATE_FIPS)
    ok = padded.str.len().eq(7) & padded.str[:2].eq(expect)
    return padded.where(ok, other=pd.NA)


def load_esser(path: str):
    df = pd.read_excel(path, sheet_name='crossact',
                       usecols=['stateCode', 'reportingYear', 'entityName', 'ncesNumber',
                                'isLea', 'esserALeaEnrollmentUnique'] + list(GRANT_COLS))
    n_all = len(df)
    df = df[df['isLea'] == True].copy()                                    # noqa: E712
    print(f"    ESSER crossact: {n_all:,} rows -> {len(df):,} LEA rows "
          f"(reporting year {sorted(df.reportingYear.unique())})")

    for col in GRANT_COLS:
        df[col + '_bin'] = to_binary(df[col])
    df['PORTFOLIO'] = df.apply(
        lambda r: ', '.join(l for c, l in GRANT_COLS.items() if r[c + '_bin'] == 1.0) or 'None',
        axis=1)
    df.loc[df[[c + '_bin' for c in GRANT_COLS]].isna().all(axis=1), 'PORTFOLIO'] = pd.NA

    df['LEAID'] = clean_leaid(df['ncesNumber'], df['stateCode'])

    # --- diagnostics that become Table 1 of the paper -----------------------
    cov = (df.groupby('stateCode')
             .agg(leas=('LEAID', 'size'),
                  leas_with_valid_id=('LEAID', lambda s: s.notna().sum()),
                  vent_answered=('isEsserAUsedFundsVentilation_bin', lambda s: s.notna().sum()),
                  vent_funded=('isEsserAUsedFundsVentilation_bin', lambda s: (s == 1).sum()),
                  enrollment=('esserALeaEnrollmentUnique', 'sum')))
    cov['pct_id'] = (cov.leas_with_valid_id / cov.leas * 100).round(1)
    cov['lea_funded_pct'] = (cov.vent_funded / cov.vent_answered * 100).round(1)

    unlinkable = sorted(cov.index[cov.leas_with_valid_id == 0])
    print(f"    states reporting ventilation but with NO usable NCES identifier: {unlinkable}")
    print(f"    LEA-level national funded rate (join-free): "
          f"{cov.vent_funded.sum() / cov.vent_answered.sum() * 100:.1f}% "
          f"of {int(cov.vent_answered.sum()):,} LEAs")

    # Collapse to one row per valid LEAID. A handful of authorisers file under a
    # shared identifier (Nevada's State Public Charter School Authority is the
    # clear case), so resolve by "funded if any constituent record says funded"
    # and count how often that arbitration was needed.
    linked = df[df.LEAID.notna()].copy()
    dup = linked.LEAID.duplicated(keep=False)
    conflicts = (linked[dup].groupby('LEAID')['isEsserAUsedFundsVentilation_bin']
                            .nunique(dropna=True).gt(1).sum())
    print(f"    LEAIDs appearing more than once: {linked.LEAID[dup].nunique():,} "
          f"(of which {conflicts} disagree on ventilation and are resolved to 'any = funded')")

    agg = (linked.groupby('LEAID')
                 .agg(HAS_VENT=('isEsserAUsedFundsVentilation_bin', 'max'),
                      HAS_CLEAN=('isEsserAUsedFundsCleaning_bin', 'max'),
                      HAS_PPE=('isEsserAUsedFundsMasks_bin', 'max'),
                      LEA_STATE=('stateCode', 'first'),
                      LEA_NAME=('entityName', 'first'),
                      LEA_ENROLL=('esserALeaEnrollmentUnique', 'sum'))
                 .reset_index())
    agg['PORTFOLIO'] = agg.apply(
        lambda r: ', '.join(l for c, l in zip(['HAS_VENT', 'HAS_CLEAN', 'HAS_PPE'],
                                              GRANT_COLS.values()) if r[c] == 1.0) or 'None',
        axis=1)
    agg.loc[agg[['HAS_VENT', 'HAS_CLEAN', 'HAS_PPE']].isna().all(axis=1), 'PORTFOLIO'] = pd.NA
    return agg, df, cov


def load_acs_income(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, skiprows=[1], dtype=str)
    df['COUNTY_FIPS'] = df['GEO_ID'].str.split('US').str[-1].str.zfill(5)
    df['median_income'] = pd.to_numeric(df['B19013_001E'], errors='coerce')
    return df[['COUNTY_FIPS', 'median_income']].dropna(subset=['COUNTY_FIPS'])


def load_acs_race(path: str) -> pd.DataFrame:
    """percent people of color = 1 - (non-Hispanic White alone / total).

    B03002_001E is the county total; B03002_003E is non-Hispanic White alone.
    Using the Hispanic-origin table rather than B02001 avoids double-counting
    Hispanic respondents who report White race.
    """
    df = pd.read_csv(path, skiprows=[1], dtype=str)
    df['COUNTY_FIPS'] = df['GEO_ID'].str.split('US').str[-1].str.zfill(5)
    total = pd.to_numeric(df['B03002_001E'], errors='coerce')
    nhw = pd.to_numeric(df['B03002_003E'], errors='coerce')
    df['pct_poc'] = np.where(total > 0, (1.0 - nhw / total) * 100.0, np.nan)
    return df[['COUNTY_FIPS', 'pct_poc']].dropna(subset=['COUNTY_FIPS'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--exposure', default='data/derived/school_exposure.csv')
    ap.add_argument('--esser', default='data/raw/esf_hvac_spending.xlsx')
    ap.add_argument('--income', default='data/raw/ACSDT5Y2024.B19013-Data.csv')
    ap.add_argument('--race', default='data/raw/ACSDT5Y2024.B03002-Data.csv')
    ap.add_argument('--outdir', default='data/derived')
    ap.add_argument('--outputs', default='output')
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    os.makedirs(a.outputs, exist_ok=True)

    print('--- 1. ESSER ---')
    lea, lea_raw, cov = load_esser(a.esser)

    print('--- 2. SCHOOLS + EXPOSURE ---')
    sch = pd.read_csv(a.exposure, dtype={'NCESSCH': str, 'LEAID': str, 'CNTY': str})
    sch['CNTY'] = sch['CNTY'].str.zfill(5)
    print(f"    {len(sch):,} geolocated schools")

    df = sch.merge(lea.drop(columns=['LEA_STATE']), on='LEAID', how='left')
    assert len(df) == len(sch), 'the LEA join must not change the row count'

    print('--- 3. COUNTY CONTEXT (ACS 5-year, 2024 vintage) ---')
    inc = load_acs_income(a.income)
    race = load_acs_race(a.race)
    df = df.merge(inc, left_on='CNTY', right_on='COUNTY_FIPS', how='left').drop(columns='COUNTY_FIPS')
    df = df.merge(race, left_on='CNTY', right_on='COUNTY_FIPS', how='left').drop(columns='COUNTY_FIPS')
    print(f"    income matched for {df.median_income.notna().sum():,}/{len(df):,} schools; "
          f"race for {df.pct_poc.notna().sum():,}")

    # --- linkability, stated as data rather than assumed -----------------------
    reported_states = set(cov.index[cov.vent_answered > 0])
    linkable_states = set(cov.index[cov.leas_with_valid_id > 0])
    df['STATE_REPORTED'] = df.STATE.isin(reported_states)
    df['STATE_LINKABLE'] = df.STATE.isin(linkable_states)
    df['ANALYTIC'] = df.STATE_LINKABLE & df.HAS_VENT.notna() & df.EXPOSURE.notna()

    by_state = (df.groupby('STATE')
                  .agg(schools=('NCESSCH', 'size'), matched=('HAS_VENT', lambda s: s.notna().sum()))
                  .assign(pct_matched=lambda d: (d.matched / d.schools * 100).round(1)))
    by_state = by_state.join(cov[['leas', 'leas_with_valid_id', 'pct_id',
                                  'vent_answered', 'vent_funded', 'lea_funded_pct']], how='left')
    by_state.to_csv(os.path.join(a.outputs, 'coverage_by_state.csv'))

    print(f"\n    school-level ESSER coverage: {df.HAS_VENT.notna().sum():,}/{len(df):,} "
          f"({df.HAS_VENT.notna().mean()*100:.1f}%)")
    print('    ten lowest-coverage states:')
    print(by_state.sort_values('pct_matched')[['schools', 'matched', 'pct_matched', 'pct_id',
                                               'lea_funded_pct']].head(10).to_string())

    df.to_csv(os.path.join(a.outdir, 'analysis_dataset.csv'), index=False)
    lea_raw.to_csv(os.path.join(a.outdir, 'lea_level.csv'), index=False)
    print(f"\n    wrote analysis_dataset.csv ({len(df):,} rows) and lea_level.csv ({len(lea_raw):,} rows)")


if __name__ == '__main__':
    sys.exit(main())
