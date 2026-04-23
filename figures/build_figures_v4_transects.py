"""
Paper 6 v4 — Figures 6, 7, 8, 9
================================
Cross-basin transects, recycling amplification, seasonal transect,
deforestation counterfactual.

Key revision vs v3:
- Fig 7 replaces "Bunyard 75%" reference line with geometric bound eta ~= 35%
- No Bunyard annotations anywhere

Design spec: paper_6_transfer_fraction/docs/superpowers/specs/
              2026-04-23-paper-6-universal-reframe-design.md (Section 12)
"""

import os
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import warnings
warnings.filterwarnings('ignore')

# ── Style standards ────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial'],
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'axes.linewidth': 0.8,
    'xtick.major.width': 0.8,
    'ytick.major.width': 0.8,
    'axes.spines.top': False,
    'axes.spines.right': False,
})

C_SW  = '#1f77b4'   # blue
C_LW  = '#d62728'   # red
C_NET = '#2ca02c'   # green (used for some; alt: black)
C_NET_BLACK = 'black'

# ── Paths ──────────────────────────────────────────────────────────────
CERES_PATH = "D:/chagpt export/pace-alpha-coefficients/data/raw/ceres/CERES_EBAF_Edition4.2_200003-202407.nc"
OUT_DIR = "D:/Projects/Programme/paper_6_transfer_fraction/figures_v4"
os.makedirs(OUT_DIR, exist_ok=True)


def ceres_lon_to_360(lon):
    return lon % 360


def extract_ceres(ds, lat_range, lon_range, months=None):
    lon_min = ceres_lon_to_360(lon_range[0])
    lon_max = ceres_lon_to_360(lon_range[1])
    if lon_min > lon_max:
        mask = (ds.lon >= lon_min) | (ds.lon <= lon_max)
    else:
        mask = (ds.lon >= lon_min) & (ds.lon <= lon_max)
    region = ds.sel(lat=slice(lat_range[0], lat_range[1])).where(mask, drop=True)
    if months is not None:
        region = region.sel(time=region['time.month'].isin(months))
    return region


def _panel_label(ax, label, dx=-0.12, dy=1.02):
    """Panel label placed outside the axis frame, upper-left corner."""
    ax.text(dx, dy, label, transform=ax.transAxes,
            fontsize=12, fontweight='bold', va='bottom', ha='left')


# ── Load CERES ─────────────────────────────────────────────────────────
print("Loading CERES EBAF...")
ceres = xr.open_dataset(CERES_PATH)


# ══════════════════════════════════════════════════════════════════════
# FIGURE 6 — Cross-basin transects (Amazon, Congo, SE Asia)
# ══════════════════════════════════════════════════════════════════════
print("\n[Fig 6] Cross-basin transects…")

# Each basin: 5-6 coastal-to-interior boxes; x-axis is distance from coast (km)
# 1 degree ~ 111 km at equator
BASINS = {
    'Amazon': {
        # lon bins move inland (coast ~ -50W toward -75W)
        'transects': [
            ('Coast',    (-5, 0), (-50, -45),  0),
            ('East',     (-5, 0), (-55, -50),  500),
            ('Central',  (-5, 0), (-60, -55),  1000),
            ('West',     (-5, 0), (-65, -60),  1500),
            ('Interior', (-5, 0), (-70, -65),  2000),
            ('Andes',    (-5, 0), (-75, -70),  2500),
        ],
    },
    'Congo': {
        # coast ~ 10E, moving east into interior ~ 30E
        'transects': [
            ('Coast',      (-3, 2), (10, 14),   0),
            ('W Congo',    (-3, 2), (14, 18),   500),
            ('Central',    (-3, 2), (18, 22),  1000),
            ('E Congo',    (-3, 2), (22, 26),  1500),
            ('Interior',   (-3, 2), (26, 30),  2000),
        ],
    },
    'SE Asia': {
        # Borneo / Maritime Continent; coast(Sumatra) to interior(Borneo/Papua)
        'transects': [
            ('Sumatra W', (-3, 3), (95, 100),   0),
            ('Sumatra E', (-3, 3), (100, 105), 500),
            ('Java Sea',  (-3, 3), (105, 110),1000),
            ('Borneo W',  (-3, 3), (110, 115),1500),
            ('Borneo E',  (-3, 3), (115, 120),2000),
        ],
    },
}


def compute_transect(transects, months=None):
    dist, sw, lw, net = [], [], [], []
    for label, lat, lon, d in transects:
        c = extract_ceres(ceres, lat, lon, months=months)
        dist.append(d)
        sw.append(float(c['toa_cre_sw_mon'].mean()))
        lw.append(float(c['toa_cre_lw_mon'].mean()))
        net.append(float(c['toa_cre_net_mon'].mean()))
    return np.array(dist), np.array(sw), np.array(lw), np.array(net)


fig, axes = plt.subplots(1, 3, figsize=(6.5 * 1.5, 4.2), sharey=True)
labels = ['(a)', '(b)', '(c)']
basin_titles = ['Amazon', 'Congo', 'SE Asia']
for i, (bname, ax) in enumerate(zip(basin_titles, axes)):
    d, sw, lw, net = compute_transect(BASINS[bname]['transects'])
    ax.plot(d, sw,  'o-', color=C_SW,  linewidth=1.8, markersize=5, label=r'CRE$_{\rm SW}$')
    ax.plot(d, lw,  's-', color=C_LW,  linewidth=1.8, markersize=5, label=r'CRE$_{\rm LW}$')
    ax.plot(d, net, 'D-', color=C_NET_BLACK, linewidth=2.0, markersize=5, label=r'CRE$_{\rm net}$')
    ax.axhline(0, color='gray', linewidth=0.5, linestyle=':')
    ax.set_xlabel('Distance from coast (km)')
    if i == 0:
        ax.set_ylabel(r'CRE (W m$^{-2}$)')
    ax.set_title(bname, fontsize=11)
    ax.grid(True, alpha=0.3, linewidth=0.5)
    _panel_label(ax, labels[i])
    if i == 2:
        ax.legend(loc='center right', frameon=False)

fig.tight_layout()
fig.savefig(f"{OUT_DIR}/fig6_cross_basin_transects.pdf", bbox_inches='tight')
fig.savefig(f"{OUT_DIR}/fig6_cross_basin_transects.png", dpi=300, bbox_inches='tight')
plt.close(fig)
print("  Saved fig6_cross_basin_transects.{pdf,png}")


# ══════════════════════════════════════════════════════════════════════
# FIGURE 7 — Recycling amplification model (REVISED: geometric bound ~35%)
# ══════════════════════════════════════════════════════════════════════
print("\n[Fig 7] Recycling amplification…")

# Eltahir-Bras: eta_basin = eta_site / (1 - rho)
eta_site = 0.129             # BR-Sa1 single-site anchor (matches main text §4.6;
                             # yields amplification 20.8/12.9 = 1.62x and rho = 0.38)
eta_empirical = 0.208        # CERES empirical basin value
eta_geom_bound = 0.35        # geometric bound for deep convection

# rho implied by empirical: rho = 1 - eta_site / eta_empirical = 1 - 0.129/0.208 = 0.380
rho_empirical = 1 - eta_site / eta_empirical     # ≈ 0.380 — on-curve, matches main text

# rho at geometric bound:
rho_geom = 1 - eta_site / eta_geom_bound         # ≈ 0.63

# Amazon published recycling range
rho_lo, rho_hi = 0.25, 0.67

# Curve
rho = np.linspace(0.0, 0.85, 400)
eta_basin = eta_site / (1 - rho)

fig, ax = plt.subplots(figsize=(6.5, 4.8))

# Shaded published range
ax.axvspan(rho_lo, rho_hi, color='gray', alpha=0.15, zorder=0,
           label=f'Published Amazon ρ range (0.25–0.67)')

# Theoretical curve
ax.plot(rho, eta_basin * 100, '-', color='#333333', linewidth=2.2,
        label=r'$\eta_{\rm basin} = \eta_{\rm site}/(1-\rho)$,  $\eta_{\rm site}=12.9\%$ (BR-Sa1)',
        zorder=3)

# Site reference line
ax.axhline(eta_site * 100, color=C_SW, linestyle='--', linewidth=1.2,
           label=f'Site η = {eta_site*100:.1f}%')

# GEOMETRIC BOUND (replaces Bunyard line)
ax.axhline(eta_geom_bound * 100, color='#8c564b', linestyle='--', linewidth=1.5,
           label=f'Geometric bound (deep convection) η ≈ {eta_geom_bound*100:.0f}%')

# Mark CERES empirical point
ax.plot(rho_empirical, eta_empirical * 100, 'o', color='black',
        markersize=10, zorder=5,
        markeredgecolor='white', markeredgewidth=1.2,
        label=f'CERES empirical (η = {eta_empirical*100:.1f}%, ρ = {rho_empirical:.2f})')

# Mark ρ where curve meets geometric bound
ax.plot(rho_geom, eta_geom_bound * 100, 's', color='#8c564b',
        markersize=9, zorder=5, markeredgecolor='white', markeredgewidth=1.0)
ax.annotate(f'ρ required to reach\ngeometric bound ≈ {rho_geom:.2f}',
            xy=(rho_geom, eta_geom_bound * 100),
            xytext=(rho_geom - 0.28, eta_geom_bound * 100 + 8),
            fontsize=7, color='#8c564b',
            arrowprops=dict(arrowstyle='->', color='#8c564b', lw=0.8))

# Annotate empirical point
ax.annotate(f'ρ = {rho_empirical:.2f}',
            xy=(rho_empirical, eta_empirical * 100),
            xytext=(rho_empirical + 0.04, eta_empirical * 100 - 4),
            fontsize=7)

ax.set_xlim(0, 0.8)
ax.set_ylim(0, 60)
ax.set_xlabel(r'Recycling fraction $\rho$')
ax.set_ylabel(r'Basin-scale transfer fraction $\eta_{\rm basin}$ (%)')
ax.grid(True, alpha=0.3, linewidth=0.5)
ax.legend(loc='upper left', frameon=False, fontsize=7.5)

fig.tight_layout()
fig.savefig(f"{OUT_DIR}/fig7_recycling_amplification.pdf", bbox_inches='tight')
fig.savefig(f"{OUT_DIR}/fig7_recycling_amplification.png", dpi=300, bbox_inches='tight')
plt.close(fig)
print("  Saved fig7_recycling_amplification.{pdf,png}")


# ══════════════════════════════════════════════════════════════════════
# FIGURE 8 — Seasonal Amazon transect (wet vs dry)
# ══════════════════════════════════════════════════════════════════════
print("\n[Fig 8] Seasonal Amazon transect…")

AMAZON_SEASONAL = BASINS['Amazon']['transects']
wet_months = [12, 1, 2, 3, 4, 5]
dry_months = [6, 7, 8, 9, 10, 11]

d, sw_w, lw_w, net_w = compute_transect(AMAZON_SEASONAL, months=wet_months)
_, sw_d, lw_d, net_d = compute_transect(AMAZON_SEASONAL, months=dry_months)

fig, axes = plt.subplots(1, 2, figsize=(6.5 * 1.25, 4.2), sharey=True)

for ax, sw, lw, net, title, label in [
    (axes[0], sw_w, lw_w, net_w, 'Wet season (DJF–MAM)', '(a)'),
    (axes[1], sw_d, lw_d, net_d, 'Dry season (JJA–SON)', '(b)'),
]:
    ax.plot(d, sw,  'o-', color=C_SW,  linewidth=1.8, markersize=5, label=r'CRE$_{\rm SW}$')
    ax.plot(d, lw,  's-', color=C_LW,  linewidth=1.8, markersize=5, label=r'CRE$_{\rm LW}$')
    ax.plot(d, net, 'D-', color=C_NET_BLACK, linewidth=2.0, markersize=5, label=r'CRE$_{\rm net}$')
    ax.axhline(0, color='gray', linewidth=0.5, linestyle=':')
    ax.set_xlabel('Distance from coast (km)')
    ax.set_title(title, fontsize=11)
    ax.grid(True, alpha=0.3, linewidth=0.5)
    _panel_label(ax, label)

axes[0].set_ylabel(r'CRE (W m$^{-2}$)')
axes[1].legend(loc='center right', frameon=False)

fig.tight_layout()
fig.savefig(f"{OUT_DIR}/fig8_seasonal_transect.pdf", bbox_inches='tight')
fig.savefig(f"{OUT_DIR}/fig8_seasonal_transect.png", dpi=300, bbox_inches='tight')
plt.close(fig)
print("  Saved fig8_seasonal_transect.{pdf,png}")


# ══════════════════════════════════════════════════════════════════════
# FIGURE 9 — Deforestation counterfactual (intact vs arc)
# ══════════════════════════════════════════════════════════════════════
print("\n[Fig 9] Deforestation counterfactual…")

INTACT_LAT = (-3, 2)     # interior forest strip
ARC_LAT    = (-12, -7)   # arc of deforestation
LON_BINS = [(-60, -55), (-55, -50), (-50, -45)]
LON_LABELS = ['60–55 W', '55–50 W', '50–45 W']


def group_stats(lat_range, months=None):
    net, cloud = [], []
    for lon in LON_BINS:
        c = extract_ceres(ceres, lat_range, lon, months=months)
        net.append(float(c['toa_cre_net_mon'].mean()))
        cloud.append(float(c['cldarea_total_daynight_mon'].mean()))
    return np.array(net), np.array(cloud)


# Annual, wet, dry means across the 3 lon bins
seasons = [
    ('Wet (DJF–MAM)', wet_months),
    ('Dry (JJA–SON)', dry_months),
    ('Annual',        None),
]

intact_net = []
arc_net = []
for sname, months in seasons:
    i_net, _ = group_stats(INTACT_LAT, months=months)
    a_net, _ = group_stats(ARC_LAT, months=months)
    intact_net.append(np.mean(i_net))
    arc_net.append(np.mean(a_net))

# Cloud fraction difference per longitude bin (annual)
i_net_ann, i_cld_ann = group_stats(INTACT_LAT, months=None)
a_net_ann, a_cld_ann = group_stats(ARC_LAT,    months=None)
cloud_diff = i_cld_ann - a_cld_ann  # percentage points

fig, axes = plt.subplots(1, 2, figsize=(6.5 * 1.35, 4.3))

# Panel (a) grouped bars: CRE_net intact vs arc, wet/dry/annual
ax = axes[0]
x = np.arange(len(seasons))
w = 0.36
season_names = [s[0] for s in seasons]
b1 = ax.bar(x - w/2, intact_net, w, color='#2ca02c', alpha=0.85, label='Intact forest')
b2 = ax.bar(x + w/2, arc_net,    w, color='#8c564b', alpha=0.85, label='Deforested arc')
# annotate penalty
for i, (iv, av) in enumerate(zip(intact_net, arc_net)):
    penalty = iv - av
    y_top = max(iv, av)
    ax.text(x[i], y_top + 0.8, f'Δ = {penalty:+.1f}', ha='center', fontsize=7.5)
ax.axhline(0, color='gray', linewidth=0.5)
ax.set_xticks(x)
ax.set_xticklabels(season_names)
ax.set_ylabel(r'CRE$_{\rm net}$ (W m$^{-2}$)')
ax.set_title('CRE$_{\\rm net}$: intact forest vs deforested arc')
ax.legend(frameon=False)
ax.grid(True, axis='y', alpha=0.3, linewidth=0.5)
_panel_label(ax, '(a)')

# Panel (b) cloud fraction difference in pp
ax = axes[1]
bars = ax.bar(LON_LABELS, cloud_diff, color='#555555', alpha=0.8)
for bar, val in zip(bars, cloud_diff):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
            f'{val:+.1f} pp', ha='center', fontsize=7.5)
ax.set_ylabel('Cloud fraction difference (pp)\nIntact − Arc')
ax.set_xlabel('Longitude bin')
ax.set_title('Cloud cover loss in deforested arc')
ax.grid(True, axis='y', alpha=0.3, linewidth=0.5)
ax.axhline(0, color='gray', linewidth=0.5)
_panel_label(ax, '(b)')

fig.tight_layout()
fig.savefig(f"{OUT_DIR}/fig9_deforestation_counterfactual.pdf", bbox_inches='tight')
fig.savefig(f"{OUT_DIR}/fig9_deforestation_counterfactual.png", dpi=300, bbox_inches='tight')
plt.close(fig)
print("  Saved fig9_deforestation_counterfactual.{pdf,png}")

print("\nAll figures built. Output directory:", OUT_DIR)
print("\nFig 9 diagnostics (cloud diff, pp):", cloud_diff)
print("Fig 9 diagnostics (intact_net / arc_net by season):")
for s, i, a in zip(season_names, intact_net, arc_net):
    print(f"  {s:20s}  intact={i:+.2f}  arc={a:+.2f}  Δ={i-a:+.2f}")
