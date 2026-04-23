"""
06b_control_test_extended.py

Extended Atlantic-source control experiment for the Lagrangian trajectory
analysis. Runs the control matrix for all 7 years that match the main
Amazon-source ensemble (Option A: full n=28 symmetric control).

Years: 2005, 2008, 2010, 2015, 2016, 2019, 2020
Seasons: January, April, July, October (months 1, 4, 7, 10)
Total: 7 x 4 = 28 Atlantic-source runs

ENSO phase labelling (approximate NOAA ONI classification):
  2005 — neutral/weak La Nina (late)
  2008 — La Nina
  2010 — El Nino to La Nina transition
  2015 — strong El Nino
  2016 — El Nino tail to neutral
  2019 — weak El Nino
  2020 — La Nina

Scientific question answered: does the Amazon-source endpoint OLR differ
systematically from an ocean-source endpoint OLR, when both are released
at 200 hPa and advected 20 days forward by the same ERA5 winds?

If systematic: the convective relay is forest-specific.
If indistinguishable: the pathway is shared Hadley infrastructure.

The original n=4 (2010 only) gave mean diff +0.8 W m-2 with no consistent
sign. This extension confirms whether that result holds across ENSO phases
and years.

Output: results/control_comparison_extended.csv
"""
import numpy as np
import xarray as xr
import pandas as pd
import os
import sys

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


def advect(lat, lon, u, v):
    dlat = (v * dt_s) / EARTH_RADIUS * (180 / np.pi)
    cos_lat = np.cos(np.radians(max(abs(lat), 0.1)))
    dlon = (u * dt_s) / (EARTH_RADIUS * cos_lat) * (180 / np.pi)
    return lat + dlat, lon + dlon


def run_ensemble(ds, release_lats, release_lons, start_idx):
    LAT_GRID, LON_GRID = np.meshgrid(release_lats, release_lons, indexing="ij")
    n = LAT_GRID.size
    lats = LAT_GRID.flatten().copy()
    lons = LON_GRID.flatten().copy()
    active = np.ones(n, dtype=bool)
    traj_lats = np.full((n, N_STEPS + 1), np.nan)
    traj_lons = np.full((n, N_STEPS + 1), np.nan)
    traj_lats[:, 0] = lats
    traj_lons[:, 0] = lons

    for s in range(N_STEPS):
        tidx = start_idx + s
        u_field = ds["u"].isel(valid_time=tidx, pressure_level=0)
        v_field = ds["v"].isel(valid_time=tidx, pressure_level=0)
        for p in range(n):
            if not active[p]:
                continue
            if (
                lats[p] < LAT_MIN
                or lats[p] > LAT_MAX
                or lons[p] < LON_MIN
                or lons[p] > LON_MAX
            ):
                active[p] = False
                traj_lats[p, s + 1 :] = lats[p]
                traj_lons[p, s + 1 :] = lons[p]
                continue
            try:
                u = float(
                    u_field.interp(
                        latitude=lats[p], longitude=lons[p], method="linear"
                    ).values
                )
                v = float(
                    v_field.interp(
                        latitude=lats[p], longitude=lons[p], method="linear"
                    ).values
                )
                if np.isnan(u) or np.isnan(v):
                    u, v = 0.0, 0.0
            except Exception:
                u, v = 0.0, 0.0
            lats[p], lons[p] = advect(lats[p], lons[p], u, v)
        traj_lats[active, s + 1] = lats[active]
        traj_lons[active, s + 1] = lons[active]

    return traj_lats, traj_lons


def extract_olr_at_endpoints(olr_field, lats, lons, step):
    end_lats = lats[:, step]
    end_lons = lons[:, step]
    valid = ~(np.isnan(end_lats) | np.isnan(end_lons))
    olr_vals = []
    for la, lo in zip(end_lats[valid], end_lons[valid]):
        try:
            v = float(olr_field.sel(lat=la, lon=lo % 360, method="nearest").values)
            if not np.isnan(v):
                olr_vals.append(v)
        except Exception:
            pass
    return np.array(olr_vals)


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
            print(f"  {year}-{month:02d}: insufficient wind record, skipping")
            continue

        ceres_target = np.datetime64(f"{year}-{month:02d}-15")
        ceres_idx = int(np.argmin(np.abs(ceres.time.values - ceres_target)))
        olr_month = olr.isel(time=ceres_idx)

        amazon_ref = float(
            olr_month.sel(lat=slice(-5, 5), lon=slice(285, 310)).mean().values
        )

        amz_lats, amz_lons = run_ensemble(ds, amazon_lats, amazon_lons, start_idx)
        atl_lats, atl_lons = run_ensemble(ds, atlantic_lats, atlantic_lons, start_idx)

        amz_olr = extract_olr_at_endpoints(olr_month, amz_lats, amz_lons, N_STEPS)
        atl_olr = extract_olr_at_endpoints(olr_month, atl_lats, atl_lons, N_STEPS)

        amz_mean = float(np.mean(amz_olr)) if len(amz_olr) else np.nan
        atl_mean = float(np.mean(atl_olr)) if len(atl_olr) else np.nan
        diff = amz_mean - atl_mean

        print(
            f"  {year}-{month:02d}: amz={amz_mean:6.1f}  atl={atl_mean:6.1f}  diff={diff:+6.1f}  "
            f"n_amz={len(amz_olr)}  n_atl={len(atl_olr)}"
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
    print("=" * 70)
    print("Extended Atlantic-source control (n=28)")
    print("=" * 70)

    # Check files
    for year in YEARS:
        wind_file = os.path.join(WIND_DIR, f"era5_200hPa_uv_{year}.nc")
        if not os.path.exists(wind_file):
            print(f"MISSING: {wind_file}")
            sys.exit(1)
    if not os.path.exists(CERES_PATH):
        print(f"MISSING: {CERES_PATH}")
        sys.exit(1)

    ceres = xr.open_dataset(CERES_PATH)
    olr = ceres["toa_lw_all_mon"]

    all_results = []
    for year in YEARS:
        wind_file = os.path.join(WIND_DIR, f"era5_200hPa_uv_{year}.nc")
        print(f"\n{year} ({ENSO_PHASE[year]}):")
        ds = xr.open_dataset(wind_file)
        year_results = run_year(year, ds, ceres, olr)
        all_results.extend(year_results)
        ds.close()

    ceres.close()

    df = pd.DataFrame(all_results)
    out_csv = os.path.join(OUT_DIR, "control_comparison_extended.csv")
    df.to_csv(out_csv, index=False)

    print("\n" + "=" * 70)
    print("EXTENDED CONTROL SUMMARY (n=28)")
    print("=" * 70)
    print(f"Total runs: {len(df)}")
    print(f"Mean Amazon endpoint OLR: {df['amazon_endpoint_olr'].mean():.2f} W/m²")
    print(f"Mean Atlantic endpoint OLR: {df['atlantic_endpoint_olr'].mean():.2f} W/m²")
    print(f"Mean difference (Amazon - Atlantic): {df['difference'].mean():+.2f} W/m²")
    print(f"Std of difference: {df['difference'].std():.2f} W/m²")
    print(f"Min diff: {df['difference'].min():+.2f}  Max diff: {df['difference'].max():+.2f}")
    print(
        f"Range: {df['difference'].max() - df['difference'].min():.2f} W/m²"
    )

    # t-test: is mean difference significantly different from zero?
    from scipy import stats
    t, p = stats.ttest_1samp(df["difference"].dropna(), 0)
    print(f"\nOne-sample t-test (H0: mean difference = 0):")
    print(f"  t = {t:.3f}, p = {p:.3f}")
    if p > 0.05:
        print(
            "  FAIL TO REJECT H0: Amazon and Atlantic endpoints indistinguishable."
        )
    else:
        print(
            "  REJECT H0: Amazon and Atlantic endpoints differ significantly."
        )

    # Per-ENSO breakdown
    print(f"\nPer-ENSO-phase means:")
    by_phase = df.groupby("enso_phase")["difference"].agg(["mean", "std", "count"])
    print(by_phase.to_string())

    print(f"\nSaved: {out_csv}")


if __name__ == "__main__":
    main()
