"""
01_download_era5_winds.py

Download ERA5 6-hourly pressure-level winds (u, v) at 200 hPa
for the Amazon region and downstream Hadley transport zone.

Domain: 30S to 60N, 90W to 30E (Amazon to Atlantic to Europe)
Level: 200 hPa (upper troposphere / TTL)
Period: 2000-2020 (matching CERES EBAF)
Temporal: 6-hourly (for trajectory integration)

Downloads one file per year to keep requests manageable.
Total estimated size: ~2-3 GB for 20 years.
"""
import cdsapi
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'era5_winds')
os.makedirs(OUT_DIR, exist_ok=True)

c = cdsapi.Client()

# Download one year at a time
for year in range(2000, 2021):
    outfile = os.path.join(OUT_DIR, f'era5_200hPa_uv_{year}.nc')
    if os.path.exists(outfile):
        print(f'{year}: already exists, skipping')
        continue

    print(f'Downloading {year}...')
    c.retrieve(
        'reanalysis-era5-pressure-levels',
        {
            'product_type': 'reanalysis',
            'variable': [
                'u_component_of_wind',
                'v_component_of_wind',
                'vertical_velocity',
            ],
            'pressure_level': '200',
            'year': str(year),
            'month': [f'{m:02d}' for m in range(1, 13)],
            'day': [f'{d:02d}' for d in range(1, 32)],
            'time': ['00:00', '06:00', '12:00', '18:00'],
            'area': [60, -90, -30, 30],  # N, W, S, E
            'data_format': 'netcdf',
        },
        outfile
    )
    print(f'  Saved: {outfile}')

print('All downloads complete.')
