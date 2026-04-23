"""
06_control_test.py

Control experiment for the trajectory analysis.

Compares air parcels released from two tropical source regions at 200 hPa:
  - Amazon (5S-5N, 75W-50W): forested continental convective source
  - Tropical Atlantic (5S-5N, 30W-5W): open ocean, no forest, no continental convection

Both sets of parcels are advected forward for 20 days using ERA5 winds, then
matched to CERES OLR at endpoint locations. The test answers whether the forest
source produces measurably different endpoint OLR than an ocean source at the
same altitude.

If endpoint OLR differs systematically, the convective relay is forest-specific.
If endpoint OLR is indistinguishable, the pathway is shared Hadley infrastructure.

Output: control_comparison.csv in results/ folder.

Shahid, A.B. (2026). Supplementary materials.
"""
import numpy as np
import xarray as xr
import pandas as pd
import os

WIND_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'era5_winds')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(OUT_DIR, exist_ok=True)

EARTH_RADIUS = 6.371e6
DT_HOURS = 6
N_STEPS = 80
dt_s = DT_HOURS * 3600
LAT_MIN, LAT_MAX = -30.0, 60.0
LON_MIN, LON_MAX = -90.0, 30.0


def advect(lat, lon, u, v):
    dlat = (v * dt_s) / EARTH_RADIUS * (180 / np.pi)
    cos_lat = np.cos(np.radians(max(abs(lat), 0.1)))
    dlon = (u * dt_s) / (EARTH_RADIUS * cos_lat) * (180 / np.pi)
    return lat + dlat, lon + dlon


def run_ensemble(ds, release_lats, release_lons, start_idx):
    LAT_GRID, LON_GRID = np.meshgrid(release_lats, release_lons, indexing='ij')
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
        u_field = ds['u'].isel(valid_time=tidx, pressure_level=0)
        v_field = ds['v'].isel(valid_time=tidx, pressure_level=0)
        for p in range(n):
            if not active[p]:
                continue
            if lats[p] < LAT_MIN or lats[p] > LAT_MAX or lons[p] < LON_MIN or lons[p] > LON_MAX:
                active[p] = False
                traj_lats[p, s+1:] = lats[p]
                traj_lons[p, s+1:] = lons[p]
                continue
            try:
                u = float(u_field.interp(latitude=lats[p], longitude=lons[p], method='linear').values)
                v = float(v_field.interp(latitude=lats[p], longitude=lons[p], method='linear').values)
                if np.isnan(u) or np.isnan(v):
                    u, v = 0.0, 0.0
            except Exception:
                u, v = 0.0, 0.0
            lats[p], lons[p] = advect(lats[p], lons[p], u, v)
        traj_lats[active, s+1] = lats[active]
        traj_lons[active, s+1] = lons[active]

    return traj_lats, traj_lons


def extract_olr_at_endpoints(olr_field, lats, lons, step):
    end_lats = lats[:, step]
    end_lons = lons[:, step]
    valid = ~(np.isnan(end_lats) | np.isnan(end_lons))
    olr_vals = []
    for la, lo in zip(end_lats[valid], end_lons[valid]):
        try:
            v = float(olr_field.sel(lat=la, lon=lo % 360, method='nearest').values)
            if not np.isnan(v):
                olr_vals.append(v)
        except Exception:
            pass
    return np.array(olr_vals)


def main(year=2010, ceres_path=None):
    wind_file = os.path.join(WIND_DIR, f'era5_200hPa_uv_{year}.nc')
    if not os.path.exists(wind_file):
        print(f'Wind file missing: {wind_file}')
        return

    ds = xr.open_dataset(wind_file)
    times = ds['valid_time'].values

    if ceres_path is None:
        ceres_path = 'D:/Data/ceres_ebaf/CERES_EBAF_Edition4.2_200003-202407.nc'
    if not os.path.exists(ceres_path):
        print('CERES file not found; set ceres_path argument')
        return
    ceres = xr.open_dataset(ceres_path)
    olr = ceres['toa_lw_all_mon']

    amazon_lats = np.arange(-5, 6, 1.0)
    amazon_lons = np.arange(-75, -49, 1.0)
    atlantic_lats = np.arange(-5, 6, 1.0)
    atlantic_lons = np.arange(-30, -4, 1.0)

    results = []
    for month in [1, 4, 7, 10]:
        target = np.datetime64(f'{year}-{month:02d}-15T12:00:00')
        start_idx = int(np.argmin(np.abs(times - target)))
        if start_idx + N_STEPS >= len(times):
            continue

        ceres_target = np.datetime64(f'{year}-{month:02d}-15')
        ceres_idx = int(np.argmin(np.abs(ceres.time.values - ceres_target)))
        olr_month = olr.isel(time=ceres_idx)
        amazon_ref = float(olr_month.sel(lat=slice(-5, 5), lon=slice(285, 310)).mean().values)

        amz_lats, amz_lons = run_ensemble(ds, amazon_lats, amazon_lons, start_idx)
        atl_lats, atl_lons = run_ensemble(ds, atlantic_lats, atlantic_lons, start_idx)

        amz_olr = extract_olr_at_endpoints(olr_month, amz_lats, amz_lons, N_STEPS)
        atl_olr = extract_olr_at_endpoints(olr_month, atl_lats, atl_lons, N_STEPS)

        amz_mean = float(np.mean(amz_olr)) if len(amz_olr) else np.nan
        atl_mean = float(np.mean(atl_olr)) if len(atl_olr) else np.nan
        diff = amz_mean - atl_mean

        print(f'{year}-{month:02d}: Amazon OLR day 20 = {amz_mean:.1f}, '
              f'Atlantic OLR day 20 = {atl_mean:.1f}, diff = {diff:+.1f}')

        results.append({
            'year': year, 'month': month,
            'amazon_source_olr': amazon_ref,
            'amazon_endpoint_olr': amz_mean,
            'atlantic_endpoint_olr': atl_mean,
            'difference': diff,
        })

    ds.close()
    ceres.close()

    if results:
        df = pd.DataFrame(results)
        mean_diff = df['difference'].mean()
        df.to_csv(os.path.join(OUT_DIR, 'control_comparison.csv'), index=False)
        print(f'\nMean difference across 4 months: {mean_diff:+.1f} W m-2')


if __name__ == '__main__':
    main(year=2010)
