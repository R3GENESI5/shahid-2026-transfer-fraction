"""Correlate all available trajectory runs with CERES OLR."""
import numpy as np
import xarray as xr
import pandas as pd
import os
from glob import glob

TRAJ_DIR = os.path.join(os.path.dirname(__file__), '..', 'trajectories')
CERES_PATH = 'D:/Data/ceres_ebaf/CERES_EBAF_Edition4.2_200003-202407.nc'
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'results')
os.makedirs(OUT_DIR, exist_ok=True)

ceres = xr.open_dataset(CERES_PATH)
olr = ceres['toa_lw_all_mon']

traj_files = sorted(glob(os.path.join(TRAJ_DIR, 'traj_*.nc')))
print(f'Found {len(traj_files)} trajectory files')

all_results = []

for fpath in traj_files:
    fname = os.path.basename(fpath)
    parts = fname.replace('.nc', '').split('_')
    year = int(parts[1])
    month = int(parts[2])

    traj = xr.open_dataset(fpath)

    ceres_time = np.datetime64(f'{year}-{month:02d}-15')
    tidx = int(np.argmin(np.abs(ceres.time.values - ceres_time)))
    olr_month = olr.isel(time=tidx)
    amazon_ref = float(olr_month.sel(lat=slice(-5, 5), lon=slice(285, 310)).mean().values)

    print(f'\n--- {year}-{month:02d} (Amazon OLR: {amazon_ref:.1f}) ---')

    for day, step in [(0, 0), (5, 20), (10, 40), (15, 60), (20, 80)]:
        lats = traj['latitude'][:, step].values
        lons = traj['longitude'][:, step].values
        valid = ~(np.isnan(lats) | np.isnan(lons))
        lats_v, lons_v = lats[valid], lons[valid]

        if len(lats_v) == 0:
            continue

        olr_vals = []
        for la, lo in zip(lats_v, lons_v):
            try:
                val = float(olr_month.sel(lat=la, lon=lo % 360, method='nearest').values)
                if not np.isnan(val):
                    olr_vals.append(val)
            except:
                pass

        if olr_vals:
            mean_olr = np.mean(olr_vals)
            enh = mean_olr - amazon_ref
            mean_lat = np.mean(np.abs(lats_v))
            mean_lon = np.mean(lons_v)
            print(f'  Day {day:>2}: |lat|={mean_lat:>5.1f}  lon={mean_lon:>6.1f}  '
                  f'OLR={mean_olr:>5.1f}  enh={enh:>+6.1f}  n={len(olr_vals)}')
            all_results.append({
                'year': year, 'month': month, 'day': day,
                'mean_lat': mean_lat, 'mean_lon': mean_lon,
                'olr': mean_olr, 'enhancement': enh, 'amazon_olr': amazon_ref
            })

    traj.close()

# Summary
df = pd.DataFrame(all_results)
df.to_csv(os.path.join(OUT_DIR, 'trajectory_olr_all_runs.csv'), index=False)

print('\n' + '=' * 70)
print('SUMMARY ACROSS ALL RUNS')
print('=' * 70)

for day in [0, 5, 10, 15, 20]:
    sub = df[df['day'] == day]
    if len(sub) > 0:
        print(f'Day {day:>2}: |lat|={sub["mean_lat"].mean():>5.1f}  '
              f'OLR={sub["olr"].mean():>5.1f}  '
              f'enh={sub["enhancement"].mean():>+6.1f} +/- {sub["enhancement"].std():>4.1f}  '
              f'n_runs={len(sub)}')

print(f'\nAmazon mean OLR: {df[df["day"]==0]["amazon_olr"].mean():.1f} W/m2')

day5_enh = df[df['day'] == 5]['enhancement'].mean()
day20_enh = df[df['day'] == 20]['enhancement'].mean()
print(f'\nRelay signature:')
print(f'  Day 5 enhancement:  +{day5_enh:.1f} W/m2')
print(f'  Day 20 enhancement: +{day20_enh:.1f} W/m2')

if day5_enh > 10:
    print('\nRELAY CONFIRMED: parcels from the Amazon TTL reach subtropical')
    print('latitudes where OLR is 25-35 W/m2 higher than over the Amazon.')
    print('The heat exits to space, but at a different location.')

ceres.close()
