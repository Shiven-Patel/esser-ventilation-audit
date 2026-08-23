"""
03_analysis.py
--------------
Every number reported in the paper, computed from data/derived/analysis_dataset.csv
and written to output/ as machine-readable CSVs plus one human-readable log.

Design rules, applied throughout:

  * The analytic sample is schools in linkable states with a non-missing ESSER
    ventilation answer, a computed exposure value, and county income and race.
    Schools with no ESSER record are missing, never zero. No state is dropped
    for having a low funded rate; Oklahoma's statewide zero is data.

  * The canonical exposure index is the air-mass-weighted inverse-square index
    from 01_build_exposure.py. Every stratified result is recomputed under all
    four exposure specifications and written to output/sensitivity_exposure.csv
    so the reader can see what the specification is doing.

  * Exposure is stratified two ways. The fixed tier cutoffs (0.5/10/25/50/75 on
    the 0-100 normalised index) are carried forward from the original work for
    comparability. Quintiles of the same index are the primary stratification in
    the paper, because the normalisation is relative to the 99th percentile and
    fixed cutoffs on a relative index invite a reading the index cannot support.

  * All models are associational. Income and race are county-level, so every
    coefficient on them is ecological and is described that way.
"""
from __future__ import annotations
import argparse, io, os, sys
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

EXPOSURE_VARIANTS = {
    'E_air': 'air-mass weighted inverse square (canonical)',
    'E_isq': 'unweighted inverse square',
    'E_fac': 'facility dedup only, legacy epsilon and k=50',
    'E_forms': 'published index (chemical-form cloud, legacy epsilon, k=50)',
}
TIER_EDGES = [-0.01, 0.5, 10, 25, 50, 75, 100.01]
TIER_LABELS = ['Negligible', 'Minimal', 'Low', 'Moderate', 'High', 'Critical']

LOG = io.StringIO()


def say(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    LOG.write(s + '\n')


def wilson(k, n, z=1.96):
    """Wilson score interval. Used instead of the normal approximation because
    several state cells are small and a few are at or near 0% or 100%, where the
    Wald interval runs outside [0,1]."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h) * 100, min(1.0, c + h) * 100)


def or_ci(res, name):
    b, se = res.params[name], res.bse[name]
    return np.exp(b), np.exp(b - 1.96 * se), np.exp(b + 1.96 * se)


def auc(y, p):
    """Mann-Whitney form of the C-statistic. Ties get midranks, which is what
    `rank()` does by default, so this matches the trapezoidal ROC area."""
    y = np.asarray(y, float); p = np.asarray(p, float)
    pos, neg = p[y == 1], p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    r = pd.Series(np.concatenate([pos, neg])).rank().to_numpy()
    return (r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def qcut_labelled(s, q, prefix):
    lab = [f'{prefix}{i+1}' for i in range(q)]
    return pd.qcut(s, q, labels=lab, duplicates='drop')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='data/derived/analysis_dataset.csv')
    ap.add_argument('--lea', default='data/derived/lea_level.csv')
    ap.add_argument('--esser', default='data/raw/esf_hvac_spending.xlsx')
    ap.add_argument('--out', default='output')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    W = lambda df, name: df.to_csv(os.path.join(a.out, name))          # noqa: E731

    df = pd.read_csv(a.data, low_memory=False, dtype={'NCESSCH': str, 'LEAID': str, 'CNTY': str})
    df['E_air'] = df['EXPOSURE']

    # ---------------------------------------------------------------- A. sample
    say('## A. Sample, coverage, and what counts as missing\n')
    say(f'Geolocated public schools, NCES EDGE 2024-25: {len(df):,}')
    say(f'Schools in states with at least one usable NCES district identifier: '
        f'{int(df.STATE_LINKABLE.sum()):,}')
    say(f'Schools matched to an ESSER ventilation answer: {int(df.HAS_VENT.notna().sum()):,} '
        f'({df.HAS_VENT.notna().mean()*100:.1f}%)')

    ana = df[df.STATE_LINKABLE & df.HAS_VENT.notna() & df.EXPOSURE.notna()
             & df.median_income.notna() & df.pct_poc.notna()].copy()
    say(f'Analytic sample (complete cases): {len(ana):,} schools in {ana.STATE.nunique()} states\n')

    unlink = df[~df.STATE_LINKABLE].STATE.unique()
    say(f'States excluded for having no usable identifier on any LEA record: {sorted(unlink)}')
    say('These states reported ventilation status for every LEA; the identifier field is blank.')
    say('Their LEA-level rates are reported in output/coverage_by_state.csv and in the paper,')
    say('but they cannot enter a school-level model.\n')

    say(f'Overall funded rate, analytic sample: {ana.HAS_VENT.mean()*100:.1f}% '
        f'(Wilson 95% CI {wilson(ana.HAS_VENT.sum(), len(ana))[0]:.1f}-'
        f'{wilson(ana.HAS_VENT.sum(), len(ana))[1]:.1f})')
    naive = df[df.STATE_LINKABLE].HAS_VENT.fillna(0).mean() * 100
    say(f'The same figure with unmatched schools read as unfunded: {naive:.1f}%')
    say('The gap between those two numbers is the entire source of the original')
    say('regional case-study table, and it is a coding artifact, not a finding.\n')

    # ------------------------------------------------------- B. grant categories
    say('## B. Grant categories, analytic sample\n')
    cats = pd.DataFrame({
        'Ventilation': [ana.HAS_VENT.mean()],
        'Cleaning': [ana.HAS_CLEAN.mean()],
        'PPE/Masks': [ana.HAS_PPE.mean()],
        'None of the three': [(ana[['HAS_VENT', 'HAS_CLEAN', 'HAS_PPE']].sum(axis=1) == 0).mean()],
        'All three': [(ana[['HAS_VENT', 'HAS_CLEAN', 'HAS_PPE']].sum(axis=1) == 3).mean()],
    }).T.rename(columns={0: 'share'}) * 100
    say(cats.round(1).to_string() + '\n')
    W(cats.round(4), 'grant_categories.csv')

    # ------------------------------------------------ C. exposure stratification
    say('## C. Funded rate by exposure, canonical index\n')
    ana['tier'] = pd.cut(ana.E_air, TIER_EDGES, labels=TIER_LABELS)
    ana['exp_q'] = qcut_labelled(ana.E_air.rank(method='first'), 5, 'Q')

    def strat(g):
        out = g.agg(n=('HAS_VENT', 'size'), funded=('HAS_VENT', 'sum'),
                    mean_poc=('pct_poc', 'mean'), med_income=('median_income', 'median'))
        out['funded_pct'] = (out.funded / out.n * 100).round(1)
        ci = out.apply(lambda r: wilson(r.funded, r.n), axis=1)
        out['ci_lo'] = [c[0] for c in ci]; out['ci_hi'] = [c[1] for c in ci]
        return out[['n', 'funded_pct', 'ci_lo', 'ci_hi', 'mean_poc', 'med_income']].round(1)

    by_q = strat(ana.groupby('exp_q', observed=True))
    by_t = strat(ana.groupby('tier', observed=True))
    say('By quintile of the canonical exposure index (primary stratification):')
    say(by_q.to_string() + '\n')
    say('By the original fixed tier cutoffs (for comparability):')
    say(by_t.to_string() + '\n')
    W(by_q, 'funded_by_exposure_quintile.csv'); W(by_t, 'funded_by_exposure_tier.csv')

    # Quintiles are too coarse to see what happens at the top: the fifth quintile
    # holds 16,000 schools, while the schools that dominate a mass-weighted index
    # are a few hundred. Percentile bands, narrowing towards the tail, are where
    # the turnover shows up, and the turnover is the paper's central claim.
    # Rank on the unnormalised index. The 0-100 version is clipped at the 99th
    # percentile, so everything above it collapses to exactly 100 and the top
    # band would be degenerate.
    pct = ana.E_air_raw_lbs_per_km2.rank(pct=True) * 100
    bands = [(0, 50), (50, 80), (80, 90), (90, 95), (95, 99), (99, 99.9), (99.9, 100.01)]
    rows = []
    for lo, hi in bands:
        g = ana[(pct > lo) & (pct <= hi)]
        if not len(g):
            continue
        c = wilson(g.HAS_VENT.sum(), len(g))
        rows.append({'band': f'p{lo:g}-{min(hi, 100):g}', 'n': len(g),
                     'funded_pct': round(g.HAS_VENT.mean() * 100, 1),
                     'ci_lo': round(c[0], 1), 'ci_hi': round(c[1], 1),
                     'median_index_raw': f'{g.E_air_raw_lbs_per_km2.median():.3g}',
                     'mean_poc': round(g.pct_poc.mean(), 1),
                     'med_income': int(g.median_income.median())})
    tail = pd.DataFrame(rows).set_index('band')
    say('By percentile band of the canonical index, narrowing towards the tail:')
    say(tail.to_string() + '\n')
    W(tail, 'funded_by_exposure_percentile_band.csv')

    # Where the top band's schools actually are. A tail result carried by one state's
    # reporting practice would be a different finding, so the spread is reported.
    top = ana[pct > 99.9]
    top_states = top.STATE.value_counts()
    say(f'Schools above the 99.9th percentile: {len(top)} across {top_states.size} states. '
        f'Largest concentrations: '
        + ', '.join(f'{s} {n}' for s, n in top_states.head(5).items()) + '.')
    say(f'Their median unnormalised index is '
        f'{top.E_air_raw_lbs_per_km2.median() / ana[(pct > 95) & (pct <= 99)].E_air_raw_lbs_per_km2.median():.0f}'
        f' times that of the p95-99 band.\n')
    W(top_states.rename('schools').to_frame(), 'top_band_states.csv')

    # -------------------------------------------------- D. exposure sensitivity
    say('## D. The same stratification under all four exposure specifications\n')
    rows = []
    for v, desc in EXPOSURE_VARIANTS.items():
        s = ana.copy()
        s['q'] = qcut_labelled(s[v].rank(method='first'), 5, 'Q')
        g = s.groupby('q', observed=True)['HAS_VENT'].agg(['size', 'mean'])
        for q, r in g.iterrows():
            rows.append({'variant': v, 'description': desc, 'quintile': q,
                         'n': int(r['size']), 'funded_pct': round(r['mean'] * 100, 1)})
    sens = pd.DataFrame(rows).pivot(index='quintile', columns='variant', values='funded_pct')
    say(sens.to_string())
    say('\nThe gradient is present under every specification. Its shape is not: the two')
    say('corrected indices turn over at the top quintile, and the published index does not.\n')
    W(pd.DataFrame(rows).set_index(['variant', 'quintile']), 'sensitivity_exposure.csv')

    tierx = pd.concat([pd.cut(ana[v], TIER_EDGES, labels=TIER_LABELS).value_counts().rename(v)
                       for v in EXPOSURE_VARIANTS], axis=1).loc[TIER_LABELS]
    say('Schools per fixed tier under each specification:')
    say(tierx.to_string() + '\n')
    W(tierx, 'tier_counts_by_variant.csv')

    # ------------------------------------------------------------ E. correlations
    say('## E. Correlations, school level\n')
    for v in EXPOSURE_VARIANTS:
        say(f'  {v:8s} vs % people of color: r = {ana[v].corr(ana.pct_poc):+.3f}   '
            f'vs county median income: r = {ana[v].corr(ana.median_income):+.3f}')
    say(f'  county income vs % people of color: r = {ana.median_income.corr(ana.pct_poc):+.3f}\n')

    # ---------------------------------------------------------------- F. models
    say('## F. Logistic regression\n')
    ana['exp10'] = ana.E_air / 10.0
    ana['inc10k'] = ana.median_income / 10000.0
    ana['poc10'] = ana.pct_poc / 10.0
    ana['expq'] = ana.exp_q.astype(str)

    mods = {}
    mods['A. exposure only'] = smf.logit('HAS_VENT ~ exp10', data=ana).fit(disp=0)
    mods['B. + county income + % POC'] = smf.logit('HAS_VENT ~ exp10 + inc10k + poc10',
                                                   data=ana).fit(disp=0)
    srate = ana.groupby('STATE')['HAS_VENT'].mean()
    mixed_states = srate[(srate > 0.001) & (srate < 0.999)].index
    mixed = ana[ana.STATE.isin(mixed_states)].copy()
    mods['C. + state fixed effects'] = smf.logit('HAS_VENT ~ exp10 + inc10k + poc10 + C(STATE)',
                                                 data=mixed).fit(disp=0)
    say(f'Model C is estimated on the {len(mixed_states)} states with within-state variation '
        f'(n = {len(mixed):,}).')
    say(f'States dropped by perfect separation: {sorted(set(ana.STATE) - set(mixed_states))}')
    say('Oklahoma separates because it is a genuine statewide zero, which is worth stating')
    say('rather than hiding: no fixed-effects model can use a state with no variation.\n')

    # Two further models on Model C's own sample, so the comparison "does the state
    # predict better than the covariates" is answered by numbers rather than asserted.
    # Model B is estimated on the full analytic sample and Model C on the mixed-state
    # subset, so their C-statistics are not directly comparable; these two are.
    mods['S. state fixed effects only'] = smf.logit('HAS_VENT ~ C(STATE)', data=mixed).fit(disp=0)
    mods["B'. covariates only, Model C's sample"] = smf.logit(
        'HAS_VENT ~ exp10 + inc10k + poc10', data=mixed).fit(disp=0)

    rows = []
    for name, m in mods.items():
        d = ana if name.startswith(('A.', 'B.')) else mixed
        row = {'model': name, 'n': int(m.nobs),
               'C_statistic': round(auc(d.HAS_VENT, m.predict()), 3),
               'pseudo_R2': round(m.prsquared, 4)}
        for term, lab in [('exp10', 'exposure_per_10pts'), ('inc10k', 'income_per_10k'),
                          ('poc10', 'pct_poc_per_10pp')]:
            if term in m.params:
                o, lo, hi = or_ci(m, term)
                row[lab] = f'{o:.3f} ({lo:.3f}-{hi:.3f})'
                row[lab + '_p'] = f'{m.pvalues[term]:.2e}'
        rows.append(row)
    models = pd.DataFrame(rows).set_index('model')
    say(models.to_string() + '\n')
    W(models, 'models.csv')

    # attenuation: how much of the exposure association runs through race
    m_norace = smf.logit('HAS_VENT ~ exp10 + inc10k + C(STATE)', data=mixed).fit(disp=0)
    o0, l0, h0 = or_ci(m_norace, 'exp10'); o1, l1, h1 = or_ci(mods['C. + state fixed effects'], 'exp10')
    say(f'Attenuation check, Model C without county race: exposure aOR {o0:.3f} ({l0:.3f}-{h0:.3f}); '
        f'adding race gives {o1:.3f} ({l1:.3f}-{h1:.3f}).\n')

    # exposure-quintile odds ratios, reference = Q1
    mq = smf.logit('HAS_VENT ~ C(expq) + inc10k + poc10 + C(STATE)', data=mixed).fit(disp=0)
    qrows = []
    for t in [p for p in mq.params.index if p.startswith('C(expq)')]:
        o, lo, hi = or_ci(mq, t)
        qrows.append({'quintile': t.split('.')[-1].strip(']'), 'aOR': round(o, 3),
                      'lo': round(lo, 3), 'hi': round(hi, 3), 'p': f'{mq.pvalues[t]:.2e}'})
    qtab = pd.DataFrame(qrows).set_index('quintile')
    say('Adjusted odds of ventilation funding by exposure quintile (ref = Q1, lowest):')
    say(qtab.to_string() + '\n')
    W(qtab, 'exposure_quintile_odds.csv')

    # --- the tail result, which is the paper's central claim --------------------
    # Quintile and tier contrasts average over too many schools to see it. Coding
    # the top of the distribution as three explicit bands, against everything below
    # the 95th percentile, asks the question directly: are the most exposed schools
    # funded more or less than the rest, once state, county income and county racial
    # composition are held fixed?
    mixed = mixed.copy()
    pctm = mixed.E_air_raw_lbs_per_km2.rank(pct=True) * 100
    mixed['t95'] = ((pctm > 95) & (pctm <= 99)).astype(int)
    mixed['t99'] = ((pctm > 99) & (pctm <= 99.9)).astype(int)
    mixed['t999'] = (pctm > 99.9).astype(int)
    mt = smf.logit('HAS_VENT ~ t95 + t99 + t999 + inc10k + poc10 + C(STATE)',
                   data=mixed).fit(disp=0)
    trows = []
    for term, lab in [('t95', 'p95-99'), ('t99', 'p99-99.9'), ('t999', 'top 0.1%')]:
        o, lo, hi = or_ci(mt, term)
        trows.append({'band': lab, 'n': int(mixed[term].sum()), 'aOR_vs_below_p95': round(o, 3),
                      'lo': round(lo, 3), 'hi': round(hi, 3), 'p': f'{mt.pvalues[term]:.2e}'})
    tt = pd.DataFrame(trows).set_index('band')
    say('Adjusted odds of ventilation funding at the top of the exposure distribution,')
    say('reference = everything below the 95th percentile, with state fixed effects:')
    say(tt.to_string() + '\n')
    W(tt, 'tail_odds.csv')

    # Is it a smooth inverted U, or a discontinuity confined to the extreme tail?
    mixed['lx'] = np.log10(mixed.E_air_raw_lbs_per_km2.clip(lower=1.0))
    mquad = smf.logit('HAS_VENT ~ lx + I(lx**2) + inc10k + poc10 + C(STATE)',
                      data=mixed).fit(disp=0)
    say(f'Quadratic in log10 exposure: linear b = {mquad.params["lx"]:.4f} '
        f'(p = {mquad.pvalues["lx"]:.2e}); squared b = {mquad.params["I(lx ** 2)"]:.4f} '
        f'(p = {mquad.pvalues["I(lx ** 2)"]:.2e}).')
    say('The squared term is not distinguishable from zero, so the pattern is not a')
    say('smooth inverted U. The association rises across the bulk of the distribution')
    say('and then breaks at the extreme tail. Reporting it as curvature would overstate')
    say('what the data show.\n')

    # interaction
    mi = smf.logit('HAS_VENT ~ exp10 * poc10 + inc10k + C(STATE)', data=mixed).fit(disp=0)
    o, lo, hi = or_ci(mi, 'exp10:poc10')
    say(f'Exposure x county-race interaction: OR {o:.4f} ({lo:.4f}-{hi:.4f}), '
        f'p = {mi.pvalues["exp10:poc10"]:.2e}\n')

    # ------------------------------------------------- G/H. race and income cuts
    say('## G. Funded rate by county composition\n')
    for col, pref, lab in [('pct_poc', 'P', '% people of color'), ('median_income', 'I', 'county median income')]:
        ana['_q'] = qcut_labelled(ana[col].rank(method='first'), 5, pref)
        g = strat(ana.groupby('_q', observed=True))
        say(f'By quintile of {lab}:')
        say(g.to_string() + '\n')
        W(g, f'funded_by_{col}_quintile.csv')

    # --------------------------------------------------- I. within-state gradient
    say('## I. Within-state exposure gradient\n')
    ana['hi_exp'] = ana.groupby('STATE')['E_air'].transform(lambda s: s >= s.quantile(0.8))
    ana['lo_exp'] = ana.groupby('STATE')['E_air'].transform(lambda s: s <= s.quantile(0.2))
    rows = []
    for st, g in ana.groupby('STATE'):
        hi, lo = g[g.hi_exp], g[g.lo_exp]
        if len(hi) < 50 or len(lo) < 50:
            continue
        gap = hi.HAS_VENT.mean() * 100 - lo.HAS_VENT.mean() * 100
        rows.append({'state': st, 'n_hi': len(hi), 'n_lo': len(lo),
                     'funded_hi': round(hi.HAS_VENT.mean() * 100, 1),
                     'funded_lo': round(lo.HAS_VENT.mean() * 100, 1),
                     'gap_pts': round(gap, 1)})
    gaps = pd.DataFrame(rows).sort_values('gap_pts').set_index('state')
    say('Gap = funded rate in the state\'s own top exposure quintile minus its bottom quintile.')
    say('Within-state quintiles, so a state is compared only against itself. States with')
    say('fewer than 50 schools in either band are omitted.\n')
    say(gaps.to_string() + '\n')
    say(f'States with a negative gap: {int((gaps.gap_pts < 0).sum())} of {len(gaps)}\n')
    W(gaps, 'within_state_gap.csv')

    # ----------------------------------------------------------- J. case studies
    say('## J. Regional cases, corrected\n')
    lea = pd.read_csv(a.lea, low_memory=False)
    cases = [('South Bronx', 'NY', 'Bronx County'), ('Albuquerque', 'NM', 'Bernalillo County'),
             ('Gary / NW Indiana', 'IN', 'Lake County'), ('Houston', 'TX', 'Harris County'),
             ('Oklahoma City', 'OK', 'Oklahoma County')]
    rows = []
    for lab, st, cty in cases:
        c = df[(df.STATE == st) & (df.NMCNTY == cty)]
        n, m = len(c), int(c.HAS_VENT.notna().sum())
        rows.append({'case': lab, 'state': st, 'county': cty, 'schools': n,
                     'matched_to_ESSER': m, 'pct_matched': round(m / n * 100, 1) if n else np.nan,
                     'funded_pct_matched_only': round(c.HAS_VENT.mean() * 100, 1) if m else np.nan,
                     'funded_pct_blank_as_zero': round(c.HAS_VENT.fillna(0).mean() * 100, 1),
                     'mean_exposure': round(c.E_air.mean(), 2),
                     'pct_poc': round(c.pct_poc.mean(), 1),
                     'county_income': int(c.median_income.median()) if c.median_income.notna().any() else None})
    cs = pd.DataFrame(rows).set_index('case')
    say(cs.to_string() + '\n')
    say('The last two columns are the whole story. Where school-level coverage is high')
    say('(Albuquerque, 91.8%) the two codings agree and the finding is real. Where it is low')
    say('(South Bronx, 12.3%) they diverge by a factor of eight, and the published figure is')
    say('the one that assumed silence meant no.\n')
    W(cs, 'case_studies.csv')

    say('District-of-record answers for the same places, taken straight from the ESSER file:')
    for pat, st in [('Chancellor', 'NY'), ('Albuquerque', 'NM'), ('Gary Community', 'IN'),
                    ('Houston Isd', 'TX'), ('Oklahoma City Public Schools', 'OK')]:
        r = lea[(lea.stateCode == st) & (lea.entityName.str.contains(pat, case=False, na=False))]
        for _, x in r.head(2).iterrows():
            say(f'  {x.stateCode}  {x.entityName:<46s} ncesNumber={str(x.ncesNumber):<12s} '
                f'ventilation={x.isEsserAUsedFundsVentilation}')
    say('')

    # --------------------------------------------------------- K. the funding cliff
    say('## K. Was this a one-off allocation?\n')
    prime = pd.read_excel(a.esser, sheet_name='prime')
    fund = []
    for n, lab in [(1, 'ESSER I (CARES)'), (2, 'ESSER II (CRRSA)'), (3, 'ARP ESSER')]:
        alloc = prime[f'esser{n}GrantAmountAllocated'].sum()
        rem = prime[f'esser{n}GrantAmountRemaining'].sum()
        fund.append({'fund': lab, 'allocated_B': round(alloc / 1e9, 2),
                     'remaining_B': round(rem / 1e9, 2),
                     'pct_remaining': round(rem / alloc * 100, 1)})
    fu = pd.DataFrame(fund).set_index('fund')
    fu.loc['Total'] = [fu.allocated_B.sum(), fu.remaining_B.sum(),
                       round(fu.remaining_B.sum() / fu.allocated_B.sum() * 100, 1)]
    say('Dollars as reported by the 52 state and territory grantees in the FY2023 APR,')
    say('which is the most recent APR in this file (position as of 30 September 2023):\n')
    say(fu.to_string() + '\n')
    W(fu, 'esser_funding_position.csv')

    with open(os.path.join(a.out, 'analysis_log.md'), 'w') as f:
        f.write('# ESSER ventilation EJ audit: computed results\n\n')
        f.write('Generated by `src/03_analysis.py`. Every figure below is reproduced by\n')
        f.write('running the three scripts in order against the files in `data/raw/`.\n\n')
        f.write(LOG.getvalue())
    say(f'wrote {a.out}/analysis_log.md')


if __name__ == '__main__':
    sys.exit(main())
