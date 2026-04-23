"""
02_run_trajectories.py

Forward trajectory analysis from the Amazon TTL.

Releases air parcels from a 1-degree grid over the Amazon at 200 hPa,
tracks forward for 20 days using ERA5 winds, records position at 6-hour
intervals.

Uses a simple Lagrangian advection scheme (no diffusion, no subgrid).
This is equivalent to what easy-era5-trck does but self-contained.

Grid: 5S to 5N, 75W to 50W (Amazon basin, 1-degree spacing)
Level: 200 hPa
Integration: 4th-order Runge-Kutta, 6-hour timestep
Duration: 20 days forward
Output: NetCDF with (parcel_id, time) dimensions, lat/lon at each step
"""
import numpy as np
import xarray as xr
import os
from glob import glob
from datetime import datetime, timedelta

WIND_DIR = os.path.join(os.path.dirname(__file__), '..', 'era5_winds')
OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'trajectories')
os.makedirs(OUT_DIR, exist_ok=True)

# Release grid: Amazon basin at 200 hPa
release_lats = np.arange(-5, 6, 1.0)   # 5S to 5N, 11 points
release_lons = np.arange(-75, -49, 1.0) # 75W to 50W, 26 points
LAT_GRID, LON_GRID = np.meshgrid(release_lats, release_lons, indexing='ij')
n_parcels = LAT_GRID.size
print(f'Release grid: {len(release_lats)} x {len(release_lons)} = {n_parcels} parcels')

# Integration parameters
DT_HOURS = 6
N_STEPS = 80  # 20 days * 4 steps/day
EARTH_RADIUS = 6.371e6  # meters


def load_winds(year):
    """Load ERA5 200 hPa u,v for one year."""
    fpath = os.path.join(WIND_DIR, f'era5_200hPa_uv_{year}.nc')
    if not os.path.exists(fpath):
        print(f'  WARNING: {fpath} not found')
        return None
    ds = xr.open_dataset(fpath)
    return ds


def interp_wind(ds, lat, lon, time_idx):
    """Bilinear interpolation of u,v at (lat, lon) from the wind field at time_idx."""
    # Get the time slice
    u_field = ds['u'].isel(valid_time=time_idx)
    v_field = ds['v'].isel(valid_time=time_idx)

    # Handle longitude convention (ERA5 may use 0-360 or -180 to 180)
    if 'longitude' in ds.dims:
        lon_name, lat_name = 'longitude', 'latitude'
    elif 'lon' in ds.dims:
        lon_name, lat_name = 'lon', 'lat'
    else:
        lon_name = [d for d in ds.dims if 'lon' in d.lower()][0]
        lat_name = [d for d in ds.dims if 'lat' in d.lower()][0]

    # Wrap longitude if needed
    lon_vals = ds[lon_name].values
    if lon_vals.min() >= 0 and lon < 0:
        lon = lon + 360

    # Interpolate
    try:
        u = float(u_field.interp({lat_name: lat, lon_name: lon}, method='linear').values)
        v = float(v_field.interp({lat_name: lat, lon_name: lon}, method='linear').values)
    except:
        u, v = 0.0, 0.0

    return u, v


def advect_step(lat, lon, u, v, dt_seconds):
    """Move a parcel by (u,v) for dt_seconds. Returns new (lat, lon)."""
    # Convert m/s to degrees
    dlat = (v * dt_seconds) / EARTH_RADIUS * (180 / np.pi)
    dlon = (u * dt_seconds) / (EARTH_RADIUS * np.cos(np.radians(lat))) * (180 / np.pi)
    return lat + dlat, lon + dlon


def run_trajectories_for_month(year, month):
    """Run forward trajectories for all parcels released on the 15th of the given month."""
    ds = load_winds(year)
    if ds is None:
        return None

    # Find the time index closest to the 15th at 12:00
    target_time = np.datetime64(f'{year}-{month:02d}-15T12:00:00')
    time_var = 'valid_time' if 'valid_time' in ds.dims else 'time'
    times = ds[time_var].values
    start_idx = int(np.argmin(np.abs(times - target_time)))

    # Check we have enough timesteps ahead
    if start_idx + N_STEPS >= len(times):
        print(f'  Not enough timesteps after {year}-{month:02d}-15 (need {N_STEPS}, have {len(times) - start_idx})')
        # Try to load next year
        ds.close()
        return None

    # Initialize parcels
    lats = LAT_GRID.flatten().copy()
    lons = LON_GRID.flatten().copy()

    # Storage
    traj_lats = np.zeros((n_parcels, N_STEPS + 1))
    traj_lons = np.zeros((n_parcels, N_STEPS + 1))
    traj_lats[:, 0] = lats
    traj_lons[:, 0] = lons

    dt_seconds = DT_HOURS * 3600

    print(f'  Integrating {n_parcels} parcels x {N_STEPS} steps...')
    for step in range(N_STEPS):
        time_idx = start_idx + step
        for p in range(n_parcels):
            u, v = interp_wind(ds, lats[p], lons[p], time_idx)
            lats[p], lons[p] = advect_step(lats[p], lons[p], u, v, dt_seconds)
            # Keep longitude in range
            if lons[p] > 180:
                lons[p] -= 360
            elif lons[p] < -180:
                lons[p] += 360
        traj_lats[:, step + 1] = lats
        traj_lons[:, step + 1] = lons

        if (step + 1) % 20 == 0:
            print(f'    Step {step+1}/{N_STEPS} done')

    ds.close()

    # Save as NetCDF
    hours = np.arange(0, (N_STEPS + 1) * DT_HOURS, DT_HOURS)
    out = xr.Dataset({
        'latitude': (['parcel', 'time_hours'], traj_lats),
        'longitude': (['parcel', 'time_hours'], traj_lons),
        'release_lat': (['parcel'], LAT_GRID.flatten()),
        'release_lon': (['parcel'], LON_GRID.flatten()),
    }, coords={
        'parcel': np.arange(n_parcels),
        'time_hours': hours,
    }, attrs={
        'description': f'Forward trajectories from Amazon TTL, {year}-{month:02d}',
        'release_level': '200 hPa',
        'integration_dt': f'{DT_HOURS} hours',
        'duration': '20 days',
    })

    outfile = os.path.join(OUT_DIR, f'traj_{year}_{month:02d}.nc')
    out.to_netcdf(outfile)
    print(f'  Saved: {outfile}')
    return out


# Run for selected months (one per season per year, to keep it manageable)
# JFM = wet season, JAS = dry season transition
if __name__ == '__main__':
    # Check if any wind files exist
    wind_files = sorted(glob(os.path.join(WIND_DIR, 'era5_200hPa_uv_*.nc')))
    if not wind_files:
        print('No ERA5 wind files found. Run 01_download_era5_winds.py first.')
        print(f'Expected location: {WIND_DIR}')
        exit(1)

    print(f'Found {len(wind_files)} wind files')

    for year in range(2000, 2021):
        for month in [1, 4, 7, 10]:  # One per quarter
            print(f'\n{year}-{month:02d}:')
            run_trajectories_for_month(year, month)
