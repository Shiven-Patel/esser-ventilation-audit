"""
01_build_exposure.py
--------------------
Build a school-level industrial air-emissions exposure index from EPA TRI.

WHY THIS SCRIPT EXISTS
======================
The original `esser_ej_audit.py` computed exposure directly from
`epa_tri_national.csv`, treating every row of that file as one emitting source.
That file is *chemical-release-form* level: 77,295 rows describing 21,482
facilities in reporting year 2024. A facility that files 218 chemical forms
therefore entered the inverse-distance sum 218 times at identical coordinates.

Two further problems compounded it:

  (a) `NEIGHBOR_K = 50` capped the neighbour query at the 50 nearest points.
      Because the point cloud was chemical forms rather than facilities, that
      cap bound for 77.2% of schools, and the 50 "nearest sources" were often
      all the same one or two facilities. Every other facility within 50 km
      was invisible to the index.

  (b) `IDW_EPSILON = 1e-5` was added to a squared great-circle distance
      expressed in radians. A facility 20 km from a school has d^2 = 9.9e-6,
      i.e. smaller than epsilon, so epsilon dominated the denominator across
      essentially the whole near field. Over the full 0-50 km range the
      contribution ratio collapsed from ~10,000:1 (true inverse square) to
      about 7:1. The index had almost no distance decay left.

The net effect: the published index was a truncated count of nearby chemical
filings, not a plume model, and it ignored released mass entirely.

WHAT THIS SCRIPT DOES INSTEAD
=============================
Aggregate TRI to the facility, sum 2024 fugitive + stack air releases (lbs),
and compute

    E_s = sum_f  m_f / max(d_sf, 100 m)^2        over facilities within 50 km

with k = 500 neighbours so the cap effectively never binds (the median school
has 49 facilities within 50 km; the 99.9th percentile is well under 500).
Distances are great-circle chord distances in radians, converted to km, with a
100 m floor standing in for the fact that a school is not a point and no one
lives inside the fenceline.

The index is then normalised to 0-100 against its own 99th percentile, matching
the original convention so tier cutoffs remain comparable. That normalisation
is relative by construction: a school at "Critical" is in the top percentiles
of US schools, not above any absolute health threshold. The paper says so.

Three comparison variants are written alongside the canonical one so the
sensitivity of every downstream result can be reported:

    E_forms   exact reproduction of the published index (validation target,
              reproduces the shipped EXPOSURE column at r = 1.00000)
    E_fac     facility-level, original epsilon and k=50
    E_isq     facility-level, true inverse square, unweighted
    E_air     facility-level, true inverse square, air-mass weighted  <- CANONICAL

INPUTS   data/raw/epa_tri_national.csv          (EPA TRI Basic Data Files, RY2024)
         data/raw/EDGE_GEOCODE_PUBLICSCH_2425.TXT  (NCES EDGE, pipe-delimited)
OUTPUTS  data/derived/tri_facilities_2024.csv
         data/derived/school_exposure.csv
"""
from __future__ import annotations
import argparse, os, sys
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

EARTH_R_KM = 6371.0
BOUND_KM = 50.0          # search radius, unchanged from the original
K_NEIGHBORS = 500        # raised from 50 so the cap does not bind
FLOOR_KM = 0.1           # 100 m minimum separation
LEGACY_EPS = 1e-5        # the original epsilon, kept only to reproduce the old index
LEGACY_K = 50

# TRI Basic Data File column names (RY2024 layout). Matched by suffix because
# EPA prefixes every header with a section number, e.g. "51. 5.1 - FUGITIVE AIR".
TRI_COLS = {
    "id": "TRIFD", "lat": "LATITUDE", "lon": "LONGITUDE", "state": "ST",
    "fugitive": "FUGITIVE AIR", "stack": "STACK AIR", "total": "TOTAL RELEASES",
}

NCES_COLS = [
    "NCESSCH", "LEAID", "NAME", "OPSTFIPS", "STREET", "CITY", "STATE", "ZIP",
    "STFIP", "CNTY", "NMCNTY", "LOCALE", "LAT", "LON", "CBSA", "NMCBSA",
    "CBSATYPE", "CSA", "NMCSA", "CD", "SLDL", "SLDU", "SCHOOLYEAR",
]


def resolve(colnames, suffix):
    """EPA prefixes headers with section numbers; match on the trailing name."""
    hits = [c for c in colnames if c.strip().upper().endswith(suffix)]
    if not hits:
        raise KeyError(f"no TRI column ending in {suffix!r}; found {list(colnames)[:8]}...")
    return hits[0]


def aggregate_tri(path: str) -> pd.DataFrame:
    """Collapse the chemical-form file to one row per facility.

    Returns facility coordinates, summed air releases (fugitive + stack, lbs),
    summed total releases, and the number of chemical forms filed. That last
    column is what the original index was implicitly weighting by, so it is
    kept for the reproduction variant.
    """
    head = pd.read_csv(path, nrows=0)
    c = {k: resolve(head.columns, v) for k, v in TRI_COLS.items()}
    usecols = list(dict.fromkeys(c.values()))
    df = pd.read_csv(path, usecols=usecols, low_memory=False)
    df = df.rename(columns={v: k for k, v in c.items()})

    for col in ("fugitive", "stack", "total"):
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0).clip(lower=0.0)
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")

    n_rows = len(df)
    fac = (df.groupby("id", as_index=False)
             .agg(lat=("lat", "first"), lon=("lon", "first"), state=("state", "first"),
                  air_lbs=("fugitive", "sum"), total_lbs=("total", "sum"),
                  n_chem_forms=("id", "size")))
    fac["air_lbs"] = fac["air_lbs"] + df.groupby("id")["stack"].sum().values

    bad = fac.lat.isna() | fac.lon.isna() | ~fac.lat.between(-90, 90) | ~fac.lon.between(-180, 180)
    if bad.any():
        print(f"    dropped {int(bad.sum())} facilities with unusable coordinates")
    fac = fac[~bad].reset_index(drop=True)

    print(f"    TRI: {n_rows:,} chemical-release rows -> {len(fac):,} facilities "
          f"(max forms at one facility: {int(fac.n_chem_forms.max())})")
    return fac


def load_schools(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, sep="|", names=NCES_COLS, dtype=str, low_memory=False)
    df["LAT"] = pd.to_numeric(df["LAT"], errors="coerce")
    df["LON"] = pd.to_numeric(df["LON"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["LAT", "LON"])
    # Restrict to the 50 states, DC, Puerto Rico and the US Virgin Islands, which
    # is the footprint EPA TRI covers. This drops 109 schools in American Samoa,
    # Guam and the Northern Mariana Islands. Those three territories have no TRI
    # facilities and appear in no ESSER LEA record, so they contribute nothing to
    # either side of the analysis; they are excluded here rather than silently
    # carried as zero-exposure, zero-coverage rows.
    df = df[df.LAT.between(15, 72) & df.LON.between(-180, -60)]
    dropped = before - len(df.dropna(subset=["LAT", "LON"]))
    df = df.drop_duplicates("NCESSCH").reset_index(drop=True)
    print(f"    NCES: {before:,} rows -> {len(df):,} geolocated unique schools "
          f"({dropped} outside the TRI reporting footprint)")
    return df


def idw(school_rad, source_rad, weights, k, eps=0.0, floor_km=None):
    """Inverse-square accumulation over sources within BOUND_KM.

    Distances come back from cKDTree as chord distances in radians; multiplying
    by EARTH_R_KM gives kilometres to within 0.1% at 50 km, which is far inside
    the precision of the underlying coordinates.

    `eps` reproduces the legacy softening term (added to the squared *radian*
    distance). `floor_km` is the replacement: a physical minimum separation
    applied before squaring. Pass one or the other, not both.
    """
    bound_rad = BOUND_KM / EARTH_R_KM
    tree = cKDTree(source_rad)
    k_eff = min(k, len(source_rad))
    d, idx = tree.query(school_rad, k=k_eff, distance_upper_bound=bound_rad, workers=-1)
    d = np.atleast_2d(d)
    idx = np.atleast_2d(idx)
    in_range = d < bound_rad
    n_in_range = in_range.sum(axis=1)

    if floor_km is not None:
        d_km = np.maximum(d * EARTH_R_KM, floor_km)
        denom = d_km ** 2
    else:
        denom = d ** 2 + eps

    with np.errstate(divide="ignore", invalid="ignore"):
        contrib = np.where(in_range, 1.0 / denom, 0.0)

    if weights is not None:
        padded = np.append(np.asarray(weights, dtype=float), 0.0)
        contrib = contrib * padded[np.clip(idx, 0, len(source_rad))]

    contrib = np.nan_to_num(contrib, nan=0.0, posinf=0.0, neginf=0.0)
    return contrib.sum(axis=1), n_in_range, (n_in_range >= k_eff)


def normalise(x: np.ndarray) -> np.ndarray:
    """Scale to 0-100 against the 99th percentile, clipped. Original convention."""
    finite = x[np.isfinite(x)]
    q99 = np.quantile(finite[finite > 0], 0.99) if (finite > 0).any() else 1.0
    return np.clip(x / q99 * 100.0, 0.0, 100.0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tri", default="data/raw/epa_tri_national.csv")
    ap.add_argument("--schools", default="data/raw/EDGE_GEOCODE_PUBLICSCH_2425.TXT")
    ap.add_argument("--outdir", default="data/derived")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    print("--- 1. LOADING ---")
    fac = aggregate_tri(a.tri)
    sch = load_schools(a.schools)
    fac.to_csv(os.path.join(a.outdir, "tri_facilities_2024.csv"), index=False)

    s_rad = np.deg2rad(sch[["LAT", "LON"]].to_numpy(dtype=float))
    f_rad = np.deg2rad(fac[["lat", "lon"]].to_numpy(dtype=float))
    # The legacy point cloud: one point per chemical form, at the facility's coords.
    forms_rad = f_rad[np.repeat(np.arange(len(fac)), fac.n_chem_forms.to_numpy(dtype=int))]

    print("--- 2. COMPUTING EXPOSURE VARIANTS ---")
    out = sch[["NCESSCH", "LEAID", "NAME", "STATE", "CNTY", "NMCNTY", "CITY", "ZIP",
               "LOCALE", "LAT", "LON", "SCHOOLYEAR"]].copy()

    e_forms, n_forms, cap_forms = idw(s_rad, forms_rad, None, LEGACY_K, eps=LEGACY_EPS)
    print(f"    E_forms (legacy reproduction): k=50 cap binds for {cap_forms.mean()*100:.1f}% of schools")

    e_fac, n_fac, cap_fac = idw(s_rad, f_rad, None, LEGACY_K, eps=LEGACY_EPS)
    print(f"    E_fac   (facility dedup only): k=50 cap binds for {cap_fac.mean()*100:.1f}% of schools")

    e_isq, n_isq, cap_isq = idw(s_rad, f_rad, None, K_NEIGHBORS, floor_km=FLOOR_KM)
    print(f"    E_isq   (true inverse square): k=500 cap binds for {cap_isq.mean()*100:.2f}% of schools; "
          f"median facilities within {BOUND_KM:.0f} km = {int(np.median(n_isq))}")

    e_air, _, _ = idw(s_rad, f_rad, fac.air_lbs.to_numpy(dtype=float), K_NEIGHBORS, floor_km=FLOOR_KM)
    print("    E_air   (air-mass weighted, CANONICAL)")

    out["E_forms"] = normalise(e_forms).round(4)
    out["E_fac"] = normalise(e_fac).round(4)
    out["E_isq"] = normalise(e_isq).round(4)
    out["EXPOSURE"] = normalise(e_air).round(4)          # canonical name for downstream
    out["E_air_raw_lbs_per_km2"] = e_air                  # unnormalised, for the appendix
    out["n_facilities_50km"] = n_isq

    path = os.path.join(a.outdir, "school_exposure.csv")
    out.to_csv(path, index=False)
    print(f"\n    wrote {path}  ({len(out):,} schools)")


if __name__ == "__main__":
    sys.exit(main())
