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
    d = pd.read_csv(f'{D}/funded_by_exposure_percentile_band.csv', index_col=0)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    x = range(len(d))
    err = [d.funded_pct - d.ci_lo, d.ci_hi - d.funded_pct]
    cols = [BLUE] * len(d)
    cols[-1] = ORANGE
    if len(d) > 1:
        cols[-2] = ORANGE
    ax.errorbar(x, d.funded_pct, yerr=err, fmt='o', ms=5, lw=1.2, capsize=3,
                color=INK, ecolor=GREY, zorder=3, linestyle='none')
    ax.scatter(x, d.funded_pct, s=42, c=cols, zorder=4, edgecolor='white', linewidth=0.8)
    ax.plot(x, d.funded_pct, color=GREY, lw=1, zorder=2)
    for i, (lab, r) in enumerate(d.iterrows()):
        ax.annotate(f'{r.funded_pct:.1f}', (i, r.funded_pct), textcoords='offset points',
                    xytext=(0, 11), ha='center', fontsize=8)
        ax.annotate(f'n={int(r.n):,}', (i, r.funded_pct), textcoords='offset points',
                    xytext=(0, -19), ha='center', fontsize=7, color=GREY)
    ax.set_xticks(list(x))
    ax.set_xticklabels(d.index, fontsize=8)
    ax.set_xlabel('Percentile band of modelled industrial air-emissions exposure')
    ax.set_ylabel('Schools with recorded\nventilation funding (%)')
    ax.set_ylim(28, 80)
    fig.savefig(f'{out}/fig1_exposure_tail.png')
    plt.close(fig)


def fig_specification(out, D):
    d = pd.read_csv(f'{D}/tier_counts_by_variant.csv', index_col=0)
    order = ['Negligible', 'Minimal', 'Low', 'Moderate', 'High', 'Critical']
    d = d.loc[order]
    names = {'E_forms': 'Published index\n(chemical forms, k=50)',
             'E_fac': 'Facility dedup only',
             'E_isq': 'True inverse square',
             'E_air': 'Air-mass weighted\n(canonical)'}
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
    ax.legend(frameon=False, fontsize=7.5, ncol=2, loc='upper right')
    fig.savefig(f'{out}/fig2_specification_sensitivity.png')
    plt.close(fig)


def fig_state_gap(out, D):
    d = pd.read_csv(f'{D}/within_state_gap.csv', index_col=0).sort_values('gap_pts')
    d = d[d.funded_hi.ne(d.funded_lo) | d.gap_pts.ne(0)]
    fig, ax = plt.subplots(figsize=(5.4, 7.2))
    cols = [ORANGE if g < 0 else BLUE for g in d.gap_pts]
    ax.barh(range(len(d)), d.gap_pts, color=cols, height=0.72)
    ax.axvline(0, color=INK, lw=0.9)
    ax.set_yticks(range(len(d)))
    ax.set_yticklabels(d.index, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlabel('Funded-rate gap, top minus bottom within-state\nexposure quintile (percentage points)')
    ax.annotate('most-exposed schools\nfunded less', xy=(-30, len(d) - 3), fontsize=7.5,
                color=ORANGE, ha='left')
    fig.savefig(f'{out}/fig3_within_state_gap.png')
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
    fig.savefig(f'{out}/fig4_identifier_coverage.png')
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
    fig.savefig(f'{out}/fig5_race_gradient.png')
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
