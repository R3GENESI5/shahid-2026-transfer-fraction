"""
Paper 6 v5 step 01: Extended CERES extraction for JapanFlux2024 sites.

The pace_empirical loader only extracts all-sky TOA/SFC SW and LW, not
clear-sky or CRE. Paper 6 needs the FULL CERES column set including
ceres_toa_cre_net_mean (the eta denominator's CRE counterpart).

This script reads the JF sites table, opens CERES EBAF Edition 4.2,
extracts the full Paper 6 column set per site, and writes
jf_sites_extended_ceres.csv.

Schema mirrors paper_1_alpha_beta/outputs/toa_tables/site_summary_v3_full.csv:
  site_id, latitude, longitude, igbp, bowen_ratio, mean_H, mean_LE,
  biome_group, ceres_sfc_net_sw_mean/std, ceres_sfc_net_lw_mean/std,
  ceres_toa_net_mean/std, ceres_toa_sw_up_mean/std, ceres_toa_lw_up_mean/std,
  ceres_toa_net_clr_mean/std, ceres_toa_sw_clr_mean/std, ceres_toa_lw_clr_mean/std,
  ceres_toa_cre_sw_mean/std, ceres_toa_cre_lw_mean/std, ceres_toa_cre_net_mean/std,
  ceres_sfc_net_rad, ceres_atm_absorption.

ID-Pag and ID-PaD have identical lat/lon (same physical tower, two
processing runs). ID-PaD is dropped; ID-Pag is kept (higher mean_LE
suggests better-quality flux data).
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import xarray as xr

JF_TABLE = Path(
    "D:/Projects/Programme/paper_1_alpha_beta_asiavalidation/outputs/"
    "jf_sites_table.csv"
)
CERES_NC = Path(
    "D:/Projects/Programme/paper_1_alpha_beta/data/raw/ceres/"
    "CERES_EBAF_Edition4.2_200003-202407.nc"
)
OUT = Path(
    "D:/Projects/Programme/paper_6_transfer_fraction/manuscript/v5_rerun/"
    "jf_sites_extended_ceres.csv"
)

# CERES variable map: Paper 6 column name -> NetCDF variable name
CERES_VARS = {
    # All-sky surface
    "ceres_sfc_net_sw": "sfc_net_sw_all_mon",
    "ceres_sfc_net_lw": "sfc_net_lw_all_mon",
    # All-sky TOA
    "ceres_toa_net": "toa_net_all_mon",
    "ceres_toa_sw_up": "toa_sw_all_mon",
    "ceres_toa_lw_up": "toa_lw_all_mon",
    # Clear-sky TOA (using _t_mon = total-region clear-sky)
    "ceres_toa_net_clr": "toa_net_clr_t_mon",
    "ceres_toa_sw_clr": "toa_sw_clr_t_mon",
    "ceres_toa_lw_clr": "toa_lw_clr_t_mon",
    # Cloud radiative effect (TOA)
    "ceres_toa_cre_sw": "toa_cre_sw_mon",
    "ceres_toa_cre_lw": "toa_cre_lw_mon",
    "ceres_toa_cre_net": "toa_cre_net_mon",
}


def extract_one_site(ds: xr.Dataset, lat: float, lon: float,
                     radius_deg: float = 0.5) -> dict:
    """Pull mean/std for each CERES_VARS variable at the nearest grid cell."""
    out: dict = {}
    lon360 = lon % 360
    try:
        site = ds.sel(lat=lat, lon=lon360, method="nearest",
                      tolerance=radius_deg)
    except (KeyError, ValueError):
        return out

    for key, var_name in CERES_VARS.items():
        if var_name not in site.data_vars:
            continue
        vals = site[var_name].values
        vals = vals[np.isfinite(vals)]
        if len(vals) == 0:
            continue
        out[f"{key}_mean"] = float(np.mean(vals))
        out[f"{key}_std"] = float(np.std(vals))

    # Derived: surface net rad = SW + LW
    sw = out.get("ceres_sfc_net_sw_mean", np.nan)
    lw = out.get("ceres_sfc_net_lw_mean", np.nan)
    if np.isfinite(sw) and np.isfinite(lw):
        out["ceres_sfc_net_rad"] = sw + lw

    # Derived: atmospheric absorption = TOA net - SFC net
    toa_net = out.get("ceres_toa_net_mean", np.nan)
    sfc_net = out.get("ceres_sfc_net_rad", np.nan)
    if np.isfinite(toa_net) and np.isfinite(sfc_net):
        out["ceres_atm_absorption"] = toa_net - sfc_net

    return out


def main() -> int:
    print(f"[load] {JF_TABLE}")
    jf = pd.read_csv(JF_TABLE)
    print(f"  rows: {len(jf)}")

    # Rename to Paper 6 schema
    jf = jf.rename(columns={
        "site_code": "site_id",
        "lat": "latitude",
        "lon": "longitude",
        "bowen": "bowen_ratio",
        "biome": "biome_group",
    })

    # ID-Pag vs ID-PaD: identical lat/lon, same tower. Drop ID-PaD.
    before = len(jf)
    is_pad = jf["site_id"] == "ID-PaD"
    if is_pad.any():
        pad = jf[is_pad].iloc[0]
        pag = jf[jf["site_id"] == "ID-Pag"].iloc[0] if (jf["site_id"] == "ID-Pag").any() else None
        if pag is not None and abs(pad["latitude"] - pag["latitude"]) < 1e-3 \
                and abs(pad["longitude"] - pag["longitude"]) < 1e-3:
            jf = jf[~is_pad].reset_index(drop=True)
            print(f"  dropped ID-PaD (duplicate of ID-Pag at same lat/lon)")
    print(f"  rows after dedup: {len(jf)} (was {before})")

    print(f"[load] {CERES_NC}")
    ds = xr.open_dataset(CERES_NC)
    print(f"  variables: {len(ds.data_vars)}")

    records = []
    for _, row in jf.iterrows():
        rec = {
            "site_id": row["site_id"],
            "latitude": float(row["latitude"]),
            "longitude": float(row["longitude"]),
            "igbp": row["igbp"],
            "biome_group": row["biome_group"],
            "bowen_ratio": float(row["bowen_ratio"]),
            "mean_H": float(row["mean_H"]),
            "mean_LE": float(row["mean_LE"]),
            "n_valid_months": int(row.get("n_months", 0)),
            "source": "JapanFlux2024",
        }
        ceres = extract_one_site(ds, row["latitude"], row["longitude"])
        rec.update(ceres)
        records.append(rec)
        cre_net = ceres.get("ceres_toa_cre_net_mean", float("nan"))
        marker = "OK" if np.isfinite(cre_net) else "MISS"
        print(f"  [{marker}] {row['site_id']}: "
              f"LE={rec['mean_LE']:.1f} W/m2, "
              f"CRE_net={cre_net:+.2f} W/m2")

    out_df = pd.DataFrame(records)
    n_cre = out_df["ceres_toa_cre_net_mean"].notna().sum()
    print(f"[ok] CRE_net non-null: {n_cre}/{len(out_df)}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT, index=False)
    print(f"[write] {OUT}")
    print(f"  cols: {len(out_df.columns)}, rows: {len(out_df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
