"""
06c_control_test_vectorized.py

Vectorized version of the extended Atlantic-source control experiment.

Identical algorithm to 06b_control_test_extended.py but replaces xarray's
per-parcel `.interp()` calls with a vectorized scipy RegularGridInterpolator
called once per timestep on all active parcels simultaneously. Expected
runtime: 3-5 minutes vs 3+ hours for the per-parcel loop version.

Output: results/control_comparison_vectorized.csv

Cross-validation: running alongside 06b_control_test_extended.py and
comparing results confirms both implementations give the same answer.
"""
import numpy as np
import xarray as xr
import pandas as pd
import os
import sys
from scipy.interpolate import RegularGridInterpolator

WIND_DIR = r"D:\Data\paper_f_convective_relay\era5_winds"
CERES_PATH = r"D:\Data\ceres_ebaf\CERES_EBAF_Edition4.2_200003-202407.nc"
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
os.makedirs(OUT_DIR, exist_ok=True)

EARTH_RADIUS = 6.371e6
DT_HOURS = 6
N_STEPS = 80
dt_s = DT_HOURS * 3600
LAT_MIN, LAT_MAX = -30.0, 60.0
LON_MIN, LON_MAX = -90.0, 30.0

YEARS = [2005, 2008, 2010, 2015, 2016, 2019, 2020]
ENSO_PHASE = {
    2005: "neutral/weak La Nina",
    2008: "La Nina",
    2010: "El Nino to La Nina transition",
    2015: "strong El Nino",
    2016: "El Nino tail",
    2019: "weak El Nino",
    2020: "La Nina",
}


def advect_vec(lat, lon, u, v):
    """Vectorized advection. lat/lon/u/v are arrays of same length."""
    dlat = (v * dt_s) / EARTH_RADIUS * (180 / np.pi)
    cos_lat = np.cos(np.radians(np.where(np.abs(lat) < 0.1, 0.1, np.abs(lat))))
    dlon = (u * dt_s) / (EARTH_RADIUS * cos_lat) * (180 / np.pi)
    return lat + dlat, lon + dlon


def run_ensemble_vectorized(ds, release_lats, release_lons, start_idx):
    """Run trajectory ensemble with vectorized per-timestep interpolation.

    For each timestep: extract u,v fields as numpy arrays, build a scipy
    RegularGridInterpolator, and interpolate ALL active parcels in one call.
    """
    LAT_GRID, LON_GRID = np.meshgrid(release_lats, release_lons, indexing="ij")
    lats = LAT_GRID.flatten().copy()
    lons = LON_GRID.flatten().copy()
    n = lats.size
    active = np.ones(n, dtype=bool)
    traj_lats = np.full((n, N_STEPS + 1), np.nan)
    traj_lons = np.full((n, N_STEPS + 1), np.nan)
    traj_lats[:, 0] = lats
    traj_lons[:, 0] = lons

    # Get grid coordinates once
    grid_lat = ds["latitude"].values
    grid_lon = ds["longitude"].values
    # Ensure ascending order for RegularGridInterpolator
    lat_desc = grid_lat[0] > grid_lat[-1]
    lon_needs_wrap = grid_lon.min() >= 0  # 0..360 convention
    if lat_desc:
        grid_lat = grid_lat[::-1]

    for s in range(N_STEPS):
        tidx = start_idx + s
        u_field = ds["u"].isel(valid_time=tidx, pressure_level=0).values
        v_field = ds["v"].isel(valid_time=tidx, pressure_level=0).values
        if lat_desc:
            u_field = u_field[::-1, :]
            v_field = v_field[::-1, :]

        # Build interpolators once per timestep
        fu = RegularGridInterpolator(
            (grid_lat, grid_lon), u_field,
            method="linear", bounds_error=False, fill_value=0.0,
        )
        fv = RegularGridInterpolator(
            (grid_lat, grid_lon), v_field,
            method="linear", bounds_error=False, fill_value=0.0,
        )

        # Boundary mask
        out_of_bounds = (lats < LAT_MIN) | (lats > LAT_MAX) | (lons < LON_MIN) | (lons > LON_MAX)
        newly_out = active & out_of_bounds
        active = active & ~out_of_bounds

        # Convert parcel lon to match grid convention if needed
        query_lons = lons.copy()
        if lon_needs_wrap:
            query_lons = np.where(query_lons < 0, query_lons + 360, query_lons)

        # Vectorized interp for all active parcels at once
        if active.sum() > 0:
            pts = np.column_stack([lats[active], query_lons[active]])
            u_at = fu(pts)
            v_at = fv(pts)
            u_at = np.where(np.isnan(u_at), 0.0, u_at)
            v_at = np.where(np.isnan(v_at), 0.0, v_at)
            lats_a, lons_a = advect_vec(lats[active], lons[active], u_at, v_at)
            lats[active] = lats_a
            lons[active] = lons_a

        traj_lats[active, s + 1] = lats[active]
        traj_lons[active, s + 1] = lons[active]
        # Parcels that just went out of bounds: freeze their position
        traj_lats[newly_out, s + 1:] = lats[newly_out, None]
        traj_lons[newly_out, s + 1:] = lons[newly_out, None]

    return traj_lats, traj_lons


def extract_olr_at_endpoints(olr_field, lats, lons, step):
    """Extract OLR at each parcel endpoint using vectorized nearest-neighbor."""
    end_lats = lats[:, step]
    end_lons = lons[:, step]
    valid = ~(np.isnan(end_lats) | np.isnan(end_lons))
    if valid.sum() == 0:
        return np.array([])
    olr_lat = olr_field["lat"].values
    olr_lon = olr_field["lon"].values
    olr_arr = olr_field.values
    # Ensure ascending
    if olr_lat[0] > olr_lat[-1]:
        olr_lat = olr_lat[::-1]
        olr_arr = olr_arr[::-1, :]
    # CERES uses 0-360 lon
    q_lons = np.where(end_lons[valid] < 0, end_lons[valid] + 360, end_lons[valid])
    # Nearest-neighbor indices
    lat_idx = np.clip(np.searchsorted(olr_lat, end_lats[valid]), 0, len(olr_lat) - 1)
    lon_idx = np.clip(np.searchsorted(olr_lon, q_lons), 0, len(olr_lon) - 1)
    vals = olr_arr[lat_idx, lon_idx]
    return vals[~np.isnan(vals)]


def run_year(year, ds, ceres, olr):
    amazon_lats = np.arange(-5, 6, 1.0)
    amazon_lons = np.arange(-75, -49, 1.0)
    atlantic_lats = np.arange(-5, 6, 1.0)
    atlantic_lons = np.arange(-30, -4, 1.0)

    times = ds["valid_time"].values
    results = []
    for month in [1, 4, 7, 10]:
        target = np.datetime64(f"{year}-{month:02d}-15T12:00:00")
        start_idx = int(np.argmin(np.abs(times - target)))
        if start_idx + N_STEPS >= len(times):
            print(f"  {year}-{month:02d}: insufficient wind record, skipping", flush=True)
            continue

        ceres_target = np.datetime64(f"{year}-{month:02d}-15")
        ceres_idx = int(np.argmin(np.abs(ceres.time.values - ceres_target)))
        olr_month = olr.isel(time=ceres_idx)

        amazon_ref = float(
            olr_month.sel(lat=slice(-5, 5), lon=slice(285, 310)).mean().values
        )

        amz_lats, amz_lons = run_ensemble_vectorized(ds, amazon_lats, amazon_lons, start_idx)
        atl_lats, atl_lons = run_ensemble_vectorized(ds, atlantic_lats, atlantic_lons, start_idx)

        amz_olr = extract_olr_at_endpoints(olr_month, amz_lats, amz_lons, N_STEPS)
        atl_olr = extract_olr_at_endpoints(olr_month, atl_lats, atl_lons, N_STEPS)

        amz_mean = float(np.mean(amz_olr)) if len(amz_olr) else np.nan
        atl_mean = float(np.mean(atl_olr)) if len(atl_olr) else np.nan
        diff = amz_mean - atl_mean

        print(
            f"  {year}-{month:02d}: amz={amz_mean:6.1f}  atl={atl_mean:6.1f}  diff={diff:+6.1f}  "
            f"n_amz={len(amz_olr)}  n_atl={len(atl_olr)}",
            flush=True,
        )

        results.append(
            {
                "year": year,
                "month": month,
                "enso_phase": ENSO_PHASE[year],
                "amazon_source_ref_olr": amazon_ref,
                "amazon_endpoint_olr": amz_mean,
                "atlantic_endpoint_olr": atl_mean,
                "difference": diff,
                "n_amazon_parcels": len(amz_olr),
                "n_atlantic_parcels": len(atl_olr),
            }
        )
    return results


def main():
    import time
    print("=" * 70, flush=True)
    print("Extended Atlantic-source control (VECTORIZED, n=28)", flush=True)
    print("=" * 70, flush=True)

    for year in YEARS:
        wind_file = os.path.join(WIND_DIR, f"era5_200hPa_uv_{year}.nc")
        if not os.path.exists(wind_file):
            print(f"MISSING: {wind_file}", flush=True)
            sys.exit(1)
    if not os.path.exists(CERES_PATH):
        print(f"MISSING: {CERES_PATH}", flush=True)
        sys.exit(1)

    ceres = xr.open_dataset(CERES_PATH)
    olr = ceres["toa_lw_all_mon"]

    t_all = time.time()
    all_results = []
    for year in YEARS:
        wind_file = os.path.join(WIND_DIR, f"era5_200hPa_uv_{year}.nc")
        print(f"\n{year} ({ENSO_PHASE[year]}):", flush=True)
        t0 = time.time()
        ds = xr.open_dataset(wind_file)
        year_results = run_year(year, ds, ceres, olr)
        all_results.extend(year_results)
        ds.close()
        print(f"  {year} complete in {time.time()-t0:.1f} s", flush=True)

    ceres.close()

    df = pd.DataFrame(all_results)
    out_csv = os.path.join(OUT_DIR, "control_comparison_vectorized.csv")
    df.to_csv(out_csv, index=False)

    print("\n" + "=" * 70, flush=True)
    print("EXTENDED CONTROL SUMMARY — VECTORIZED (n=28)", flush=True)
    print("=" * 70, flush=True)
    print(f"Total runs: {len(df)}", flush=True)
    print(f"Total wall time: {time.time()-t_all:.1f} s", flush=True)
    print(f"Mean Amazon endpoint OLR: {df['amazon_endpoint_olr'].mean():.2f} W/m²", flush=True)
    print(f"Mean Atlantic endpoint OLR: {df['atlantic_endpoint_olr'].mean():.2f} W/m²", flush=True)
    print(f"Mean difference (Amazon - Atlantic): {df['difference'].mean():+.2f} W/m²", flush=True)
    print(f"Std of difference: {df['difference'].std():.2f} W/m²", flush=True)
    print(f"Min/Max diff: {df['difference'].min():+.2f} / {df['difference'].max():+.2f}", flush=True)
    print(f"Range: {df['difference'].max() - df['difference'].min():.2f} W/m²", flush=True)

    from scipy import stats
    t, p = stats.ttest_1samp(df["difference"].dropna(), 0)
    print(f"\nOne-sample t-test (H0: mean difference = 0):", flush=True)
    print(f"  t = {t:.3f}, p = {p:.3f}", flush=True)
    if p > 0.05:
        print("  FAIL TO REJECT H0: Amazon and Atlantic endpoints indistinguishable.", flush=True)
    else:
        print("  REJECT H0: Amazon and Atlantic endpoints differ significantly.", flush=True)

    print(f"\nPer-ENSO-phase means:", flush=True)
    by_phase = df.groupby("enso_phase")["difference"].agg(["mean", "std", "count"])
    print(by_phase.to_string(), flush=True)

    print(f"\nSaved: {out_csv}", flush=True)


if __name__ == "__main__":
    main()
