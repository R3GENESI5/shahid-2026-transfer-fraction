"""
Paper 6 v4 — Universal Reframe: Figures 2, 3, 5
================================================
Builds three publication figures:
  Figure 2 — Surface LE vs TOA CRE_net scatter (314 FLUXNET-CERES sites)
  Figure 3 — Global consistency of eta (3 panels)
  Figure 5 — CRE_LW attenuation / CAPE regression (2 panels)

Design spec: docs/superpowers/specs/2026-04-23-paper-6-universal-reframe-design.md
Data:        D:/Projects/Programme/paper_1_alpha_beta/outputs/toa_tables/site_summary_v3_full.csv
             D:/chagpt export/pace-alpha-coefficients/data/raw/ceres/CERES_EBAF_*.nc
             D:/chagpt export/pace-alpha-coefficients/data/raw/era5_extracted/*.nc

Outputs (figures_v4/):
  fig2_le_vs_cre_net.pdf / .png
  fig3_global_consistency.pdf / .png
  fig5_cape_cre_lw.pdf / .png

Style standards:
  CRE_SW = #1f77b4, CRE_LW = #d62728, CRE_net = #2ca02c
  sans-serif, min 10 pt at 6.5" width, panel labels (a)(b)(c) bold 12 pt lower-left
  PDF vector + PNG 300 DPI, axis units in LaTeX math (W m$^{-2}$)
  No Bunyard annotations. No "75%" reference. Geometric bound at eta = 35%.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

# ── Configuration ─────────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
SITE_CSV = Path(
    "D:/Projects/Programme/paper_1_alpha_beta/outputs/toa_tables/site_summary_v3_full.csv"
)
CERES_PATH = Path(
    "D:/chagpt export/pace-alpha-coefficients/data/raw/ceres/"
    "CERES_EBAF_Edition4.2_200003-202407.nc"
)
ERA5_CAPE = Path(
    "D:/chagpt export/pace-alpha-coefficients/data/raw/era5_extracted/"
    "data_stream-moda_stepType-avgua.nc"
)
OUT_DIR = HERE
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Style
CRE_SW_COLOR = "#1f77b4"   # blue
CRE_LW_COLOR = "#d62728"   # red
CRE_NET_COLOR = "#2ca02c"  # green

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
    "pdf.fonttype": 42,  # embed TrueType
    "ps.fonttype": 42,
})

BIOME_COLORS = {
    "Forest":    "#2d6a4f",
    "Grassland": "#c08a2e",
    "Cropland":  "#8a5a44",
    "Savanna":   "#d48a3a",
    "Shrubland": "#a05a5a",
    "Wetland":   "#3a6a8a",
    "Other":     "#888888",
}


def panel_label(ax, text, x=-0.12, y=1.02):
    """Place bold (a)/(b)/(c) outside the axis frame, upper-left corner."""
    ax.text(x, y, text, transform=ax.transAxes,
            fontsize=12, fontweight="bold", va="bottom", ha="left")


def save(fig, stem):
    fig.savefig(OUT_DIR / f"{stem}.pdf")
    fig.savefig(OUT_DIR / f"{stem}.png", dpi=300)
    print(f"  wrote {stem}.pdf / .png")


def bootstrap_ci(values, n=2000, lo=2.5, hi=97.5, stat=np.median, seed=42):
    rng = np.random.default_rng(seed)
    values = np.asarray(values)
    values = values[~np.isnan(values)]
    if len(values) < 3:
        return np.nan, np.nan
    idx = rng.integers(0, len(values), size=(n, len(values)))
    draws = stat(values[idx], axis=1)
    return np.percentile(draws, lo), np.percentile(draws, hi)


# ── Load site-level data ──────────────────────────────────────────────────────
def load_sites():
    df = pd.read_csv(SITE_CSV)
    # Transfer fraction eta = |CRE_net| / LE  (as a fraction, then convert to %)
    df["eta_pct"] = 100.0 * np.abs(df["ceres_toa_cre_net_mean"]) / df["mean_LE"]
    # Keep sites with valid LE > 0 and finite eta
    df = df[np.isfinite(df["eta_pct"]) & (df["mean_LE"] > 0)].copy()
    # Tropical EBF flag
    df["is_tropical_ebf"] = (df["igbp"] == "EBF") & (df["latitude"].abs() <= 23.5)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 2 — Surface LE vs TOA CRE_net
# ══════════════════════════════════════════════════════════════════════════════
# Caption (v4 manuscript):
# "Figure 2. Surface LE vs TOA CRE_net across 314 FLUXNET-CERES co-located
#  sites. Points colored by biome. Tropical evergreen broadleaf forest sites
#  in yellow. Transfer fraction eta = |CRE_net|/LE is the within-biome ratio,
#  not the cross-site scatter slope. Global median eta = 30.0%
#  [95% CI: 27.1 to 34.5%]."
def build_fig2(df):
    fig, ax = plt.subplots(figsize=(6.5, 5.0))

    biomes_present = [b for b in ["Forest", "Grassland", "Cropland",
                                   "Savanna", "Shrubland", "Wetland"]
                      if b in df["biome_group"].unique()]

    # Non-tropical-EBF points by biome
    non_ebf = df[~df["is_tropical_ebf"]]
    for b in biomes_present:
        sub = non_ebf[non_ebf["biome_group"] == b]
        ax.scatter(sub["mean_LE"], sub["ceres_toa_cre_net_mean"],
                   s=22, alpha=0.75, edgecolor="white", linewidth=0.4,
                   color=BIOME_COLORS.get(b, "#888888"),
                   label=f"{b} (N={len(sub)})", zorder=2)

    # Tropical EBF highlighted
    ebf = df[df["is_tropical_ebf"]]
    ax.scatter(ebf["mean_LE"], ebf["ceres_toa_cre_net_mean"],
               s=75, marker="o", facecolor="#ffd60a",
               edgecolor="black", linewidth=0.8,
               label=f"Tropical EBF (N={len(ebf)})", zorder=4)

    ax.axhline(0, color="0.4", linewidth=0.6, linestyle="--", zorder=1)

    ax.set_xlabel(r"Surface LE (W m$^{-2}$)")
    ax.set_ylabel(r"TOA CRE$_{\mathrm{net}}$ (W m$^{-2}$)")
    ax.set_title("Surface LE vs TOA CRE$_{\\mathrm{net}}$  —  314 FLUXNET-CERES sites",
                 fontsize=11)

    # Global median eta + CI annotation
    eta_med = np.median(df["eta_pct"])
    eta_lo, eta_hi = bootstrap_ci(df["eta_pct"].values)
    ax.text(0.98, 0.98,
            (f"Global median $\\eta$ = {eta_med:.1f}%\n"
             f"[95% CI: {eta_lo:.1f}–{eta_hi:.1f}%]\n"
             f"Cross-site r = {df[['mean_LE', 'ceres_toa_cre_net_mean']].corr().iloc[0,1]:.3f}"),
            transform=ax.transAxes, ha="right", va="top",
            fontsize=9,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor="0.7", linewidth=0.6, alpha=0.95))

    ax.legend(loc="lower right", frameon=True, framealpha=0.9,
              fontsize=8, ncol=2)
    ax.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)

    save(fig, "fig2_le_vs_cre_net")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 3 — Global consistency (histogram, biome bars, latitude scatter)
# ══════════════════════════════════════════════════════════════════════════════
# Caption:
# "Figure 3. Global consistency of the transfer fraction. (a) Histogram of
#  eta across 314 sites. Geometric bound at eta ~ 35% marks the theoretical
#  upper limit imposed by cloud LW opacity in deep convective regimes.
#  (b) Median eta by biome with bootstrap 95% CI. (c) eta vs latitude with
#  tropical, temperate, and boreal medians annotated."
GEOMETRIC_BOUND_PCT = 35.0


def build_fig3(df):
    fig, (axA, axB, axC) = plt.subplots(
        1, 3, figsize=(13.0, 4.5),
        gridspec_kw=dict(wspace=0.32),
    )

    # ── Panel (a): histogram of eta ────────────────────────────────────
    eta = df["eta_pct"].values
    # Clip upper tail for display
    eta_plot = eta[eta <= 150]
    axA.hist(eta_plot, bins=np.arange(0, 151, 5),
             color="#5a7a9a", edgecolor="white", linewidth=0.6)
    axA.axvline(GEOMETRIC_BOUND_PCT, color=CRE_LW_COLOR,
                linewidth=1.6, linestyle="--",
                label=f"Geometric bound (deep convection), $\\eta$ = {GEOMETRIC_BOUND_PCT:.0f}%")
    med = np.median(eta)
    axA.axvline(med, color="black", linewidth=1.2, linestyle="-",
                label=f"Median = {med:.1f}%")
    axA.set_xlabel(r"Transfer fraction $\eta$ = $|$CRE$_{\mathrm{net}}|/$LE (%)")
    axA.set_ylabel("Number of sites")
    axA.set_xlim(0, 150)
    # Extend y-axis headroom so legend does not overlap tallest bars
    ymax_a = axA.get_ylim()[1]
    axA.set_ylim(0, ymax_a * 1.25)
    axA.legend(loc="upper right", fontsize=7.5, frameon=True,
               framealpha=0.92, borderpad=0.4, handlelength=1.6)
    axA.set_title("Distribution across 314 sites", fontsize=10)
    panel_label(axA, "(a)")

    # ── Panel (b): median eta by biome with bootstrap CI ──────────────
    biome_order_raw = ["Forest", "Grassland", "Cropland",
                       "Savanna", "Shrubland", "Wetland"]
    rows = []
    for b in biome_order_raw:
        vals = df.loc[df["biome_group"] == b, "eta_pct"].dropna().values
        if len(vals) == 0:
            continue
        lo, hi = bootstrap_ci(vals)
        rows.append((b, np.median(vals), lo, hi, len(vals)))

    # Sort by median
    rows.sort(key=lambda r: r[1])
    biomes = [r[0] for r in rows]
    meds = np.array([r[1] for r in rows])
    los = np.array([r[2] for r in rows])
    his = np.array([r[3] for r in rows])
    ns = [r[4] for r in rows]

    xpos = np.arange(len(biomes))
    colors = [BIOME_COLORS.get(b, "#888888") for b in biomes]
    yerr = np.vstack([meds - los, his - meds])
    axB.bar(xpos, meds, yerr=yerr, color=colors,
            edgecolor="black", linewidth=0.6, capsize=4,
            error_kw=dict(lw=0.8))
    axB.axhline(GEOMETRIC_BOUND_PCT, color=CRE_LW_COLOR,
                linewidth=1.2, linestyle="--", alpha=0.8,
                label=f"Geometric bound $\\eta$ = {GEOMETRIC_BOUND_PCT:.0f}%")
    for i, (m, n) in enumerate(zip(meds, ns)):
        axB.text(i, m + (his[i] - meds[i]) + 1.5, f"N={n}",
                 ha="center", va="bottom", fontsize=8)
    axB.set_xticks(xpos)
    axB.set_xticklabels(biomes, rotation=20, ha="right")
    axB.set_ylabel(r"Median $\eta$ (%)")
    axB.set_ylim(0, max(his.max() + 12, 50))
    axB.legend(loc="upper left", fontsize=8, frameon=True)
    axB.set_title("By biome (bootstrap 95% CI)", fontsize=10)
    panel_label(axB, "(b)")

    # ── Panel (c): eta vs latitude ─────────────────────────────────────
    lat = df["latitude"].values
    eta_c = df["eta_pct"].values
    mask = np.isfinite(lat) & np.isfinite(eta_c) & (eta_c <= 200)
    lat_m = lat[mask]
    eta_m = eta_c[mask]
    axC.scatter(lat_m, eta_m, s=16, alpha=0.5, color="#3a5a7a",
                edgecolor="white", linewidth=0.3)

    # Polynomial (deg 2) trend on |lat|
    abs_lat = np.abs(lat_m)
    try:
        coef = np.polyfit(abs_lat, eta_m, 2)
        xs = np.linspace(-65, 65, 200)
        ys = np.polyval(coef, np.abs(xs))
        axC.plot(xs, ys, color=CRE_LW_COLOR, linewidth=1.4,
                 label="poly(|lat|, deg=2)")
    except Exception:
        pass

    # Regional medians
    regions = [
        ("Tropical (|lat|<23.5)", np.abs(lat_m) < 23.5,  "#d9a520"),
        ("Temperate (23.5-50)",   (np.abs(lat_m) >= 23.5) & (np.abs(lat_m) < 50), "#2d6a4f"),
        ("Boreal (>=50)",         np.abs(lat_m) >= 50, "#3a6a8a"),
    ]
    ytxt = 0.97
    for label, m, color in regions:
        if m.sum() == 0:
            continue
        rmed = np.median(eta_m[m])
        axC.text(0.02, ytxt,
                 f"{label}: median $\\eta$ = {rmed:.1f}% (N={m.sum()})",
                 transform=axC.transAxes, fontsize=7.5,
                 color=color, va="top", ha="left", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                           edgecolor="none", alpha=0.75))
        ytxt -= 0.065

    axC.axhline(GEOMETRIC_BOUND_PCT, color=CRE_LW_COLOR,
                linewidth=1.0, linestyle="--", alpha=0.7)
    axC.set_xlabel("Latitude (deg)")
    axC.set_ylabel(r"$\eta$ (%)")
    axC.set_xlim(-65, 75)
    axC.set_ylim(0, 150)
    axC.legend(loc="lower right", fontsize=8, frameon=True, framealpha=0.9)
    axC.set_title(r"$\eta$ vs latitude", fontsize=10)
    panel_label(axC, "(c)")

    save(fig, "fig3_global_consistency")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
# FIGURE 5 — CRE_LW vs CAPE (19 regions)
# ══════════════════════════════════════════════════════════════════════════════
# Caption:
# "Figure 5. Convective-depth regulation of the CRE_SW/CRE_LW partition.
#  (a) CRE_LW scales linearly with CAPE (R^2 = 0.74, p = 2.4e-6,
#  slope = 0.032 W m-2 per J kg-1; 95% confidence band shown).
#  (b) CRE_LW/|CRE_SW| ratio shifts from ~0.60 (shallow coastal convection)
#  to ~0.86 (deep interior convection). This regulation is the physical
#  mechanism underlying the geometric bound on eta."
REGIONS = {
    # Tropical forests
    "Amazon Coast":    {"lat": (-5, 0),   "lon": (-50, -45)},
    "Amazon East":     {"lat": (-5, 0),   "lon": (-55, -50)},
    "Amazon Central":  {"lat": (-5, 0),   "lon": (-60, -55)},
    "Amazon West":     {"lat": (-5, 0),   "lon": (-65, -60)},
    "Amazon Interior": {"lat": (-5, 0),   "lon": (-70, -65)},
    "Amazon Andes":    {"lat": (-5, 0),   "lon": (-75, -70)},
    "Congo West":      {"lat": (-3, 2),   "lon": (15, 20)},
    "Congo Central":   {"lat": (-3, 2),   "lon": (20, 25)},
    "Congo East":      {"lat": (-3, 2),   "lon": (25, 30)},
    "Borneo West":     {"lat": (-3, 2),   "lon": (108, 113)},
    "Borneo East":     {"lat": (-3, 2),   "lon": (113, 118)},
    # Temperate
    "SE USA":          {"lat": (30, 35),  "lon": (-90, -85)},
    "W Europe":        {"lat": (45, 50),  "lon": (0, 5)},
    "E China":         {"lat": (25, 30),  "lon": (110, 115)},
    # Subtropical
    "N Africa Sahel":  {"lat": (10, 15),  "lon": (-5, 5)},
    "C Australia":     {"lat": (-25, -20),"lon": (130, 140)},
    # Oceanic
    "Trop W Atlantic": {"lat": (-5, 5),   "lon": (-35, -25)},
    "Trop E Pacific":  {"lat": (-5, 5),   "lon": (-120, -110)},
    "Indian Ocean":    {"lat": (-10, 0),  "lon": (70, 80)},
}


def ceres_lon_360(lon):
    return lon % 360


def extract_ceres(ds, lat_range, lon_range):
    lmin, lmax = ceres_lon_360(lon_range[0]), ceres_lon_360(lon_range[1])
    if lmin > lmax:
        mask = (ds.lon >= lmin) | (ds.lon <= lmax)
    else:
        mask = (ds.lon >= lmin) & (ds.lon <= lmax)
    return ds.sel(lat=slice(lat_range[0], lat_range[1])).where(mask, drop=True)


def extract_era5(ds, lat_range, lon_range):
    lat_min, lat_max = lat_range
    if ds.latitude[0] > ds.latitude[-1]:
        region = ds.sel(latitude=slice(lat_max, lat_min))
    else:
        region = ds.sel(latitude=slice(lat_min, lat_max))
    return region.sel(longitude=slice(lon_range[0], lon_range[1]))


def gather_region_cre_cape():
    """Return DataFrame with region, CAPE, CRE_LW, CRE_SW."""
    import xarray as xr
    print(f"  opening CERES: {CERES_PATH.name}")
    ceres = xr.open_dataset(CERES_PATH)
    print(f"  opening ERA5 CAPE: {ERA5_CAPE.name}")
    era5 = xr.open_dataset(ERA5_CAPE)

    rows = []
    for name, c in REGIONS.items():
        try:
            cs = extract_ceres(ceres, c["lat"], c["lon"])
            es = extract_era5(era5, c["lat"], c["lon"])
            cape = float(es["cape"].mean())
            cre_lw = float(cs["toa_cre_lw_mon"].mean())
            cre_sw = float(cs["toa_cre_sw_mon"].mean())
            rows.append({"region": name, "cape": cape,
                         "cre_lw": cre_lw, "cre_sw": cre_sw})
            print(f"    {name:20s} CAPE={cape:6.0f}  "
                  f"CRE_LW={cre_lw:+6.1f}  CRE_SW={cre_sw:+6.1f}")
        except Exception as ex:
            print(f"    {name}: ERROR {ex}")
    return pd.DataFrame(rows)


def build_fig5(df_regions):
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.5, 5.0),
                                    gridspec_kw=dict(wspace=0.28))

    cape = df_regions["cape"].values
    cre_lw = df_regions["cre_lw"].values
    cre_sw = df_regions["cre_sw"].values

    # ── Panel (a): CRE_LW vs CAPE with OLS + 95% CI band ───────────────
    slope, intercept, r, p, se = stats.linregress(cape, cre_lw)
    x_fit = np.linspace(cape.min() * 0.8, cape.max() * 1.05, 200)
    y_fit = intercept + slope * x_fit

    # 95% CI band for mean response
    n = len(cape)
    x_mean = cape.mean()
    ss_x = np.sum((cape - x_mean) ** 2)
    resid = cre_lw - (intercept + slope * cape)
    rmse = np.sqrt(np.sum(resid ** 2) / (n - 2))
    t_crit = stats.t.ppf(0.975, df=n - 2)
    se_mean = rmse * np.sqrt(1.0 / n + (x_fit - x_mean) ** 2 / ss_x)
    ci = t_crit * se_mean

    axA.fill_between(x_fit, y_fit - ci, y_fit + ci,
                     color=CRE_LW_COLOR, alpha=0.18,
                     label="95% CI")
    axA.plot(x_fit, y_fit, color=CRE_LW_COLOR, linewidth=1.8,
             label=f"OLS: slope = {slope:.3f} W m$^{{-2}}$ / J kg$^{{-1}}$")
    axA.scatter(cape, cre_lw, s=55, color=CRE_LW_COLOR,
                edgecolor="black", linewidth=0.6, zorder=3)

    # Use adjustText for automatic non-overlapping label placement.
    from adjustText import adjust_text
    texts_a = []
    for _, row in df_regions.iterrows():
        texts_a.append(axA.text(row["cape"], row["cre_lw"], row["region"],
                                fontsize=5.5, color="0.2"))
    adjust_text(
        texts_a, ax=axA,
        arrowprops=dict(arrowstyle="-", color="0.55", lw=0.5, alpha=0.7),
        expand=(1.15, 1.35),
        force_text=(0.5, 0.9),
        force_points=(0.4, 0.7),
    )

    axA.set_xlabel(r"CAPE (J kg$^{-1}$)")
    axA.set_ylabel(r"CRE$_{\mathrm{LW}}$ (W m$^{-2}$)")
    axA.set_title(r"CRE$_{\mathrm{LW}}$ scales with CAPE", fontsize=11)
    axA.text(0.03, 0.97,
             f"$R^2$ = {r**2:.2f}\n$p$ = {p:.1e}\nN = {n} regions",
             transform=axA.transAxes, va="top", ha="left", fontsize=9,
             bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                       edgecolor="0.7", linewidth=0.6, alpha=0.95))
    axA.legend(loc="lower right", fontsize=8, frameon=True)
    axA.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)
    panel_label(axA, "(a)")

    # ── Panel (b): CRE_LW / |CRE_SW| vs CAPE ───────────────────────────
    ratio = cre_lw / np.abs(cre_sw)
    axB.scatter(cape, ratio, s=55, color=CRE_NET_COLOR,
                edgecolor="black", linewidth=0.6, zorder=3)
    # Fit a simple saturating curve via OLS on log(cape)
    try:
        mask = cape > 0
        lc = np.log(cape[mask])
        rb = ratio[mask]
        s2, i2, r2, _, _ = stats.linregress(lc, rb)
        xs = np.linspace(cape[mask].min() * 0.9, cape[mask].max() * 1.05, 200)
        ys = i2 + s2 * np.log(xs)
        axB.plot(xs, ys, color=CRE_NET_COLOR, linewidth=1.6,
                 label=f"log fit ($R^2$={r2**2:.2f})")
    except Exception:
        pass

    axB.axhline(0.60, color="0.5", linewidth=0.8, linestyle=":",
                label="Shallow coastal ~0.60")
    axB.axhline(0.86, color="0.5", linewidth=0.8, linestyle="--",
                label="Deep interior ~0.86")

    # Use adjustText for automatic non-overlapping label placement.
    texts_b = []
    for _, row in df_regions.iterrows():
        texts_b.append(axB.text(row["cape"], row["cre_lw"] / abs(row["cre_sw"]),
                                row["region"], fontsize=5.5, color="0.2"))
    adjust_text(
        texts_b, ax=axB,
        arrowprops=dict(arrowstyle="-", color="0.55", lw=0.5, alpha=0.7),
        expand=(1.15, 1.35),
        force_text=(0.5, 0.9),
        force_points=(0.4, 0.7),
    )

    axB.set_xlabel(r"CAPE (J kg$^{-1}$)")
    axB.set_ylabel(r"CRE$_{\mathrm{LW}}$ / $|$CRE$_{\mathrm{SW}}|$")
    axB.set_title("Convective-depth regulation of SW/LW partition", fontsize=11)
    axB.legend(loc="lower right", fontsize=8, frameon=True)
    axB.grid(True, linestyle=":", linewidth=0.5, alpha=0.6)
    panel_label(axB, "(b)")

    save(fig, "fig5_cape_cre_lw")
    plt.close(fig)

    # Report regression stats (match v4 caption)
    print(f"\n  Fig 5 regression: slope = {slope:.4f} W m-2 / J kg-1, "
          f"R^2 = {r**2:.3f}, p = {p:.2e}, N = {n}")


# ══════════════════════════════════════════════════════════════════════════════
def main():
    print("=" * 72)
    print("Paper 6 v4 figure build (Figures 2, 3, 5)")
    print("=" * 72)
    print("\nLoading site data...")
    df = load_sites()
    print(f"  {len(df)} sites with valid eta")
    eta_med = np.median(df["eta_pct"])
    eta_lo, eta_hi = bootstrap_ci(df["eta_pct"].values)
    print(f"  Global median eta = {eta_med:.2f}%  "
          f"[95% CI: {eta_lo:.2f}-{eta_hi:.2f}%]")

    print("\nBuilding Figure 2 ...")
    build_fig2(df)

    print("\nBuilding Figure 3 ...")
    build_fig3(df)

    print("\nBuilding Figure 5 ...")
    df_regions = gather_region_cre_cape()
    df_regions.to_csv(OUT_DIR / "fig5_region_data.csv", index=False)
    build_fig5(df_regions)

    print("\nDone. Outputs in:", OUT_DIR)


if __name__ == "__main__":
    main()
