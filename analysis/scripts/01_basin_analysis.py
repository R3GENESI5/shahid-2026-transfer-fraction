"""
Paper F: Basin-Integrated Transfer Fraction Analysis
=====================================================
"Cloud longwave attenuation limits the radiative transfer efficiency of
forest latent heat: basin-integrated constraints from three tropical basins"

Shahid, A. B. (2026)

This is the single, unified analysis script that produces ALL results
and figures for the paper. Every number in the manuscript is traceable
to a CSV output from this script.

Data requirements:
  - CERES EBAF Edition 4.2 (NetCDF): ~1.9 GB
  - ERA5 monthly means (NetCDF): ~0.8 GB total
    - data_stream-moda_stepType-avgad.nc (precipitation)
    - data_stream-moda_stepType-avgua.nc (CAPE, TCWV, BLH)

Usage:
  python run_analysis.py

Outputs:
  results/
    table1_basin_cre.csv
    table2_amazon_transect.csv
    table3_congo_transect.csv
    table4_sea_transect.csv
    table5_seasonal_amazon_wet.csv
    table6_seasonal_amazon_dry.csv
    table7_deforestation_counterfactual.csv
    table8_cre_lw_vs_cape.csv
    table9_recycling_model.csv
    table10_cloud_top_properties.csv
    summary_key_numbers.json
  figures/
    fig1_cre_lw_vs_cape.png
    fig2_cross_basin_transects.png
    fig3_recycling_model.png
    fig4_seasonal_transect.png
    fig5_deforestation_counterfactual.png
"""

import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
from matplotlib.lines import Line2D
import json
import os
import warnings
warnings.filterwarnings('ignore')

# ── Configuration ──────────────────────────────────────────────────────
# Adjust these paths if your data is elsewhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(os.path.dirname(BASE_DIR))  # paper_f/supplementary-code -> paper_f -> repo root

CERES_PATH = os.path.join(REPO_DIR, "data", "raw", "ceres", "CERES_EBAF_Edition4.2_200003-202407.nc")
ERA5_TP = os.path.join(REPO_DIR, "data", "raw", "era5_extracted", "data_stream-moda_stepType-avgad.nc")
ERA5_CAPE = os.path.join(REPO_DIR, "data", "raw", "era5_extracted", "data_stream-moda_stepType-avgua.nc")

RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# Single-site reference values from Paper E (Shahid, 2026b)
PAPER_E = {
    'site': 'BR-Sa1',
    'LE': 87.1,           # W/m2
    'CRE_SW': -52.3,      # W/m2
    'CRE_LW': 41.1,       # W/m2
    'CRE_net': -11.2,     # W/m2
    'eta_site': 0.129,    # transfer fraction
}

# Published constants
ET_AMAZON_MM_YR = 1200    # mm/yr, published consensus
P_OCEAN_MM_YR = 1100      # mm/yr, Salati: ~50% recycled
LV = 2.5e6               # J/kg, latent heat of vaporisation
SEC_PER_YEAR = 365.25 * 24 * 3600

# ── Region definitions ─────────────────────────────────────────────────
BASINS = {
    'Amazon Basin':      {'lat': (-15, 5),   'lon': (-80, -45)},
    'Congo Basin':       {'lat': (-10, 5),   'lon': (15, 30)},
    'SE Asia (Borneo)':  {'lat': (-5, 5),    'lon': (105, 120)},
}

CONTROLS = {
    'Tropical Atlantic': {'lat': (-15, 5),   'lon': (-40, -15)},
    'Sahara':            {'lat': (15, 30),   'lon': (-10, 30)},
    'Central US (crop)': {'lat': (30, 45),   'lon': (-100, -85)},
}

AMAZON_TRANSECTS = {
    'Coast (50-45W)':    {'lat': (-5, 0), 'lon': (-50, -45)},
    'East (55-50W)':     {'lat': (-5, 0), 'lon': (-55, -50)},
    'Central (60-55W)':  {'lat': (-5, 0), 'lon': (-60, -55)},
    'West (65-60W)':     {'lat': (-5, 0), 'lon': (-65, -60)},
    'Interior (70-65W)': {'lat': (-5, 0), 'lon': (-70, -65)},
    'Andes (75-70W)':    {'lat': (-5, 0), 'lon': (-75, -70)},
}

CONGO_TRANSECTS = {
    'Congo T1 (15-18E)': {'lat': (-3, 2), 'lon': (15, 18)},
    'Congo T2 (18-21E)': {'lat': (-3, 2), 'lon': (18, 21)},
    'Congo T3 (21-24E)': {'lat': (-3, 2), 'lon': (21, 24)},
    'Congo T4 (24-27E)': {'lat': (-3, 2), 'lon': (24, 27)},
    'Congo T5 (27-30E)': {'lat': (-3, 2), 'lon': (27, 30)},
}

SEA_TRANSECTS = {
    'SEA T1 (105-108E)': {'lat': (-3, 2), 'lon': (105, 108)},
    'SEA T2 (108-111E)': {'lat': (-3, 2), 'lon': (108, 111)},
    'SEA T3 (111-114E)': {'lat': (-3, 2), 'lon': (111, 114)},
    'SEA T4 (114-117E)': {'lat': (-3, 2), 'lon': (114, 117)},
    'SEA T5 (117-120E)': {'lat': (-3, 2), 'lon': (117, 120)},
}

# CRE_LW vs CAPE sampling regions (19 points)
CAPE_SAMPLE_REGIONS = {
    'Amazon Coast':     {'lat': (-5, 0),   'lon': (-50, -45)},
    'Amazon East':      {'lat': (-5, 0),   'lon': (-55, -50)},
    'Amazon Central':   {'lat': (-5, 0),   'lon': (-60, -55)},
    'Amazon West':      {'lat': (-5, 0),   'lon': (-65, -60)},
    'Amazon Interior':  {'lat': (-5, 0),   'lon': (-70, -65)},
    'Amazon Andes':     {'lat': (-5, 0),   'lon': (-75, -70)},
    'Congo West':       {'lat': (-3, 2),   'lon': (15, 20)},
    'Congo Central':    {'lat': (-3, 2),   'lon': (20, 25)},
    'Congo East':       {'lat': (-3, 2),   'lon': (25, 30)},
    'Borneo West':      {'lat': (-3, 2),   'lon': (108, 113)},
    'Borneo East':      {'lat': (-3, 2),   'lon': (113, 118)},
    'SE USA':           {'lat': (30, 35),  'lon': (-90, -85)},
    'W Europe':         {'lat': (45, 50),  'lon': (0, 5)},
    'E China':          {'lat': (25, 30),  'lon': (110, 115)},
    'N Africa Sahel':   {'lat': (10, 15),  'lon': (-5, 5)},
    'C Australia':      {'lat': (-25, -20),'lon': (130, 140)},
    'Trop W Atlantic':  {'lat': (-5, 5),   'lon': (-35, -25)},
    'Trop E Pacific':   {'lat': (-5, 5),   'lon': (-120, -110)},
    'Indian Ocean':     {'lat': (-10, 0),  'lon': (70, 80)},
}


# ── Helper functions ───────────────────────────────────────────────────
def ceres_lon_360(lon):
    return lon % 360

def extract_ceres(ds, lat_range, lon_range, months=None):
    lon_min, lon_max = ceres_lon_360(lon_range[0]), ceres_lon_360(lon_range[1])
    if lon_min > lon_max:
        mask = (ds.lon >= lon_min) | (ds.lon <= lon_max)
    else:
        mask = (ds.lon >= lon_min) & (ds.lon <= lon_max)
    region = ds.sel(lat=slice(lat_range[0], lat_range[1])).where(mask, drop=True)
    if months is not None:
        region = region.sel(time=region.time.dt.month.isin(months))
    return region

def extract_era5(ds, lat_range, lon_range, months=None):
    lat_min, lat_max = lat_range
    if ds.latitude[0] > ds.latitude[-1]:
        region = ds.sel(latitude=slice(lat_max, lat_min))
    else:
        region = ds.sel(latitude=slice(lat_min, lat_max))
    region = region.sel(longitude=slice(lon_range[0], lon_range[1]))
    if months is not None:
        region = region.sel(valid_time=region.valid_time.dt.month.isin(months))
    return region

def get_ceres_stats(ds, lat_range, lon_range, months=None):
    """Extract all CERES variables for a region."""
    c = extract_ceres(ds, lat_range, lon_range, months)
    return {
        'CRE_SW': float(c['toa_cre_sw_mon'].mean()),
        'CRE_LW': float(c['toa_cre_lw_mon'].mean()),
        'CRE_net': float(c['toa_cre_net_mon'].mean()),
        'OLR': float(c['toa_lw_all_mon'].mean()),
        'Cloud_frac_pct': float(c['cldarea_total_daynight_mon'].mean()),
        'Cloud_top_temp_K': float(c['cldtemp_total_daynight_mon'].mean()),
        'Cloud_top_press_hPa': float(c['cldpress_total_daynight_mon'].mean()),
    }

def get_era5_stats(ds_tp, ds_cape, lat_range, lon_range, months=None):
    """Extract ERA5 variables for a region."""
    result = {}
    try:
        tp = extract_era5(ds_tp, lat_range, lon_range, months)
        result['Precip_mm_yr'] = float(tp['tp'].mean()) * 1000 * 365.25
    except:
        result['Precip_mm_yr'] = np.nan
    try:
        cape = extract_era5(ds_cape, lat_range, lon_range, months)
        result['CAPE_J_kg'] = float(cape['cape'].mean())
        result['TCWV_kg_m2'] = float(cape['tcwv'].mean())
    except:
        result['CAPE_J_kg'] = np.nan
        result['TCWV_kg_m2'] = np.nan
    return result


# ══════════════════════════════════════════════════════════════════════
# LOAD DATA
# ══════════════════════════════════════════════════════════════════════
print("="*70)
print("Paper F Analysis: Basin-Integrated Transfer Fraction")
print("="*70)

print("\nLoading CERES EBAF...")
ceres = xr.open_dataset(CERES_PATH)
print(f"  Time range: {str(ceres.time.values[0])[:10]} to {str(ceres.time.values[-1])[:10]}")
print(f"  Grid: {len(ceres.lat)}x{len(ceres.lon)} ({float(ceres.lat[1]-ceres.lat[0]):.1f} deg)")

print("Loading ERA5 precipitation...")
era5_tp = xr.open_dataset(ERA5_TP)

print("Loading ERA5 CAPE/TCWV/BLH...")
era5_cape = xr.open_dataset(ERA5_CAPE)
print(f"  Time range: {len(era5_tp.valid_time)} months")


# ══════════════════════════════════════════════════════════════════════
# TABLE 1: Basin-level CRE
# ══════════════════════════════════════════════════════════════════════
print("\n" + "-"*70)
print("TABLE 1: Basin-level CRE across regions")
print("-"*70)

all_regions = {**BASINS, **CONTROLS}
rows = []
for name, coords in all_regions.items():
    r = get_ceres_stats(ceres, coords['lat'], coords['lon'])
    r['Region'] = name
    rows.append(r)

df1 = pd.DataFrame(rows)
df1 = df1[['Region', 'CRE_SW', 'CRE_LW', 'CRE_net', 'Cloud_frac_pct', 'OLR',
            'Cloud_top_temp_K', 'Cloud_top_press_hPa']]
df1.to_csv(os.path.join(RESULTS_DIR, "table1_basin_cre.csv"), index=False, float_format='%.1f')
print(df1.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# TABLE 2-4: Transects (Amazon, Congo, SE Asia)
# ══════════════════════════════════════════════════════════════════════
for table_num, basin_name, transects in [
    (2, "Amazon", AMAZON_TRANSECTS),
    (3, "Congo", CONGO_TRANSECTS),
    (4, "SE Asia", SEA_TRANSECTS),
]:
    print(f"\n{'-'*70}")
    print(f"TABLE {table_num}: {basin_name} transect")
    print(f"{'-'*70}")

    rows = []
    for name, coords in transects.items():
        r = get_ceres_stats(ceres, coords['lat'], coords['lon'])
        r.update(get_era5_stats(era5_tp, era5_cape, coords['lat'], coords['lon']))
        r['Transect'] = name
        rows.append(r)

    df = pd.DataFrame(rows)
    df = df[['Transect', 'CRE_SW', 'CRE_LW', 'CRE_net', 'Cloud_frac_pct',
             'Precip_mm_yr', 'CAPE_J_kg', 'TCWV_kg_m2']]
    fname = f"table{table_num}_{basin_name.lower().replace(' ', '_')}_transect.csv"
    df.to_csv(os.path.join(RESULTS_DIR, fname), index=False, float_format='%.1f')
    print(df.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# TABLE 5-6: Seasonal Amazon transect
# ══════════════════════════════════════════════════════════════════════
for table_num, season_name, months in [
    (5, "wet", [12, 1, 2, 3, 4, 5]),
    (6, "dry", [6, 7, 8, 9, 10, 11]),
]:
    print(f"\n{'-'*70}")
    print(f"TABLE {table_num}: Amazon transect ({season_name} season)")
    print(f"{'-'*70}")

    rows = []
    for name, coords in AMAZON_TRANSECTS.items():
        r = get_ceres_stats(ceres, coords['lat'], coords['lon'], months=months)
        r['Transect'] = name
        r['Season'] = season_name
        rows.append(r)

    df = pd.DataFrame(rows)
    df = df[['Transect', 'Season', 'CRE_SW', 'CRE_LW', 'CRE_net', 'Cloud_frac_pct']]
    df.to_csv(os.path.join(RESULTS_DIR, f"table{table_num}_seasonal_amazon_{season_name}.csv"),
              index=False, float_format='%.1f')
    print(df.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# TABLE 7: Deforestation counterfactual
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'-'*70}")
print("TABLE 7: Deforestation counterfactual")
print(f"{'-'*70}")

rows = []
for lon_range, label in [((-60, -55), '60-55W'), ((-55, -50), '55-50W'), ((-50, -45), '50-45W')]:
    intact = get_ceres_stats(ceres, (-3, 2), lon_range)
    intact.update(get_era5_stats(era5_tp, era5_cape, (-3, 2), lon_range))
    arc = get_ceres_stats(ceres, (-12, -7), lon_range)
    arc.update(get_era5_stats(era5_tp, era5_cape, (-12, -7), lon_range))

    rows.append({
        'Longitude': label,
        'Intact_CRE_SW': intact['CRE_SW'],
        'Intact_CRE_LW': intact['CRE_LW'],
        'Intact_CRE_net': intact['CRE_net'],
        'Intact_Cloud_pct': intact['Cloud_frac_pct'],
        'Arc_CRE_SW': arc['CRE_SW'],
        'Arc_CRE_LW': arc['CRE_LW'],
        'Arc_CRE_net': arc['CRE_net'],
        'Arc_Cloud_pct': arc['Cloud_frac_pct'],
        'Delta_CRE_SW': intact['CRE_SW'] - arc['CRE_SW'],
        'Delta_CRE_LW': intact['CRE_LW'] - arc['CRE_LW'],
        'Delta_CRE_net': intact['CRE_net'] - arc['CRE_net'],
        'Delta_Cloud_pct': intact['Cloud_frac_pct'] - arc['Cloud_frac_pct'],
    })

df7 = pd.DataFrame(rows)
df7.to_csv(os.path.join(RESULTS_DIR, "table7_deforestation_counterfactual.csv"),
           index=False, float_format='%.1f')
print(df7.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# TABLE 8: CRE_LW vs CAPE (19 regions)
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'-'*70}")
print("TABLE 8: CRE_LW vs CAPE across 19 regions")
print(f"{'-'*70}")

rows = []
for name, coords in CAPE_SAMPLE_REGIONS.items():
    r = get_ceres_stats(ceres, coords['lat'], coords['lon'])
    r.update(get_era5_stats(era5_tp, era5_cape, coords['lat'], coords['lon']))
    r['Region'] = name
    # Classify region type
    if any(x in name for x in ['Amazon', 'Congo', 'Borneo']):
        r['Type'] = 'Tropical forest'
    elif any(x in name for x in ['Atlantic', 'Pacific', 'Indian']):
        r['Type'] = 'Ocean'
    elif any(x in name for x in ['Sahel', 'Australia']):
        r['Type'] = 'Subtropical'
    else:
        r['Type'] = 'Temperate'
    rows.append(r)

df8 = pd.DataFrame(rows)
df8 = df8[['Region', 'Type', 'CAPE_J_kg', 'CRE_LW', 'CRE_SW', 'CRE_net',
           'Cloud_frac_pct', 'Cloud_top_temp_K']]
df8.to_csv(os.path.join(RESULTS_DIR, "table8_cre_lw_vs_cape.csv"),
           index=False, float_format='%.1f')
print(df8.to_string(index=False))

# Regressions
cape_arr = df8['CAPE_J_kg'].values
cre_lw_arr = df8['CRE_LW'].values
cre_sw_arr = df8['CRE_SW'].values
cre_net_arr = df8['CRE_net'].values

reg_lw = stats.linregress(cape_arr, cre_lw_arr)
reg_sw = stats.linregress(cape_arr, cre_sw_arr)
reg_net = stats.linregress(cape_arr, cre_net_arr)

print(f"\nRegressions:")
print(f"  CRE_LW = {reg_lw.intercept:.1f} + {reg_lw.slope:.4f} * CAPE  (R2={reg_lw.rvalue**2:.3f}, p={reg_lw.pvalue:.2e})")
print(f"  CRE_SW = {reg_sw.intercept:.1f} + {reg_sw.slope:.4f} * CAPE  (R2={reg_sw.rvalue**2:.3f}, p={reg_sw.pvalue:.2e})")
print(f"  CRE_net = {reg_net.intercept:.1f} + {reg_net.slope:.4f} * CAPE  (R2={reg_net.rvalue**2:.3f}, p={reg_net.pvalue:.2e})")


# ══════════════════════════════════════════════════════════════════════
# TABLE 9: Recycling model
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'-'*70}")
print("TABLE 9: Recycling amplification model")
print(f"{'-'*70}")

eta_site = PAPER_E['eta_site']
LE_site = PAPER_E['LE']

# Basin empirical values
LE_basin = ET_AMAZON_MM_YR * LV / SEC_PER_YEAR
amazon_cre_net = df1.loc[df1['Region'] == 'Amazon Basin', 'CRE_net'].values[0]
eta_basin_empirical = abs(amazon_cre_net) / LE_basin

LE_ocean = P_OCEAN_MM_YR * LV / SEC_PER_YEAR
eta_per_oceanic = abs(amazon_cre_net) / LE_ocean

rows = []
for f_label, f_val in [("Eltahir & Bras 1994", 0.25),
                         ("Van der Ent 2010", 0.35),
                         ("Zemp et al. 2014", 0.40),
                         ("Salati & Vose 1984", 0.50)]:
    eta_model = eta_site / (1 - f_val)
    rows.append({
        'Source': f_label,
        'Recycling_fraction_f': f_val,
        'Multiplier': 1 / (1 - f_val),
        'Model_eta_basin': eta_model,
        'Model_eta_basin_pct': eta_model * 100,
    })

# Add empirical
rows.append({
    'Source': 'Empirical (this study)',
    'Recycling_fraction_f': 1 - (eta_site / eta_basin_empirical),
    'Multiplier': eta_basin_empirical / eta_site,
    'Model_eta_basin': eta_basin_empirical,
    'Model_eta_basin_pct': eta_basin_empirical * 100,
})

df9 = pd.DataFrame(rows)
df9.to_csv(os.path.join(RESULTS_DIR, "table9_recycling_model.csv"),
           index=False, float_format='%.3f')
print(df9.to_string(index=False))

print(f"\n  Single-site eta: {eta_site:.3f} ({eta_site*100:.1f}%)")
print(f"  Basin empirical eta: {eta_basin_empirical:.3f} ({eta_basin_empirical*100:.1f}%)")
print(f"  Recycling amplification: {eta_basin_empirical/eta_site:.2f}x")
print(f"  Per-oceanic-input eta: {eta_per_oceanic:.3f} ({eta_per_oceanic*100:.1f}%)")


# ══════════════════════════════════════════════════════════════════════
# TABLE 10: Cloud top properties
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'-'*70}")
print("TABLE 10: Cloud top properties")
print(f"{'-'*70}")

sigma = 5.67e-8
cloud_regions = {
    'Amazon': {'lat': (-5, 0), 'lon': (-60, -50)},
    'Congo': {'lat': (-3, 2), 'lon': (20, 28)},
    'Temperate Europe': {'lat': (45, 52), 'lon': (0, 10)},
    'Sahara': {'lat': (20, 28), 'lon': (0, 20)},
    'Trop Atlantic': {'lat': (-5, 5), 'lon': (-35, -25)},
}

rows = []
for name, coords in cloud_regions.items():
    r = get_ceres_stats(ceres, coords['lat'], coords['lon'])
    r['Region'] = name
    r['SB_emission_W_m2'] = sigma * (r['Cloud_top_temp_K'] ** 4)
    r['Cloud_top_temp_C'] = r['Cloud_top_temp_K'] - 273.15
    rows.append(r)

df10 = pd.DataFrame(rows)
df10 = df10[['Region', 'Cloud_top_temp_K', 'Cloud_top_temp_C', 'Cloud_top_press_hPa',
             'SB_emission_W_m2', 'CRE_LW', 'CRE_SW', 'CRE_net', 'OLR']]
df10.to_csv(os.path.join(RESULTS_DIR, "table10_cloud_top_properties.csv"),
            index=False, float_format='%.1f')
print(df10.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════
# SUMMARY: Key numbers (JSON)
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print("KEY NUMBERS SUMMARY")
print(f"{'='*70}")

key_numbers = {
    'paper_e_reference': PAPER_E,
    'basin_level': {
        'Amazon_CRE_net': float(amazon_cre_net),
        'Amazon_LE_W_m2': float(LE_basin),
        'Amazon_ET_mm_yr': ET_AMAZON_MM_YR,
        'eta_basin': float(eta_basin_empirical),
        'eta_basin_pct': round(float(eta_basin_empirical * 100), 1),
        'recycling_amplification': round(float(eta_basin_empirical / eta_site), 2),
    },
    'per_oceanic_input': {
        'LE_ocean_W_m2': float(LE_ocean),
        'P_ocean_mm_yr': P_OCEAN_MM_YR,
        'eta_per_oceanic': round(float(eta_per_oceanic), 3),
        'eta_per_oceanic_pct': round(float(eta_per_oceanic * 100), 1),
    },
    'attenuation_mechanism': {
        'CRE_LW_vs_CAPE_slope': round(float(reg_lw.slope), 4),
        'CRE_LW_vs_CAPE_R2': round(float(reg_lw.rvalue**2), 3),
        'CRE_LW_vs_CAPE_p': float(reg_lw.pvalue),
        'CRE_SW_vs_CAPE_slope': round(float(reg_sw.slope), 4),
        'CRE_SW_vs_CAPE_R2': round(float(reg_sw.rvalue**2), 3),
        'CRE_net_vs_CAPE_slope': round(float(reg_net.slope), 4),
        'CRE_net_vs_CAPE_R2': round(float(reg_net.rvalue**2), 3),
        'LW_SW_ratio_at_CAPE_200': round(
            (reg_lw.intercept + reg_lw.slope*200) / abs(reg_sw.intercept + reg_sw.slope*200), 2),
        'LW_SW_ratio_at_CAPE_1000': round(
            (reg_lw.intercept + reg_lw.slope*1000) / abs(reg_sw.intercept + reg_sw.slope*1000), 2),
    },
    'transect_gradient': {
        'Amazon_coast_CRE_SW': float(df8.loc[df8['Region']=='Amazon Coast', 'CRE_SW'].values[0]),
        'Amazon_interior_CRE_SW': float(df8.loc[df8['Region']=='Amazon Interior', 'CRE_SW'].values[0]),
        'Amazon_coast_CRE_LW': float(df8.loc[df8['Region']=='Amazon Coast', 'CRE_LW'].values[0]),
        'Amazon_interior_CRE_LW': float(df8.loc[df8['Region']=='Amazon Interior', 'CRE_LW'].values[0]),
        'Amazon_coast_cloud_pct': float(
            df8.loc[df8['Region']=='Amazon Coast', 'Cloud_frac_pct'].values[0]),
        'Amazon_interior_cloud_pct': float(
            df8.loc[df8['Region']=='Amazon Interior', 'Cloud_frac_pct'].values[0]),
    },
    'deforestation_counterfactual': {
        'mean_delta_CRE_net': round(float(df7['Delta_CRE_net'].mean()), 1),
        'range_delta_CRE_net': [round(float(df7['Delta_CRE_net'].min()), 1),
                                 round(float(df7['Delta_CRE_net'].max()), 1)],
        'mean_delta_cloud_pct': round(float(df7['Delta_Cloud_pct'].mean()), 1),
    },
    'financial': {
        'single_site_USD_ha_yr': 86,
        'recycling_corrected_USD_ha_yr': round(86 * float(eta_basin_empirical / eta_site)),
        'uncorrected_USD_ha_yr': 402,
        'carbon_market_range': [5, 50],
        'baker_rainfall_USD_ha_yr': 59,
    },
    'f_required_for_75pct': round(1 - (eta_site / 0.75), 2),
}

with open(os.path.join(RESULTS_DIR, "summary_key_numbers.json"), 'w') as f:
    json.dump(key_numbers, f, indent=2)

for section, vals in key_numbers.items():
    print(f"\n  {section}:")
    if isinstance(vals, dict):
        for k, v in vals.items():
            print(f"    {k}: {v}")


# ══════════════════════════════════════════════════════════════════════
# FIGURES
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print("GENERATING FIGURES")
print(f"{'='*70}")

# ── Figure 1: CRE_LW vs CAPE ─────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
fig.suptitle('The Attenuation Mechanism: Deeper Convection Traps More Longwave',
             fontsize=14, fontweight='bold')

colors = []
for _, row in df8.iterrows():
    c = {'Tropical forest': 'darkgreen', 'Ocean': 'steelblue',
         'Subtropical': 'orange', 'Temperate': 'gray'}
    colors.append(c.get(row['Type'], 'gray'))

x_fit = np.linspace(0, 1500, 100)

for ax, y_arr, reg, ylabel, title, color in [
    (axes[0], cre_lw_arr, reg_lw, 'CRE_LW (W/m\u00b2)', 'CRE_LW increases with CAPE', 'r'),
    (axes[1], cre_sw_arr, reg_sw, 'CRE_SW (W/m\u00b2)', 'CRE_SW also increases with CAPE', 'b'),
    (axes[2], cre_net_arr, reg_net, 'CRE_net (W/m\u00b2)', 'CRE_net is ATTENUATED', 'g'),
]:
    ax.scatter(cape_arr, y_arr, c=colors, s=80, zorder=5, edgecolors='k', linewidths=0.5)
    ax.plot(x_fit, reg.intercept + reg.slope * x_fit, f'{color}-', linewidth=2,
            label=f'slope={reg.slope:.3f}, R\u00b2={reg.rvalue**2:.2f}')
    ax.set_xlabel('CAPE (J/kg)', fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    if 'net' in ylabel.lower():
        ax.axhline(0, color='gray', linewidth=0.5)

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor='darkgreen', markersize=10, label='Tropical forest'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='steelblue', markersize=10, label='Ocean'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', markersize=10, label='Subtropical'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor='gray', markersize=10, label='Temperate')]
axes[2].legend(handles=legend_elements, loc='lower left', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "fig1_cre_lw_vs_cape.png"), dpi=300, bbox_inches='tight')
plt.close()
print("  Saved fig1_cre_lw_vs_cape.png")

# ── Figure 2: Cross-basin transects ───────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(12, 12), sharex=False)
fig.suptitle('Cross-Basin Transects: CRE Components Coast to Interior',
             fontsize=14, fontweight='bold')

for ax_idx, (basin_name, transects) in enumerate([
    ("Amazon", AMAZON_TRANSECTS),
    ("Congo", CONGO_TRANSECTS),
    ("SE Asia", SEA_TRANSECTS)
]):
    ax = axes[ax_idx]
    names = list(transects.keys())
    x = range(len(names))
    sw, lw, net = [], [], []
    for name, coords in transects.items():
        c = get_ceres_stats(ceres, coords['lat'], coords['lon'])
        sw.append(c['CRE_SW']); lw.append(c['CRE_LW']); net.append(c['CRE_net'])
    ax.bar(x, sw, color='steelblue', alpha=0.7, label='CRE_SW (cooling)')
    ax.bar(x, lw, color='coral', alpha=0.7, label='CRE_LW (warming)')
    ax.plot(x, net, 'ko-', linewidth=2.5, markersize=8, label='CRE_net', zorder=5)
    ax.axhline(0, color='gray', linewidth=0.5)
    ax.set_ylabel('W/m\u00b2')
    ax.set_title(basin_name, fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([n.split('(')[0].strip() if '(' in n else n for n in names],
                       rotation=30, ha='right', fontsize=9)
    ax.legend(fontsize=9)
    ax.set_ylim(-90, 70)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "fig2_cross_basin_transects.png"), dpi=300, bbox_inches='tight')
plt.close()
print("  Saved fig2_cross_basin_transects.png")

# ── Figure 3: Recycling model ────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
f_range = np.linspace(0, 0.65, 100)
eta_range = eta_site / (1 - f_range)

ax = axes[0]
ax.plot(f_range * 100, eta_range * 100, 'k-', linewidth=2.5)
ax.axhline(eta_site * 100, color='steelblue', linestyle='--', linewidth=1.5,
           label=f'Single-site: {eta_site*100:.1f}%')
ax.axhline(75, color='red', linestyle='--', linewidth=1.5, label='Bunyard et al.: 75%')
ax.axhline(eta_basin_empirical * 100, color='darkgreen', linestyle='-', linewidth=1.5,
           label=f'Basin empirical: {eta_basin_empirical*100:.1f}%')
for f_val, label, color in [(0.25, 'Eltahir &\nBras', 'green'),
                              (0.35, 'Van der\nEnt', 'teal'),
                              (0.50, 'Salati', 'purple')]:
    ax.plot(f_val*100, (eta_site/(1-f_val))*100, 'o', color=color, markersize=10, zorder=5)
    ax.annotate(f'{label}\n{eta_site/(1-f_val)*100:.1f}%', (f_val*100, (eta_site/(1-f_val))*100),
                textcoords="offset points", xytext=(12, -5), fontsize=9, color=color)
ax.set_xlabel('Recycling fraction f (%)', fontsize=12)
ax.set_ylabel('Basin-level transfer fraction (%)', fontsize=12)
ax.set_title('Recycling Amplification of Transfer Fraction', fontsize=13, fontweight='bold')
ax.legend(fontsize=10, loc='upper left')
ax.set_xlim(0, 65); ax.set_ylim(0, 50)
ax.grid(True, alpha=0.3)

ax = axes[1]
region_names = list(all_regions.keys())
cre_net_abs = [abs(df1.loc[df1['Region']==n, 'CRE_net'].values[0]) for n in region_names]
cre_sw_abs = [abs(df1.loc[df1['Region']==n, 'CRE_SW'].values[0]) for n in region_names]
y_pos = range(len(region_names))
ax.barh(y_pos, cre_sw_abs, color='steelblue', alpha=0.4, label='|CRE_SW| (cloud albedo)')
ax.barh(y_pos, cre_net_abs, color='darkgreen', alpha=0.8, label='|CRE_net| (net cooling)')
ax.set_yticks(y_pos); ax.set_yticklabels(region_names, fontsize=10)
ax.set_xlabel('W/m\u00b2', fontsize=12)
ax.set_title('CRE by Region: Albedo vs Net', fontsize=13, fontweight='bold')
ax.legend(fontsize=10); ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "fig3_recycling_model.png"), dpi=300, bbox_inches='tight')
plt.close()
print("  Saved fig3_recycling_model.png")

# ── Figure 4: Seasonal transect ───────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Amazon Transect: Wet Season vs Dry Season', fontsize=14, fontweight='bold')
for ax_idx, (season_name, months) in enumerate([
    ("Wet (DJF-MAM)", [12, 1, 2, 3, 4, 5]),
    ("Dry (JJA-SON)", [6, 7, 8, 9, 10, 11])
]):
    ax = axes[ax_idx]
    names = list(AMAZON_TRANSECTS.keys())
    x = range(len(names))
    sw, lw, net = [], [], []
    for name, coords in AMAZON_TRANSECTS.items():
        c = get_ceres_stats(ceres, coords['lat'], coords['lon'], months=months)
        sw.append(c['CRE_SW']); lw.append(c['CRE_LW']); net.append(c['CRE_net'])
    ax.bar(x, sw, color='steelblue', alpha=0.7, label='CRE_SW')
    ax.bar(x, lw, color='coral', alpha=0.7, label='CRE_LW')
    ax.plot(x, net, 'ko-', linewidth=2.5, markersize=8, label='CRE_net', zorder=5)
    ax.axhline(0, color='gray', linewidth=0.5)
    ax.set_ylabel('W/m\u00b2'); ax.set_title(season_name, fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([n.split('(')[0].strip() for n in names], rotation=30, ha='right', fontsize=9)
    ax.legend(fontsize=9); ax.set_ylim(-100, 80)
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "fig4_seasonal_transect.png"), dpi=300, bbox_inches='tight')
plt.close()
print("  Saved fig4_seasonal_transect.png")

# ── Figure 5: Deforestation counterfactual ────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle('Intact Forest vs Arc of Deforestation (same longitudes)', fontsize=14, fontweight='bold')
lon_labels = df7['Longitude'].tolist()
x = range(len(lon_labels))
w = 0.35

ax = axes[0]
ax.bar([i-w/2 for i in x], df7['Intact_CRE_SW'], w, color='darkgreen', alpha=0.7, label='Intact CRE_SW')
ax.bar([i+w/2 for i in x], df7['Arc_CRE_SW'], w, color='brown', alpha=0.7, label='Arc CRE_SW')
ax.bar([i-w/2 for i in x], df7['Intact_CRE_LW'], w, color='darkgreen', alpha=0.3)
ax.bar([i+w/2 for i in x], df7['Arc_CRE_LW'], w, color='brown', alpha=0.3)
ax.set_ylabel('W/m\u00b2'); ax.set_title('CRE Components', fontsize=12)
ax.set_xticks(x); ax.set_xticklabels(lon_labels); ax.legend(); ax.axhline(0, color='gray', linewidth=0.5)

ax = axes[1]
ax.bar([i-w/2 for i in x], df7['Intact_CRE_net'], w, color='darkgreen', alpha=0.8, label='Intact CRE_net')
ax.bar([i+w/2 for i in x], df7['Arc_CRE_net'], w, color='brown', alpha=0.8, label='Arc CRE_net')
ax.set_ylabel('W/m\u00b2'); ax.set_title('Net Cloud Radiative Effect', fontsize=12)
ax.set_xticks(x); ax.set_xticklabels(lon_labels); ax.legend(); ax.axhline(0, color='gray', linewidth=0.5)
for i in range(len(lon_labels)):
    diff = df7['Delta_CRE_net'].iloc[i]
    y_pos = min(df7['Intact_CRE_net'].iloc[i], df7['Arc_CRE_net'].iloc[i]) - 3
    ax.annotate(f'\u0394={diff:+.1f}', (i, y_pos), ha='center', fontsize=10, fontweight='bold',
                color='red' if diff < 0 else 'green')
plt.tight_layout()
plt.savefig(os.path.join(FIGURES_DIR, "fig5_deforestation_counterfactual.png"), dpi=300, bbox_inches='tight')
plt.close()
print("  Saved fig5_deforestation_counterfactual.png")


# ══════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*70}")
print("ANALYSIS COMPLETE")
print(f"{'='*70}")
print(f"\nResults saved to: {RESULTS_DIR}/")
for f in sorted(os.listdir(RESULTS_DIR)):
    size = os.path.getsize(os.path.join(RESULTS_DIR, f))
    print(f"  {f} ({size} bytes)")
print(f"\nFigures saved to: {FIGURES_DIR}/")
for f in sorted(os.listdir(FIGURES_DIR)):
    size = os.path.getsize(os.path.join(FIGURES_DIR, f))
    print(f"  {f} ({size:,} bytes)")
print(f"\nEvery number in the manuscript is traceable to a CSV in results/.")
print(f"Re-run this script to reproduce all results from raw CERES + ERA5 data.")
