"""
04_figures.py
-------------
Figures for the manuscript. Reads only the CSVs written by 03_analysis.py, so a
figure can never disagree with the reported number: if the table changes, the
figure changes with it.

No figure carries a title. Titles belong in the caption, which the manuscript
supplies, and a title burned into the image would appear twice in the typeset
document and could not be edited by a copy editor.

Palette is colourblind-safe (Okabe-Ito derived) and prints legibly in greyscale,
which Environmental Justice does not require but reviewers appreciate.
"""
from __future__ import annotations
import argparse, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

INK = '#1a1a1a'
BLUE = '#0072B2'
ORANGE = '#D55E00'
GREY = '#8c8c8c'
TEAL = '#009E73'
PURPLE = '#7B52AB'

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Liberation Serif', 'DejaVu Serif'],
    'font.size': 9, 'axes.titlesize': 10, 'axes.labelsize': 9,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.edgecolor': INK, 'text.color': INK, 'axes.labelcolor': INK,
    'xtick.color': INK, 'ytick.color': INK, 'figure.dpi': 200,
    'savefig.bbox': 'tight', 'savefig.facecolor': 'white',
})


def fig_tail(out, D):
    """Funded rate by exposure percentile band.

    The bands are deliberately unequal in width (half of all schools in the first,
    one percent in the last), so they are drawn as separate bars with the share of
    schools printed under each label rather than as points on a continuous axis,
    which a reader would take to be evenly spaced in exposure.
    """
    d = pd.read_csv(f'{D}/funded_by_exposure_percentile_band.csv', index_col=0)
    labs = {'p0-50': '0-50th', 'p50-80': '50-80th', 'p80-90': '80-90th',
            'p90-95': '90-95th', 'p95-99': '95-99th', 'p99-100': '99-100th'}
    share = {'p0-50': 50, 'p50-80': 30, 'p80-90': 10, 'p90-95': 5, 'p95-99': 4, 'p99-100': 1}
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    x = list(range(len(d)))
    ax.bar(x, d.funded_pct, width=0.62, color=BLUE, edgecolor='white')
    ax.errorbar(x, d.funded_pct, yerr=[d.funded_pct - d.ci_lo, d.ci_hi - d.funded_pct],
                fmt='none', ecolor=INK, capsize=3, lw=1)
    for i, (lab, r) in enumerate(d.iterrows()):
        ax.annotate(f'{r.funded_pct:.1f}%', (i, r.ci_hi), textcoords='offset points',
                    xytext=(0, 4), ha='center', fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([f'{labs.get(b, b)}\n{share.get(b, "")}% of schools\nn = {int(r.n):,}'
                        for b, r in d.iterrows()], fontsize=7.5)
    ax.set_xlabel('Percentile band of the exposure index (bands are not equal width)')
    ax.set_ylabel('Schools in districts that recorded\nventilation spending (%)')
    ax.set_ylim(0, 80)
    fig.savefig(f'{out}/fig_exposure_bands.png')
    plt.close(fig)


def fig_specification(out, D):
    d = pd.read_csv(f'{D}/tier_counts_by_variant.csv', index_col=0)
    order = ['Negligible', 'Minimal', 'Low', 'Moderate', 'High', 'Critical']
    d = d.loc[order]
    names = {'E_forms': 'A. Counts chemical reports,\nweak distance decay (earlier version)',
             'E_fac': 'B. Counts facilities,\nweak distance decay',
             'E_isq': 'C. Counts facilities,\ninverse-square distance',
             'E_air': 'D. Weights facilities by air releases,\ninverse-square distance (used here)'}
    cols = [c for c in ['E_forms', 'E_fac', 'E_isq', 'E_air'] if c in d.columns]
    fig, ax = plt.subplots(figsize=(6.6, 3.4))
    w = 0.2
    palette = [GREY, PURPLE, TEAL, ORANGE]
    for j, c in enumerate(cols):
        ax.bar([i + (j - 1.5) * w for i in range(len(order))], d[c] / 1000, width=w,
               label=names[c], color=palette[j], edgecolor='white', linewidth=0.5)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order)
    ax.set_ylabel('Schools (thousands)')
    ax.set_xlabel('Exposure tier, identical cutpoints on the 0-100 normalised index')
    ax.legend(frameon=False, fontsize=7, ncol=2, loc='upper center', bbox_to_anchor=(0.5, 1.28))
    fig.savefig(f'{out}/fig_index_variants.png')
    plt.close(fig)


def fig_state_gap(out, D):
    d = pd.read_csv(f'{D}/within_state_gap.csv', index_col=0).sort_values('gap_pts')
    fig, ax = plt.subplots(figsize=(5.6, 7.6))
    cols = [ORANGE if g < 0 else BLUE for g in d.gap_pts]
    ax.barh(range(len(d)), d.gap_pts, color=cols, height=0.72)
    ax.axvline(0, color=INK, lw=0.9)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels(d.index, fontsize=7.5)
    ax.invert_yaxis()
    # States with no within-state variation have a gap of zero by construction;
    # they are kept and labelled rather than silently dropped.
    for i, (st, r) in enumerate(d.iterrows()):
        if r.gap_pts == 0 and r.funded_hi == r.funded_lo:
            note = 'every school funded' if r.funded_hi == 100 else 'no school funded'
            ax.annotate(f'0 ({note})', (0.8, i), va='center', fontsize=6.8, color=GREY)
    ax.set_xlabel('Funded-rate gap, top minus bottom within-state\nexposure quintile (percentage points)')
    ax.annotate('Orange: the state\'s most-exposed\nschools were funded\nless often than its\nleast-exposed schools',
                xy=(0.03, 0.03), xycoords='axes fraction', fontsize=7.5, color=ORANGE, ha='left', va='bottom')
    ax.annotate('Blue: the state\'s most-exposed\nschools were funded\nmore often than its\nleast-exposed schools',
                xy=(0.97, 0.97), xycoords='axes fraction', fontsize=7.5, color=BLUE, ha='right', va='top')
    fig.savefig(f'{out}/fig_state_gap.png')
    plt.close(fig)


def fig_coverage(out, D):
    d = pd.read_csv(f'{D}/coverage_by_state.csv', index_col=0)
    d = d[d.schools >= 100].sort_values('pct_matched').head(24)
    fig, ax = plt.subplots(figsize=(6.0, 5.2))
    cols = [ORANGE if p < 5 else (PURPLE if p < 90 else BLUE) for p in d.pct_matched]
    ax.barh(range(len(d)), d.pct_matched, color=cols, height=0.72)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels(d.index, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 100)
    ax.set_xlabel('Schools linkable to their district\'s ESSER record (%)')
    for i, (st, r) in enumerate(d.iterrows()):
        if pd.notna(r.lea_funded_pct):
            ax.annotate(f'district-level: {r.lea_funded_pct:.0f}% funded',
                        (max(r.pct_matched, 1) + 2, i), va='center', fontsize=6.8, color=GREY)
    fig.savefig(f'{out}/fig_identifier_coverage.png')
    plt.close(fig)


def fig_race(out, D):
    d = pd.read_csv(f'{D}/funded_by_pct_poc_quintile.csv', index_col=0)
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    x = range(len(d))
    ax.bar(x, d.funded_pct, color=TEAL, width=0.6, edgecolor='white')
    ax.errorbar(x, d.funded_pct, yerr=[d.funded_pct - d.ci_lo, d.ci_hi - d.funded_pct],
                fmt='none', ecolor=INK, capsize=3, lw=1)
    for i, r in enumerate(d.itertuples()):
        ax.annotate(f'{r.funded_pct:.1f}', (i, r.funded_pct), textcoords='offset points',
                    xytext=(0, 6), ha='center', fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f'Q{i+1}\n{v:.0f}% POC' for i, v in enumerate(d.mean_poc)], fontsize=7.5)
    ax.set_ylabel('Recorded ventilation\nfunding (%)')
    ax.set_ylim(0, 92)
    ax.set_xlabel('Quintile of county population that is people of color')
    fig.savefig(f'{out}/fig_poc_quintiles.png')
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='output')
    ap.add_argument('--out', default='output/figures')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for fn in (fig_tail, fig_specification, fig_state_gap, fig_coverage, fig_race):
        fn(a.out, a.data)
        print(f'    {fn.__name__}')
    print(f'wrote figures to {a.out}')


if __name__ == '__main__':
    main()
