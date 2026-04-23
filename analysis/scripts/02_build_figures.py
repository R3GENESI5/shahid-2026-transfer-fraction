"""
Paper F: Publication-quality figures
=====================================
Rebuilt for authority and clarity.
Uses consistent design language, proper uncertainty, and clean typography.
"""

import numpy as np
import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.lines import Line2D
from scipy import stats
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import os
import json
import warnings
warnings.filterwarnings('ignore')

# ── Style ──────────────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 0.8,
    'lines.linewidth': 1.5,
    'patch.linewidth': 0.5,
})

# Colors
C_FOREST = '#1a6e3a'
C_FOREST_LIGHT = '#a8d5ba'
C_OCEAN = '#2171b5'
C_OCEAN_LIGHT = '#9ecae1'
C_SUBTROP = '#d95f02'
C_TEMP = '#666666'
C_SW = '#4292c6'      # blue for shortwave cooling
C_LW = '#ef6548'      # red/coral for longwave warming
C_NET = '#252525'      # dark for net
C_DEFOREST = '#8c510a'
C_INTACT = '#1a6e3a'
C_BUNYARD = '#e31a1c'
C_BASIN = '#238b45'

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIG_DIR = os.path.join(BASE_DIR, "figures")
REPO_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
CERES_PATH = os.path.join(REPO_DIR, "data", "raw", "ceres", "CERES_EBAF_Edition4.2_200003-202407.nc")

os.makedirs(FIG_DIR, exist_ok=True)

# Load results
df8 = pd.read_csv(os.path.join(RESULTS_DIR, "table8_cre_lw_vs_cape.csv"))
df1 = pd.read_csv(os.path.join(RESULTS_DIR, "table1_basin_cre.csv"))
df2 = pd.read_csv(os.path.join(RESULTS_DIR, "table2_amazon_transect.csv"))
df3 = pd.read_csv(os.path.join(RESULTS_DIR, "table3_congo_transect.csv"))
df4 = pd.read_csv(os.path.join(RESULTS_DIR, "table4_se_asia_transect.csv"))
df5 = pd.read_csv(os.path.join(RESULTS_DIR, "table5_seasonal_amazon_wet.csv"))
df6 = pd.read_csv(os.path.join(RESULTS_DIR, "table6_seasonal_amazon_dry.csv"))
df7 = pd.read_csv(os.path.join(RESULTS_DIR, "table7_deforestation_counterfactual.csv"))
df9 = pd.read_csv(os.path.join(RESULTS_DIR, "table9_recycling_model.csv"))

with open(os.path.join(RESULTS_DIR, "summary_key_numbers.json")) as f:
    KEY = json.load(f)


# ══════════════════════════════════════════════════════════════════════
# FIGURE 1: Study regions map with CERES CRE_net background
# ══════════════════════════════════════════════════════════════════════
print("Figure 1: Study regions map...")
ceres = xr.open_dataset(CERES_PATH)
cre_net_clim = ceres['toa_cre_net_mon'].mean(dim='time')

fig = plt.figure(figsize=(12, 6))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
ax.set_extent([-100, 140, -30, 30], crs=ccrs.PlateCarree())

# CRE_net background
lons = ceres.lon.values
lats = ceres.lat.values
lons_shifted = np.where(lons > 180, lons - 360, lons)
sort_idx = np.argsort(lons_shifted)
lons_plot = lons_shifted[sort_idx]
data_plot = cre_net_clim.values[:, sort_idx]

im = ax.pcolormesh(lons_plot, lats, data_plot, cmap='RdBu_r',
                   vmin=-60, vmax=20, shading='auto', transform=ccrs.PlateCarree())

ax.add_feature(cfeature.COASTLINE, linewidth=0.5, color='#333333')
ax.add_feature(cfeature.BORDERS, linewidth=0.3, color='#666666')

# Basin outlines
basins = {
    'Amazon': ((-80, -45), (-15, 5)),
    'Congo': ((15, 30), (-10, 5)),
    'SE Asia': ((105, 120), (-5, 5)),
}
for name, (lon_r, lat_r) in basins.items():
    rect = Rectangle((lon_r[0], lat_r[0]), lon_r[1]-lon_r[0], lat_r[1]-lat_r[0],
                      linewidth=2, edgecolor='white', facecolor='none',
                      transform=ccrs.PlateCarree(), linestyle='-')
    ax.add_patch(rect)
    ax.text(lon_r[0] + (lon_r[1]-lon_r[0])/2, lat_r[1] + 2, name,
            ha='center', fontsize=11, fontweight='bold', color='white',
            transform=ccrs.PlateCarree(),
            bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.6))

# Amazon transect strips
for i, lon_start in enumerate(range(-75, -44, 5)):
    alpha = 0.15 if i % 2 == 0 else 0.25
    rect = Rectangle((lon_start, -5), 5, 5,
                      linewidth=0.5, edgecolor='yellow', facecolor='yellow',
                      alpha=alpha, transform=ccrs.PlateCarree())
    ax.add_patch(rect)

# Arc of deforestation
rect = Rectangle((-60, -12), 15, 5,
                 linewidth=1.5, edgecolor=C_DEFOREST, facecolor='none',
                 linestyle='--', transform=ccrs.PlateCarree())
ax.add_patch(rect)
ax.text(-52.5, -14.5, 'Arc of\ndeforestation', ha='center', fontsize=8,
        color=C_DEFOREST, transform=ccrs.PlateCarree(), fontweight='bold')

cb = plt.colorbar(im, ax=ax, orientation='horizontal', pad=0.08,
                  shrink=0.6, aspect=30)
cb.set_label('CRE$_{net}$ (W m$^{-2}$)', fontsize=12)

ax.set_title('Study Regions over CERES EBAF Cloud Radiative Effect (2000-2024 climatology)',
             fontsize=13, fontweight='bold', pad=12)

gl = ax.gridlines(draw_labels=True, linewidth=0.3, color='gray', alpha=0.5)
gl.top_labels = False
gl.right_labels = False

plt.savefig(os.path.join(FIG_DIR, "fig1_study_regions.png"))
plt.close()
print("  Saved fig1_study_regions.png")
ceres.close()


# ══════════════════════════════════════════════════════════════════════
# FIGURE 2: CRE_LW vs CAPE (hero figure)
# ══════════════════════════════════════════════════════════════════════
print("Figure 2: CRE_LW vs CAPE (hero)...")

fig, axes = plt.subplots(1, 2, figsize=(14, 6.5),
                          gridspec_kw={'width_ratios': [1.3, 1]})

cape = df8['CAPE_J_kg'].values
cre_lw = df8['CRE_LW'].values
cre_sw = df8['CRE_SW'].values
cre_net = df8['CRE_net'].values

color_map = {'Tropical forest': C_FOREST, 'Ocean': C_OCEAN,
             'Subtropical': C_SUBTROP, 'Temperate': C_TEMP}
colors = [color_map[t] for t in df8['Type']]

# Panel (a): CRE_LW vs CAPE with confidence band
ax = axes[0]
reg = stats.linregress(cape, cre_lw)
x_fit = np.linspace(0, 1550, 200)
y_fit = reg.intercept + reg.slope * x_fit

# Prediction interval
n = len(cape)
x_mean = cape.mean()
se_pred = reg.stderr * np.sqrt(1 + 1/n + (x_fit - x_mean)**2 / np.sum((cape - x_mean)**2))
# Use residual standard error instead
residuals = cre_lw - (reg.intercept + reg.slope * cape)
s_res = np.sqrt(np.sum(residuals**2) / (n-2))
se_conf = s_res * np.sqrt(1/n + (x_fit - x_mean)**2 / np.sum((cape - x_mean)**2))

ax.fill_between(x_fit, y_fit - 1.96*se_conf, y_fit + 1.96*se_conf,
                color=C_LW, alpha=0.12, label='95% CI')
ax.plot(x_fit, y_fit, color=C_LW, linewidth=2.5, zorder=4)
ax.scatter(cape, cre_lw, c=colors, s=90, zorder=5, edgecolors='white', linewidths=0.8)

# Label key points
for _, row in df8.iterrows():
    if row['Region'] in ['Amazon Interior', 'Congo Central', 'Borneo West', 'W Europe', 'Trop E Pacific']:
        ax.annotate(row['Region'], (row['CAPE_J_kg'], row['CRE_LW']),
                    xytext=(8, -4), textcoords='offset points', fontsize=8,
                    color='#444444', fontstyle='italic')

ax.set_xlabel('CAPE (J kg$^{-1}$)')
ax.set_ylabel('CRE$_{LW}$ (W m$^{-2}$)')
ax.set_title(f'(a)  CRE$_{{LW}}$ = {reg.intercept:.1f} + {reg.slope:.3f} CAPE'
             f'    R$^2$ = {reg.rvalue**2:.2f},  p = {reg.pvalue:.1e}',
             fontsize=11, loc='left')
ax.grid(True, alpha=0.2, linewidth=0.5)
ax.set_xlim(-30, 1550)
ax.set_ylim(5, 72)

legend_elements = [
    Line2D([0], [0], marker='o', color='w', markerfacecolor=C_FOREST, markersize=10, label='Tropical forest'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor=C_OCEAN, markersize=10, label='Ocean'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor=C_SUBTROP, markersize=10, label='Subtropical'),
    Line2D([0], [0], marker='o', color='w', markerfacecolor=C_TEMP, markersize=10, label='Temperate'),
]
ax.legend(handles=legend_elements, loc='lower right', framealpha=0.9, fontsize=10)

# Panel (b): LW/SW ratio vs CAPE
ax = axes[1]
lw_sw_ratio = np.abs(cre_lw / cre_sw)
reg_ratio = stats.linregress(cape, lw_sw_ratio)
y_ratio_fit = reg_ratio.intercept + reg_ratio.slope * x_fit

ax.scatter(cape, lw_sw_ratio, c=colors, s=90, zorder=5, edgecolors='white', linewidths=0.8)
ax.plot(x_fit, y_ratio_fit, color=C_NET, linewidth=2, linestyle='-', zorder=4)

# Mark the convergence zone
ax.axhline(1.0, color=C_BUNYARD, linewidth=1, linestyle=':', alpha=0.7)
ax.text(1500, 1.02, 'Full offset\n(CRE$_{LW}$ = |CRE$_{SW}$|)', ha='right',
        fontsize=8, color=C_BUNYARD, fontstyle='italic')

ax.fill_between([800, 1550], 0, 2, color=C_LW, alpha=0.05)
ax.text(1150, 0.38, 'Deep tropical\nconvection zone', ha='center', fontsize=9,
        color=C_LW, fontstyle='italic', alpha=0.7)

ax.set_xlabel('CAPE (J kg$^{-1}$)')
ax.set_ylabel('CRE$_{LW}$ / |CRE$_{SW}$| ratio')
ax.set_title(f'(b)  LW offset ratio converges toward 1.0 with depth'
             f'    R$^2$ = {reg_ratio.rvalue**2:.2f}',
             fontsize=11, loc='left')
ax.grid(True, alpha=0.2, linewidth=0.5)
ax.set_xlim(-30, 1550)
ax.set_ylim(0.3, 1.15)

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig2_cre_lw_vs_cape.png"))
plt.close()
print("  Saved fig2_cre_lw_vs_cape.png")


# ══════════════════════════════════════════════════════════════════════
# FIGURE 3: Cross-basin transects (redesigned)
# ══════════════════════════════════════════════════════════════════════
print("Figure 3: Cross-basin transects...")

fig, axes = plt.subplots(1, 3, figsize=(16, 5.5), sharey=True)
fig.suptitle('Coast-to-interior CRE components across three tropical basins',
             fontsize=14, fontweight='bold', y=1.02)

for ax_idx, (basin, df_t) in enumerate([
    ("Amazon", df2), ("Congo", df3), ("SE Asia", df4)
]):
    ax = axes[ax_idx]
    names = df_t['Transect'].tolist()
    x = np.arange(len(names))
    w = 0.35

    # Paired bars: SW and LW
    bars_sw = ax.bar(x - w/2, df_t['CRE_SW'], w, color=C_SW, alpha=0.75,
                     label='CRE$_{SW}$ (cooling)', edgecolor='white', linewidth=0.5)
    bars_lw = ax.bar(x + w/2, df_t['CRE_LW'], w, color=C_LW, alpha=0.75,
                     label='CRE$_{LW}$ (warming)', edgecolor='white', linewidth=0.5)

    # CRE_net as prominent line
    ax.plot(x, df_t['CRE_net'], 'o-', color=C_NET, linewidth=2.5, markersize=8,
            markerfacecolor='white', markeredgecolor=C_NET, markeredgewidth=2,
            label='CRE$_{net}$', zorder=6)

    ax.axhline(0, color='gray', linewidth=0.5)
    ax.set_title(basin, fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    short = [n.split('(')[0].strip() if '(' in n else n.split('T')[0].strip() + n.split('(')[-1].replace(')', '').strip() if '(' in n else n
             for n in names]
    # Simpler labels
    if basin == "Amazon":
        short = ['Coast', 'East', 'Central', 'West', 'Interior', 'Andes']
    elif basin == "Congo":
        short = ['15-18E', '18-21E', '21-24E', '24-27E', '27-30E']
    else:
        short = ['105-108E', '108-111E', '111-114E', '114-117E', '117-120E']
    ax.set_xticklabels(short, rotation=35, ha='right', fontsize=9)
    ax.set_ylim(-85, 70)

    if ax_idx == 0:
        ax.set_ylabel('W m$^{-2}$')
        ax.legend(fontsize=9, loc='lower left', framealpha=0.9)

    # Add arrow showing "coast to interior" direction
    if basin == "Amazon":
        ax.annotate('', xy=(5.2, -78), xytext=(-0.2, -78),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='#555555'))
        ax.text(2.5, -82, 'Coast \u2192 Interior', ha='center', fontsize=9, color='#555555')

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig3_cross_basin_transects.png"))
plt.close()
print("  Saved fig3_cross_basin_transects.png")


# ══════════════════════════════════════════════════════════════════════
# FIGURE 4: Recycling amplification
# ══════════════════════════════════════════════════════════════════════
print("Figure 4: Recycling model...")

fig, ax = plt.subplots(figsize=(8, 6))

eta_site = KEY['paper_e_reference']['eta_site']
eta_basin = KEY['basin_level']['eta_basin']

f_range = np.linspace(0, 0.85, 200)
eta_range = eta_site / (1 - f_range)

ax.plot(f_range * 100, eta_range * 100, color=C_NET, linewidth=2.5, zorder=3)

# Shaded physical range
ax.axvspan(25, 50, color=C_FOREST_LIGHT, alpha=0.3, label='Published recycling range (25-50%)')

# Reference lines
ax.axhline(eta_site * 100, color=C_OCEAN, linewidth=1.5, linestyle='--',
           label=f'Single-site (BR-Sa1): {eta_site*100:.1f}%', zorder=2)
ax.axhline(75, color=C_BUNYARD, linewidth=1.5, linestyle='--',
           label='Bunyard et al. (2024): 75%', zorder=2)
ax.axhline(eta_basin * 100, color=C_BASIN, linewidth=2, linestyle='-',
           label=f'Basin empirical (this study): {eta_basin*100:.1f}%', zorder=4)

# Published estimates
markers = [
    (25, 'Eltahir & Bras\n(1994)', C_FOREST),
    (35, 'Van der Ent\n(2010)', C_OCEAN),
    (50, 'Salati & Vose\n(1984)', '#7b3294'),
]
for f_pct, label, color in markers:
    eta_val = eta_site / (1 - f_pct/100) * 100
    ax.plot(f_pct, eta_val, 'o', color=color, markersize=12, zorder=6,
            markeredgecolor='white', markeredgewidth=1.5)
    ax.annotate(f'{label}\n\u03b7 = {eta_val:.1f}%', (f_pct, eta_val),
                xytext=(14, -2), textcoords='offset points', fontsize=9,
                color=color, fontweight='bold')

# Mark where 75% would require
f_for_75 = (1 - eta_site / 0.75) * 100
ax.annotate(f'75% requires f = {f_for_75:.0f}%\n(physically unrealistic)',
            (f_for_75, 75), xytext=(-80, 20), textcoords='offset points',
            fontsize=9, color=C_BUNYARD, fontstyle='italic',
            arrowprops=dict(arrowstyle='->', color=C_BUNYARD, lw=1))

ax.set_xlabel('Recycling fraction f (%)', fontsize=13)
ax.set_ylabel('Basin-level transfer fraction \u03b7 (%)', fontsize=13)
ax.set_title('Recycling amplification of the transfer fraction', fontsize=14, fontweight='bold')
ax.legend(fontsize=10, loc='upper left', framealpha=0.95)
ax.set_xlim(0, 90)
ax.set_ylim(0, 85)
ax.grid(True, alpha=0.2, linewidth=0.5)

plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig4_recycling_model.png"))
plt.close()
print("  Saved fig4_recycling_model.png")


# ══════════════════════════════════════════════════════════════════════
# FIGURE 5: Seasonal Amazon transect
# ══════════════════════════════════════════════════════════════════════
print("Figure 5: Seasonal transect...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

labels_short = ['Coast', 'East', 'Central', 'West', 'Interior', 'Andes']

for ax_idx, (season, df_s, title) in enumerate([
    ("Wet", df5, "Wet season (DJF-MAM)"),
    ("Dry", df6, "Dry season (JJA-SON)"),
]):
    ax = axes[ax_idx]
    x = np.arange(len(labels_short))
    w = 0.35

    ax.bar(x - w/2, df_s['CRE_SW'], w, color=C_SW, alpha=0.75,
           label='CRE$_{SW}$', edgecolor='white', linewidth=0.5)
    ax.bar(x + w/2, df_s['CRE_LW'], w, color=C_LW, alpha=0.75,
           label='CRE$_{LW}$', edgecolor='white', linewidth=0.5)
    ax.plot(x, df_s['CRE_net'], 'o-', color=C_NET, linewidth=2.5, markersize=8,
            markerfacecolor='white', markeredgecolor=C_NET, markeredgewidth=2,
            label='CRE$_{net}$', zorder=6)

    # Cloud fraction as secondary axis
    ax2 = ax.twinx()
    ax2.plot(x, df_s['Cloud_frac_pct'], 's--', color='#999999', markersize=6,
             linewidth=1, alpha=0.7, label='Cloud fraction')
    ax2.set_ylabel('Cloud fraction (%)', color='#999999', fontsize=10)
    ax2.set_ylim(40, 100)
    ax2.tick_params(axis='y', colors='#999999')
    if ax_idx == 0:
        ax2.legend(loc='lower right', fontsize=8, framealpha=0.8)

    ax.axhline(0, color='gray', linewidth=0.5)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(labels_short, rotation=30, ha='right')
    ax.set_ylim(-100, 80)
    ax.set_ylabel('W m$^{-2}$')
    if ax_idx == 0:
        ax.legend(fontsize=9, loc='lower left', framealpha=0.9)

    # Annotate biotic pump signature in dry season
    if season == "Dry":
        ax.annotate('Interior retains\n78% cloud cover\n(biotic pump)',
                    xy=(4, df_s['CRE_SW'].iloc[4]),
                    xytext=(0.5, -85), textcoords='data',
                    fontsize=9, color=C_FOREST, fontweight='bold', fontstyle='italic',
                    arrowprops=dict(arrowstyle='->', color=C_FOREST, lw=1.2))

fig.suptitle('Amazon transect: seasonal contrast', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig5_seasonal_transect.png"))
plt.close()
print("  Saved fig5_seasonal_transect.png")


# ══════════════════════════════════════════════════════════════════════
# FIGURE 6: Deforestation counterfactual
# ══════════════════════════════════════════════════════════════════════
print("Figure 6: Deforestation counterfactual...")

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5),
                          gridspec_kw={'width_ratios': [1.2, 1]})

lon_labels = df7['Longitude'].tolist()
x = np.arange(len(lon_labels))
w = 0.3

# Panel (a): CRE_net comparison
ax = axes[0]
ax.bar(x - w/2, df7['Intact_CRE_net'], w, color=C_INTACT, alpha=0.85,
       label='Intact forest (3\u00b0S-2\u00b0N)', edgecolor='white', linewidth=0.8)
ax.bar(x + w/2, df7['Arc_CRE_net'], w, color=C_DEFOREST, alpha=0.85,
       label='Arc of deforestation (12\u00b0S-7\u00b0S)', edgecolor='white', linewidth=0.8)

# Delta annotations
for i in range(len(lon_labels)):
    delta = df7['Delta_CRE_net'].iloc[i]
    y_mid = (df7['Intact_CRE_net'].iloc[i] + df7['Arc_CRE_net'].iloc[i]) / 2
    ax.annotate(f'\u0394 = {delta:.1f}',
                xy=(i, min(df7['Intact_CRE_net'].iloc[i], df7['Arc_CRE_net'].iloc[i]) - 1.5),
                ha='center', fontsize=11, fontweight='bold', color=C_BUNYARD)

ax.axhline(0, color='gray', linewidth=0.5)
ax.set_ylabel('CRE$_{net}$ (W m$^{-2}$)')
ax.set_title('(a)  Net cloud radiative effect', fontsize=12, loc='left')
ax.set_xticks(x)
ax.set_xticklabels(lon_labels, fontsize=11)
ax.set_xlabel('Longitude band')
ax.legend(fontsize=10, framealpha=0.95)

# Panel (b): Cloud fraction comparison
ax = axes[1]
ax.bar(x - w/2, df7['Intact_Cloud_pct'], w, color=C_INTACT, alpha=0.85,
       label='Intact', edgecolor='white', linewidth=0.8)
ax.bar(x + w/2, df7['Arc_Cloud_pct'], w, color=C_DEFOREST, alpha=0.85,
       label='Deforested', edgecolor='white', linewidth=0.8)

for i in range(len(lon_labels)):
    delta = df7['Delta_Cloud_pct'].iloc[i]
    y_top = max(df7['Intact_Cloud_pct'].iloc[i], df7['Arc_Cloud_pct'].iloc[i]) + 1
    ax.annotate(f'+{delta:.1f}%', xy=(i, y_top), ha='center', fontsize=10,
                fontweight='bold', color=C_INTACT)

ax.set_ylabel('Cloud fraction (%)')
ax.set_title('(b)  Cloud cover', fontsize=12, loc='left')
ax.set_xticks(x)
ax.set_xticklabels(lon_labels, fontsize=11)
ax.set_xlabel('Longitude band')
ax.legend(fontsize=10, framealpha=0.95)

fig.suptitle('Intact forest vs arc of deforestation at matched longitudes',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(FIG_DIR, "fig6_deforestation_counterfactual.png"))
plt.close()
print("  Saved fig6_deforestation_counterfactual.png")


# ══════════════════════════════════════════════════════════════════════
# FIGURE 7: Summary — the three streams at BR-Sa1
# ══════════════════════════════════════════════════════════════════════
print("Figure 7: Three energy streams summary...")

fig, ax = plt.subplots(figsize=(10, 7))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.axis('off')

# Title
ax.text(5, 9.7, 'Energy accounting at BR-Sa1 (Tapajos, Amazon)',
        ha='center', fontsize=15, fontweight='bold')
ax.text(5, 9.3, 'All values in W m$^{-2}$, FLUXNET + CERES EBAF Ed4.2',
        ha='center', fontsize=10, color='#666666')

# TOA line
ax.axhline(8.5, color='#999999', linewidth=1, linestyle=':')
ax.text(9.8, 8.6, 'TOA', fontsize=9, color='#999999', ha='right')

# Surface
rect = FancyBboxPatch((1, 0.5), 8, 0.6, boxstyle="round,pad=0.1",
                       facecolor=C_FOREST, alpha=0.7, edgecolor='white', linewidth=2)
ax.add_patch(rect)
ax.text(5, 0.8, 'Forest surface  |  R$_{net}$ = 111', ha='center',
        fontsize=11, color='white', fontweight='bold')

# LE arrow
ax.annotate('', xy=(3.5, 3.8), xytext=(3.5, 1.3),
            arrowprops=dict(arrowstyle='->', lw=3, color=C_SW))
ax.text(3.5, 2.5, 'LE = 87.1\n(79%)', ha='center', fontsize=11,
        color=C_SW, fontweight='bold')

# H arrow
ax.annotate('', xy=(7.5, 2.5), xytext=(7.5, 1.3),
            arrowprops=dict(arrowstyle='->', lw=1.5, color=C_LW))
ax.text(7.5, 2.0, 'H = 17.4\n(16%)', ha='center', fontsize=10, color=C_LW)

# Cloud level
rect = FancyBboxPatch((1.5, 4.0), 7, 0.5, boxstyle="round,pad=0.1",
                       facecolor=C_SW, alpha=0.15, edgecolor=C_SW, linewidth=1.5)
ax.add_patch(rect)
ax.text(5, 4.2, 'Cloud level (condensation at 3-6 km)', ha='center',
        fontsize=10, color=C_SW, fontweight='bold')

# Stream 1: Cloud albedo
box1 = FancyBboxPatch((0.5, 6.0), 2.8, 1.5, boxstyle="round,pad=0.15",
                       facecolor=C_SW, alpha=0.12, edgecolor=C_SW, linewidth=1.5)
ax.add_patch(box1)
ax.text(1.9, 7.2, 'STREAM 1', ha='center', fontsize=9, fontweight='bold', color=C_SW)
ax.text(1.9, 6.8, 'Cloud albedo', ha='center', fontsize=10, color=C_SW)
ax.text(1.9, 6.3, 'CRE$_{SW}$ = \u221252.3', ha='center', fontsize=12,
        fontweight='bold', color=C_SW)

# Arrow up to TOA for stream 1
ax.annotate('', xy=(1.9, 8.5), xytext=(1.9, 7.6),
            arrowprops=dict(arrowstyle='->', lw=2.5, color=C_SW))

# Solar input arrow down
ax.annotate('', xy=(0.8, 6.0), xytext=(0.8, 8.5),
            arrowprops=dict(arrowstyle='->', lw=2, color='#e6a800'))
ax.text(0.3, 7.5, 'Solar\ninput', ha='center', fontsize=9, color='#cc9600', fontweight='bold')

# Note: not latent heat
ax.text(1.9, 5.7, '(reflected sunlight,', ha='center', fontsize=8, color=C_SW, fontstyle='italic')
ax.text(1.9, 5.4, 'NOT latent heat)', ha='center', fontsize=8, color=C_SW, fontstyle='italic')

# Stream 2: LW trapping
box2 = FancyBboxPatch((3.8, 6.0), 2.5, 1.5, boxstyle="round,pad=0.15",
                       facecolor=C_LW, alpha=0.12, edgecolor=C_LW, linewidth=1.5)
ax.add_patch(box2)
ax.text(5.05, 7.2, 'STREAM 2', ha='center', fontsize=9, fontweight='bold', color=C_LW)
ax.text(5.05, 6.8, 'LW trapping', ha='center', fontsize=10, color=C_LW)
ax.text(5.05, 6.3, 'CRE$_{LW}$ = +41.1', ha='center', fontsize=12,
        fontweight='bold', color=C_LW)

# Arrow DOWN for stream 2 (trapping)
ax.annotate('', xy=(5.05, 4.6), xytext=(5.05, 5.9),
            arrowprops=dict(arrowstyle='->', lw=2, color=C_LW))
ax.text(5.05, 5.3, '(feeds deeper\nconvection)', ha='center', fontsize=8,
        color=C_LW, fontstyle='italic')

# Stream 3: Net TOA
box3 = FancyBboxPatch((6.8, 6.0), 2.8, 1.5, boxstyle="round,pad=0.15",
                       facecolor=C_FOREST, alpha=0.12, edgecolor=C_FOREST, linewidth=1.5)
ax.add_patch(box3)
ax.text(8.2, 7.2, 'STREAM 3', ha='center', fontsize=9, fontweight='bold', color=C_FOREST)
ax.text(8.2, 6.8, 'Net TOA exit', ha='center', fontsize=10, color=C_FOREST)
ax.text(8.2, 6.3, 'CRE$_{net}$ = \u221211.2', ha='center', fontsize=12,
        fontweight='bold', color=C_FOREST)

# Arrow up to TOA for stream 3
ax.annotate('', xy=(8.2, 8.5), xytext=(8.2, 7.6),
            arrowprops=dict(arrowstyle='->', lw=2.5, color=C_FOREST))

# Transfer fraction annotation
ax.text(8.2, 5.6, '\u03b7 = 11.2 / 87.1 = 12.9%', ha='center', fontsize=11,
        fontweight='bold', color=C_FOREST,
        bbox=dict(boxstyle='round,pad=0.3', facecolor=C_FOREST_LIGHT, alpha=0.4, edgecolor=C_FOREST))

plt.savefig(os.path.join(FIG_DIR, "fig7_three_streams.png"))
plt.close()
print("  Saved fig7_three_streams.png")


print("\nAll publication figures generated.")
print(f"Output: {FIG_DIR}/")
for f in sorted(os.listdir(FIG_DIR)):
    print(f"  {f}")
