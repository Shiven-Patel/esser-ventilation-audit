"""
07_maps.py
----------
Map figures for the manuscript, drawn directly from the analysis dataset.

There is no basemap and no tile layer. The 102,069 school points are dense enough
that they draw the country themselves, which has three advantages over a tiled
web map: the figure depends on no external service, it reproduces byte-for-byte
from the repository alone, and nothing appears on it that is not in the data.
The interactive viewer built by 08_build_viewer.py is the exploratory counterpart
to these figures and carries the same numbers.

Projection is Albers equal-area conic with the standard USGS parameters for the
conterminous United States (29.5N / 45.5N, origin 96W). Equal-area matters here
because the figures invite the reader to compare how much of the country falls
into each category; a Mercator map would inflate the northern states.

Alaska, Hawaii and Puerto Rico are omitted from the national panels rather than
inset. They hold 848 schools between them, none of which is in the top exposure
band, and insetting them would imply a spatial precision the point cloud does
not have at that scale.

INPUTS   data/derived/analysis_dataset.csv
         data/derived/tri_facilities_2024.csv
OUTPUTS  output/figures/fig6_funding_map.png
         output/figures/fig7_top_exposure_map.png
         output/figures/fig8_case_maps.png
"""
from __future__ import annotations
import argparse, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd

INK = '#1a1a1a'
FUNDED = '#0072B2'      # Okabe-Ito blue
UNFUNDED = '#D55E00'    # Okabe-Ito vermillion
MISSING = '#9AA0A6'     # neutral: absence of a record, not a third category
FACILITY = '#444444'

plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'Liberation Serif', 'Nimbus Roman No9 L', 'DejaVu Serif'],
    'font.size': 9, 'axes.titlesize': 9.5, 'axes.labelsize': 8.5,
    'text.color': INK, 'axes.labelcolor': INK,
    'figure.dpi': 300, 'savefig.bbox': 'tight', 'savefig.facecolor': 'white',
})

# Albers equal-area conic, USGS conterminous US parameters.
LAT0, LON0, SP1, SP2 = 37.5, -96.0, 29.5, 45.5


def albers(lat, lon):
    lat, lon = np.deg2rad(lat), np.deg2rad(lon)
    lat0, lon0 = np.deg2rad(LAT0), np.deg2rad(LON0)
    p1, p2 = np.deg2rad(SP1), np.deg2rad(SP2)
    n = 0.5 * (np.sin(p1) + np.sin(p2))
    C = np.cos(p1) ** 2 + 2 * n * np.sin(p1)
    rho = np.sqrt(C - 2 * n * np.sin(lat)) / n
    rho0 = np.sqrt(C - 2 * n * np.sin(lat0)) / n
    theta = n * (lon - lon0)
    return rho * np.sin(theta), rho0 - rho * np.cos(theta)


def conus(df):
    return df[df.LAT.between(24, 50) & df.LON.between(-125, -66)]


def frame(ax):
    ax.set_aspect('equal')
    ax.axis('off')


def fig_funding(out, df):
    """National funding status. The four unlinkable states read as solid neutral
    blocks, which is the identifier finding as a picture."""
    d = conus(df).copy()
    x, y = albers(d.LAT.to_numpy(), d.LON.to_numpy())
    d['x'], d['y'] = x, y

    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    layers = [
        (d[d.HAS_VENT.isna()], MISSING, 'No linkable district record'),
        (d[d.HAS_VENT == 0], UNFUNDED, 'District recorded no ventilation spending'),
        (d[d.HAS_VENT == 1], FUNDED, 'District recorded ventilation spending'),
    ]
    for sub, colour, _ in layers:
        ax.scatter(sub.x, sub.y, s=0.45, c=colour, alpha=0.5, linewidths=0, rasterized=True)
    frame(ax)

    # The neutral grey sits below 3:1 contrast, so the states it covers are named.
    # Direct labels are the relief the palette check requires.
    for st, lat, lon in [('TX', 31.3, -99.6), ('AZ', 34.4, -111.7), ('WA', 47.4, -120.6)]:
        px, py = albers(np.array([lat]), np.array([lon]))
        ax.annotate(st, (px[0], py[0]), fontsize=8, fontweight='bold', color='#3c4043',
                    ha='center', va='center')
    # Connecticut is too small to hold a label at this scale, so it gets a leader.
    cx, cy = albers(np.array([41.6]), np.array([-72.7]))
    ax.annotate('CT', (cx[0], cy[0]), xytext=(28, -26), textcoords='offset points',
                fontsize=8, fontweight='bold', color='#3c4043', ha='left', va='center',
                arrowprops=dict(arrowstyle='-', lw=0.6, color='#9AA0A6',
                                shrinkA=0, shrinkB=2))
    px, py = albers(np.array([35.6]), np.array([-97.5]))
    ax.annotate('OK', (px[0], py[0]), fontsize=8, fontweight='bold', color='#7a3300',
                ha='center', va='center')

    handles = [Line2D([], [], marker='o', ls='none', ms=5, mfc=c, mec='none', label=l)
               for _, c, l in layers]
    ax.legend(handles=handles, loc='lower left', frameon=False, fontsize=7.5,
              handletextpad=0.4, borderpad=0)
    fig.savefig(f'{out}/fig6_funding_map.png')
    plt.close(fig)


def fig_top_exposure(out, df, fac):
    """Where the 81 schools in the top band are, against TRI facilities."""
    d = conus(df).copy()
    x, y = albers(d.LAT.to_numpy(), d.LON.to_numpy())
    d['x'], d['y'] = x, y

    ana = d[d.STATE_LINKABLE & d.HAS_VENT.notna() & d.EXPOSURE.notna()
            & d.median_income.notna() & d.pct_poc.notna()].copy()
    # Rank on the full analytic sample, then restrict to CONUS for drawing, so the
    # threshold is the same one the models use.
    full = df[df.STATE_LINKABLE & df.HAS_VENT.notna() & df.EXPOSURE.notna()
              & df.median_income.notna() & df.pct_poc.notna()]
    cutoff = full.E_air_raw_lbs_per_km2.quantile(0.999)
    top = ana[ana.E_air_raw_lbs_per_km2 >= cutoff]

    f = fac[fac.lat.between(24, 50) & fac.lon.between(-125, -66)].copy()
    fx, fy = albers(f.lat.to_numpy(), f.lon.to_numpy())

    fig, ax = plt.subplots(figsize=(7.0, 4.4))
    ax.scatter(d.x, d.y, s=0.30, c='#d9d9d9', alpha=0.55, linewidths=0, rasterized=True)
    ax.scatter(fx, fy, s=1.1, c='#8a8a8a', alpha=0.30, linewidths=0, rasterized=True)
    funded = top[top.HAS_VENT == 1]
    unfunded = top[top.HAS_VENT == 0]
    ax.scatter(funded.x, funded.y, s=26, c=FUNDED, edgecolor='white', linewidth=0.6, zorder=5)
    ax.scatter(unfunded.x, unfunded.y, s=26, c=UNFUNDED, edgecolor='white', linewidth=0.6,
               zorder=6, marker='D')
    frame(ax)

    handles = [
        Line2D([], [], marker='o', ls='none', ms=2.2, mfc='#d9d9d9', mec='none',
               label='All public schools'),
        Line2D([], [], marker='o', ls='none', ms=2.8, mfc='#8a8a8a', mec='none',
               label='TRI reporting facility, 2024'),
        Line2D([], [], marker='o', ls='none', ms=5, mfc=FUNDED, mec='white',
               label='Top 0.1% exposure, funded'),
        Line2D([], [], marker='D', ls='none', ms=5, mfc=UNFUNDED, mec='white',
               label='Top 0.1% exposure, not funded'),
    ]
    ax.legend(handles=handles, loc='lower left', frameon=False, fontsize=7.5,
              handletextpad=0.4, borderpad=0)
    fig.savefig(f'{out}/fig7_top_exposure_map.png')
    plt.close(fig)


def fig_cases(out, df):
    """Three counties, each in its own square window with a scale bar.

    The counties differ in extent by an order of magnitude, so a shared window is
    not usable: Bronx County would be a smudge. Each panel is instead a square
    centred on its own county, which makes the three axes boxes identical in size
    so the captions line up, and each carries a scale bar so the reader is never
    invited to compare areas across panels.
    """
    cases = [
        ('Bernalillo County, New Mexico', 'NM', 'Bernalillo County'),
        ('Oklahoma County, Oklahoma', 'OK', 'Oklahoma County'),
        ('Bronx County, New York', 'NY', 'Bronx County'),
    ]
    R_KM = 6371.0
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.2))
    for ax, (label, st, cty) in zip(axes, cases):
        c = df[(df.STATE == st) & (df.NMCNTY == cty)].copy()
        cx, cy = albers(c.LAT.to_numpy(), c.LON.to_numpy())
        c['x'], c['y'] = cx, cy
        for sub, colour, z in [(c[c.HAS_VENT.isna()], MISSING, 2),
                               (c[c.HAS_VENT == 0], UNFUNDED, 3),
                               (c[c.HAS_VENT == 1], FUNDED, 4)]:
            ax.scatter(sub.x, sub.y, s=7, c=colour, alpha=0.85, linewidths=0, zorder=z)

        # Square window, so all three axes boxes come out the same size.
        mx, my = (cx.min() + cx.max()) / 2, (cy.min() + cy.max()) / 2
        half = max(cx.max() - cx.min(), cy.max() - cy.min()) / 2 * 1.18
        ax.set_xlim(mx - half, mx + half)
        ax.set_ylim(my - half, my + half)
        frame(ax)

        # Scale bar. Albers units here are radians of Earth radius, so one unit
        # is R_KM kilometres; pick a round length near a fifth of the window.
        span_km = 2 * half * R_KM
        nice = min([1, 2, 5, 10, 20, 50, 100], key=lambda v: abs(v - span_km / 5))
        bar = nice / R_KM
        x0, y0 = mx - half * 0.88, my - half * 0.88
        ax.plot([x0, x0 + bar], [y0, y0], color='#4a4a4a', lw=1.1, solid_capstyle='butt')
        ax.text(x0 + bar / 2, y0 + half * 0.05, f'{nice} km', ha='center', va='bottom',
                fontsize=6.5, color='#4a4a4a')

        n, m = len(c), int(c.HAS_VENT.notna().sum())
        rate = c.HAS_VENT.mean() * 100
        ax.text(0.5, -0.04, label, transform=ax.transAxes, ha='center', va='top',
                fontsize=8, color=INK)
        ax.text(0.5, -0.13, f'{m} of {n} schools linked', transform=ax.transAxes,
                ha='center', va='top', fontsize=7.5, color='#4a4a4a')
        if m:
            ax.text(0.5, -0.21, f'{rate:.1f}% funded among linked schools',
                    transform=ax.transAxes, ha='center', va='top', fontsize=7.5,
                    color='#4a4a4a')
    fig.subplots_adjust(bottom=0.24, top=0.97, wspace=0.08)
    fig.savefig(f'{out}/fig8_case_maps.png')
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='data/derived/analysis_dataset.csv')
    ap.add_argument('--fac', default='data/derived/tri_facilities_2024.csv')
    ap.add_argument('--out', default='output/figures')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    df = pd.read_csv(a.data, low_memory=False, dtype={'NCESSCH': str, 'LEAID': str})
    df['E_air'] = df['EXPOSURE']
    fac = pd.read_csv(a.fac)

    fig_funding(a.out, df); print('    fig6_funding_map')
    fig_top_exposure(a.out, df, fac); print('    fig7_top_exposure_map')
    fig_cases(a.out, df); print('    fig8_case_maps')
    print(f'wrote maps to {a.out}')


if __name__ == '__main__':
    main()
