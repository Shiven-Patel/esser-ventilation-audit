"""
00_audit_legacy.py
------------------
Reproduce and quantify the four defects in the earlier pipeline.

This script exists so the claims in README.md and docs/METHODS.md are checkable
rather than asserted. It does not feed the analysis; nothing downstream depends
on it. Run it once to confirm the diagnosis, or run it against a modified legacy
script to see whether a proposed fix actually fixes anything.

The first thing it does is reproduce the published exposure index. If that
reproduction does not come back at r > 0.9999 against the shipped EXPOSURE
column, the rest of the diagnosis is describing some other pipeline and should
not be trusted.

  Defect 1  TRI aggregation: the index summed over chemical-release forms, not
            facilities, weighting each facility by its chemical count.
  Defect 2  Neighbour cap: k=50 over a form-level point cloud, so the cap bound
            for most schools and hid every facility past the 50th nearest form.
  Defect 3  Softening constant: 1e-5 added to squared radian distance, which
            dominates the denominator out to roughly 20 km and flattens the
            inverse square into a near-count.
  Defect 4  Linkage and missingness: zero-padded identifiers collide across
            states; blanks were read as zeros at the community scale; and a
            "state funded rate below 2 percent means non-reporting" rule
            deleted Oklahoma's genuine statewide zero.

USAGE
    python src/00_audit_legacy.py \
        --legacy-dataset /path/to/old/school_audit_dataset.csv

The --legacy-dataset argument is optional. Without it the script still runs
defects 1 to 3 and the linkage diagnostics; it just cannot verify the
reproduction against the shipped column.
"""
from __future__ import annotations
import argparse
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

import importlib.util
import os
import sys

_here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('build_exposure',
                                              os.path.join(_here, '01_build_exposure.py'))
bx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bx)

STATE_FIPS_PATH = os.path.join(_here, '02_build_dataset.py')
spec2 = importlib.util.spec_from_file_location('build_dataset', STATE_FIPS_PATH)
bd = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(bd)

LEGACY_EPS = 1e-5
LEGACY_K = 50
BOUND_RAD = 0.0078          # the legacy bound, ~49.7 km
R_KM = 6371.0


def rule(title):
    print('\n' + '=' * 78)
    print(title)
    print('=' * 78)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tri', default='data/raw/epa_tri_national.csv')
    ap.add_argument('--schools', default='data/raw/EDGE_GEOCODE_PUBLICSCH_2425.TXT')
    ap.add_argument('--esser', default='data/raw/esf_hvac_spending.xlsx')
    ap.add_argument('--legacy-dataset', default=None,
                    help='the old school_audit_dataset.csv, to verify the reproduction')
    a = ap.parse_args()

    rule('DEFECT 1 and 2: what the TRI file actually contains')
    raw = pd.read_csv(a.tri, usecols=lambda c: c.strip().upper().endswith(
        ('TRIFD', 'LATITUDE', 'LONGITUDE', 'YEAR')), low_memory=False)
    raw.columns = [c.strip().split('. ')[-1] for c in raw.columns]
    print(f'  rows in epa_tri_national.csv          {len(raw):,}')
    print(f'  distinct facilities (TRIFD)           {raw.TRIFD.nunique():,}')
    print(f'  reporting years present               {sorted(raw.YEAR.unique())}')
    top = raw.TRIFD.value_counts().head(3)
    print(f'  chemical forms filed by the top three facilities: {list(top.values)}')
    print('  A distance-weighted sum over these rows weights each facility by its')
    print('  chemical count, which reflects product mix and reporting obligations.')

    fac = bx.aggregate_tri(a.tri)
    sch = bx.load_schools(a.schools)
    s_rad = np.deg2rad(sch[['LAT', 'LON']].to_numpy(float))
    f_rad = np.deg2rad(fac[['lat', 'lon']].to_numpy(float))
    forms_rad = f_rad[np.repeat(np.arange(len(fac)), fac.n_chem_forms.to_numpy(int))]

    e_forms, n_forms, cap_forms = bx.idw(s_rad, forms_rad, None, LEGACY_K, eps=LEGACY_EPS)
    e_fac, n_fac, cap_fac = bx.idw(s_rad, f_rad, None, LEGACY_K, eps=LEGACY_EPS)
    e_isq, n_isq, _ = bx.idw(s_rad, f_rad, None, 500, floor_km=0.1)
    e_air, _, _ = bx.idw(s_rad, f_rad, fac.air_lbs.to_numpy(float), 500, floor_km=0.1)

    print(f'\n  k=50 cap binds for {cap_forms.mean()*100:5.1f}% of schools on the form-level cloud')
    print(f'  k=50 cap binds for {cap_fac.mean()*100:5.1f}% of schools on the facility-level cloud')
    print(f'  median facilities genuinely within 50 km: {int(np.median(n_isq))}')
    print('  Where the cap binds, every source past the 50th nearest is invisible.')

    rule('DEFECT 3: the softening constant erases the distance decay')
    print(f'  legacy denominator: d_rad^2 + {LEGACY_EPS:g}')
    for km in (0.5, 2, 5, 10, 20, 35, 50):
        d = km / R_KM
        legacy = 1.0 / (d ** 2 + LEGACY_EPS)
        true = 1.0 / (max(km, 0.1) ** 2)
        print(f'    at {km:5.1f} km   legacy weight {legacy:10,.0f}   '
              f'true inverse square (per km^2) {true:12.6f}')
    d50 = 50.0 / R_KM
    d05 = 0.5 / R_KM
    print(f'\n  legacy ratio, 0.5 km vs 50 km: '
          f'{(1/(d05**2+LEGACY_EPS)) / (1/(d50**2+LEGACY_EPS)):6.1f} : 1')
    print(f'  true inverse square, same pair: {(50.0/0.5)**2:6.0f} : 1')
    print('  Four orders of magnitude of decay compressed into less than one.')

    rule('CONSEQUENCE: how much of the published index survives the fixes')
    out = pd.DataFrame({'NCESSCH': sch.NCESSCH.astype(str),
                        'E_forms': bx.normalise(e_forms), 'E_fac': bx.normalise(e_fac),
                        'E_isq': bx.normalise(e_isq), 'E_air': bx.normalise(e_air)})

    if a.legacy_dataset:
        old = pd.read_csv(a.legacy_dataset, low_memory=False,
                          dtype={'NCESSCH': str}).drop_duplicates('NCESSCH')
        m = out.merge(old[['NCESSCH', 'EXPOSURE']], on='NCESSCH', how='inner')
        r = np.corrcoef(m.E_forms, m.EXPOSURE)[0, 1]
        print(f'  reproduction of the shipped EXPOSURE column: Pearson r = {r:.5f} '
              f'on {len(m):,} schools, mean |diff| = {np.abs(m.E_forms-m.EXPOSURE).mean():.4f}')
        if r < 0.9999:
            print('  WARNING: reproduction failed. The diagnosis below may describe a '
                  'different pipeline than the one that produced the legacy file.')
        print(f'  legacy file rows: {len(pd.read_csv(a.legacy_dataset, low_memory=False)):,}; '
              f'distinct NCESSCH: {old.NCESSCH.nunique():,}  '
              '(the difference is the identifier-collision duplication, defect 4)')
    else:
        print('  (--legacy-dataset not supplied; reproduction not verified)')

    tiers = lambda s: pd.cut(s, bx_edges := [-.01, .5, 10, 25, 50, 75, 100.01],
                             labels=['Negligible', 'Minimal', 'Low', 'Moderate',
                                     'High', 'Critical'])
    for v in ('E_fac', 'E_isq', 'E_air'):
        changed = (tiers(out[v]).astype(str) != tiers(out.E_forms).astype(str)).mean()
        print(f'  schools changing exposure tier, E_forms -> {v}: {changed*100:5.1f}%   '
              f'(Spearman rho {spearmanr(out.E_forms, out[v]).statistic:.3f})')
    cnt = pd.concat([tiers(out[v]).value_counts().rename(v)
                     for v in ('E_forms', 'E_fac', 'E_isq', 'E_air')], axis=1)
    print('\n  schools per tier under each specification:')
    print(cnt.to_string().replace('\n', '\n    '))

    rule('DEFECT 4a: zero-padded identifiers collide across states')
    e = pd.read_excel(a.esser, sheet_name='crossact',
                      usecols=['stateCode', 'entityName', 'ncesNumber', 'isLea',
                               'isEsserAUsedFundsVentilation'])
    e = e[e.isLea == True].copy()                                        # noqa: E712
    e['naive'] = (e.ncesNumber.astype('Float64').astype('Int64').astype(str)
                    .str.replace('<NA>', '', regex=False).str.zfill(7))
    e['validated'] = bd.clean_leaid(e.ncesNumber, e.stateCode)
    collisions = (e[e.naive.ne('') & e.validated.isna() & e.naive.str.len().eq(7)]
                  .groupby('naive').filter(lambda g: len(g) > 0))
    naive_dupes = e[e.naive.ne('')].naive.duplicated(keep=False).sum()
    valid_dupes = e[e.validated.notna()].validated.duplicated(keep=False).sum()
    print(f'  LEA rows                                        {len(e):,}')
    print(f'  duplicate identifiers under naive zfill(7)       {naive_dupes:,}')
    print(f'  duplicate identifiers after FIPS-prefix check    {valid_dupes:,}')
    print(f'  identifiers rejected because the leading two digits')
    print(f'  do not match the reporting state\'s FIPS code      {len(collisions):,}')
    ex = e[(e.stateCode.isin(['NH', 'AR'])) & (e.naive == '0502960')]
    if len(ex):
        print('\n  worked example, one identifier claimed by two states:')
        print(ex[['stateCode', 'entityName', 'ncesNumber',
                  'isEsserAUsedFundsVentilation']].to_string(index=False)
              .replace('\n', '\n    '))

    rule('DEFECT 4b: four states reported everything and identified nothing')
    cov = e.groupby('stateCode').agg(
        leas=('validated', 'size'),
        with_id=('validated', lambda s: s.notna().sum()),
        answered=('isEsserAUsedFundsVentilation', lambda s: s.notna().sum()),
        funded=('isEsserAUsedFundsVentilation', lambda s: (s == True).sum()))  # noqa: E712
    cov['pct_id'] = (cov.with_id / cov.leas * 100).round(1)
    cov['funded_pct'] = (cov.funded / cov.answered * 100).round(1)
    blind = cov[cov.with_id == 0]
    print(blind.to_string().replace('\n', '\n  '))
    print(f'\n  These {len(blind)} states answered the ventilation question for '
          f'{int(blind.answered.sum()):,} districts')
    print('  and left the NCES identifier blank on every row. A pipeline that infers')
    print('  reporting from a failed join will call them non-reporting.')

    rule('DEFECT 4c: the "below 2 percent means non-reporting" rule deletes a real zero')
    ok = cov.loc['OK']
    print(f'  Oklahoma: {int(ok.leas)} agencies, {int(ok.with_id)} with valid identifiers, '
          f'{int(ok.answered)} answered, {int(ok.funded)} funded.')
    print('  Every identifier is valid and every answer is False. This is a measured')
    print('  statewide zero, and the rule that removes it biases the national rate upward.')

    print('\nAudit complete.\n')


if __name__ == '__main__':
    sys.exit(main())
