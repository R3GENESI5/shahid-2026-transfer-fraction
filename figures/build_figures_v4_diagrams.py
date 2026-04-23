"""
Paper 6 v4 — Diagrammatic figures (Fig 1 and Fig 4).

Fig 1: Three-stream decomposition at BR-Sa1 (Tapajos, Amazon).
       Matplotlib rebuild (Rectangle + FancyArrow), consistent with
       other v4 figures. No Bunyard/CCQ framing.

Fig 4: Study regions on annual-mean CRE_net (CERES EBAF Ed4.2) map.
       Reads the CERES NetCDF from paper_1_alpha_beta if present,
       else emits a placeholder with the intended layout and an
       inline README documenting the required data.

Outputs (PDF + PNG at 300 DPI) to figures_v4/.
"""
from __future__ import annotations

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

# ── Shared style ─────────────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial'],
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'axes.linewidth': 0.8,
    'lines.linewidth': 1.5,
})

# Paper-6 v4 palette
C_SW  = '#1f77b4'   # blue   — CRE_SW
C_LW  = '#d62728'   # red    — CRE_LW
C_NET = '#2ca02c'   # green  — CRE_net
C_K   = '#000000'   # black  — neutral / TOA line
C_FOREST = '#1a6e3a'
C_GRAY = '#808080'
C_GRAY_L = '#d0d0d0'
C_SOLAR = '#f2a900'

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(OUT_DIR, exist_ok=True)


def save(fig, stem):
    pdf_path = os.path.join(OUT_DIR, f"{stem}.pdf")
    png_path = os.path.join(OUT_DIR, f"{stem}.png")
    fig.savefig(pdf_path)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print(f"  Saved: {pdf_path}")
    print(f"  Saved: {png_path}")


# ════════════════════════════════════════════════════════════════════
# FIGURE 1 — Three-stream decomposition at BR-Sa1
# ════════════════════════════════════════════════════════════════════
def build_fig1():
    print("Figure 1: three-stream decomposition at BR-Sa1 ...")
    fig = plt.figure(figsize=(6.5, 5.0))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_axis_off()

    # ── Title / subtitle ────────────────────────────────────────────
    ax.text(5.0, 9.55, "Three-stream decomposition at BR-Sa1",
            ha='center', va='center', fontsize=13, fontweight='bold')
    ax.text(5.0, 9.15,
            "FLUXNET + CERES EBAF Ed4.2  |  2000\u20132024",
            ha='center', va='center', fontsize=9, color='#555555')

    # ── TOA line ────────────────────────────────────────────────────
    y_toa = 8.55
    ax.plot([0.4, 9.6], [y_toa, y_toa], color=C_GRAY, lw=1.0, ls='--')
    ax.text(9.62, y_toa, "TOA", ha='left', va='center',
            fontsize=8, color=C_GRAY)

    # ── Three stream boxes ──────────────────────────────────────────
    box_spec = [
        dict(cx=1.85, color=C_SW,  fill='#e8f1fa',
             stream="STREAM 1", name="Cloud albedo",
             var="CRE$_{SW}$", val="\u221252.3 W m$^{-2}$",
             sub="Reflected sunlight"),
        dict(cx=5.00, color=C_LW,  fill='#fbe8e8',
             stream="STREAM 2", name="LW trapping",
             var="CRE$_{LW}$", val="+41.1 W m$^{-2}$",
             sub="Trapped outgoing IR"),
        dict(cx=8.15, color=C_NET, fill='#e7f3e7',
             stream="STREAM 3", name="Net TOA exit",
             var="CRE$_{net}$", val="\u221211.2 W m$^{-2}$",
             sub=r"$\eta$ = 11.2 / 87.1 = 12.9%"),
    ]
    box_w, box_h = 2.3, 2.1
    box_top = 7.95
    box_bot = box_top - box_h
    for b in box_spec:
        x0 = b['cx'] - box_w / 2
        patch = FancyBboxPatch((x0, box_bot), box_w, box_h,
                               boxstyle="round,pad=0.02,rounding_size=0.12",
                               linewidth=1.4, edgecolor=b['color'],
                               facecolor=b['fill'])
        ax.add_patch(patch)
        ax.text(b['cx'], box_top - 0.25, b['stream'],
                ha='center', va='center', fontsize=8,
                fontweight='bold', color=b['color'])
        ax.text(b['cx'], box_top - 0.58, b['name'],
                ha='center', va='center', fontsize=11,
                fontweight='bold', color=b['color'])
        ax.text(b['cx'], box_top - 1.05, b['var'],
                ha='center', va='center', fontsize=10,
                fontweight='bold', color=b['color'])
        ax.text(b['cx'], box_top - 1.42, b['val'],
                ha='center', va='center', fontsize=11,
                fontweight='bold', color=b['color'])
        ax.plot([b['cx'] - box_w/2 + 0.25, b['cx'] + box_w/2 - 0.25],
                [box_top - 1.65, box_top - 1.65],
                color=b['color'], lw=0.6)
        ax.text(b['cx'], box_top - 1.88, b['sub'],
                ha='center', va='center', fontsize=8.5,
                color=b['color'], style='italic')

    # ── Arrows: Stream 1 and 3 upward to TOA ────────────────────────
    for cx, col in [(1.85, C_SW), (8.15, C_NET)]:
        ax.annotate('', xy=(cx, y_toa), xytext=(cx, box_top + 0.02),
                    arrowprops=dict(arrowstyle='-|>', lw=2.0,
                                    color=col, mutation_scale=14))

    # ── Arrow: Stream 2 downward (recycled into atmosphere) ────────
    ax.annotate('', xy=(5.0, 4.65), xytext=(5.0, box_bot - 0.02),
                arrowprops=dict(arrowstyle='-|>', lw=1.8,
                                color=C_LW, mutation_scale=12))
    ax.text(5.15, (box_bot + 4.65) / 2, "recycled",
            ha='left', va='center', fontsize=8,
            color=C_LW, style='italic')

    # ── Solar input arrow (down to Stream 1) ────────────────────────
    ax.annotate('', xy=(1.05, box_top + 0.02), xytext=(1.05, y_toa - 0.05),
                arrowprops=dict(arrowstyle='-|>', lw=1.8,
                                color=C_SOLAR, mutation_scale=12))
    ax.text(0.95, (y_toa + box_top) / 2, "Solar\ninput",
            ha='right', va='center', fontsize=8,
            color=C_SOLAR, fontweight='bold')

    # ── Condensation layer bar ──────────────────────────────────────
    cond_y0, cond_h = 4.20, 0.45
    cond_patch = FancyBboxPatch((0.8, cond_y0), 8.4, cond_h,
                                boxstyle="round,pad=0.02,rounding_size=0.10",
                                linewidth=1.0, edgecolor='#3c8dbc',
                                facecolor='#dff1fb')
    ax.add_patch(cond_patch)
    ax.text(5.0, cond_y0 + cond_h/2,
            "Condensation at cloud level (3\u20136 km)",
            ha='center', va='center', fontsize=9.5,
            fontweight='bold', color='#25678c')

    # ── LE and H arrows from surface to cloud ───────────────────────
    surf_y1 = 1.50
    ax.annotate('', xy=(3.0, cond_y0 - 0.02), xytext=(3.0, surf_y1 + 0.02),
                arrowprops=dict(arrowstyle='-|>', lw=3.0,
                                color=C_SW, mutation_scale=16))
    ax.text(3.2, (cond_y0 + surf_y1) / 2 + 0.15,
            "LE = 87.1 W m$^{-2}$", ha='left', va='center',
            fontsize=9.5, fontweight='bold', color=C_SW)
    ax.text(3.2, (cond_y0 + surf_y1) / 2 - 0.10,
            "(79% of R$_n$)", ha='left', va='center',
            fontsize=8, color=C_SW)

    ax.annotate('', xy=(7.0, cond_y0 - 0.02), xytext=(7.0, surf_y1 + 0.02),
                arrowprops=dict(arrowstyle='-|>', lw=1.8,
                                color=C_LW, mutation_scale=12))
    ax.text(7.2, (cond_y0 + surf_y1) / 2 + 0.05,
            "H = 17.4 W m$^{-2}$ (16%)",
            ha='left', va='center', fontsize=8.5, color=C_LW)

    # ── Surface bar ─────────────────────────────────────────────────
    surf_patch = FancyBboxPatch((0.6, 0.95), 8.8, surf_y1 - 0.95 + 0.05,
                                boxstyle="round,pad=0.02,rounding_size=0.10",
                                linewidth=0, facecolor=C_FOREST)
    ax.add_patch(surf_patch)
    ax.text(5.0, 1.37, "Forest surface (BR-Sa1)",
            ha='center', va='center', fontsize=10,
            fontweight='bold', color='white')
    ax.text(5.0, 1.12, "R$_n$ = 111 W m$^{-2}$",
            ha='center', va='center', fontsize=9, color='white')

    # ── Equation footer ─────────────────────────────────────────────
    ax.plot([0.6, 9.4], [0.70, 0.70], color=C_GRAY_L, lw=0.8)
    ax.text(5.0, 0.42,
            "CRE$_{net}$ = CRE$_{SW}$ + CRE$_{LW}$ = (\u221252.3) + (+41.1) = "
            "\u221211.2 W m$^{-2}$   |   "
            r"$\eta$ = |CRE$_{net}$|/LE = 11.2 / 87.1 = 12.9%",
            ha='center', va='center', fontsize=8.5, color='#333333')

    save(fig, "fig1_three_streams")


# ════════════════════════════════════════════════════════════════════
# FIGURE 4 — Study regions on annual-mean CRE_net map
# ════════════════════════════════════════════════════════════════════
CERES_CANDIDATES = [
    r"D:/Projects/Programme/paper_1_alpha_beta/data/raw/ceres/"
    r"CERES_EBAF_Edition4.2_200003-202407.nc",
    r"D:/Projects/Programme/paper_6_transfer_fraction/data/raw/ceres/"
    r"CERES_EBAF_Edition4.2_200003-202407.nc",
]

BASINS = {
    # (lon_min, lon_max, lat_min, lat_max)
    "Amazon":  (-78, -48,  -18,   5),
    "Congo":   ( 12,  32,   -8,   5),
    "SE Asia": ( 95, 140,  -10,   5),
}


def _load_ceres_cre_net():
    """Return (lons, lats, cre_net_clim 2D array) or None if unavailable."""
    try:
        import xarray as xr
    except ImportError:
        print("  xarray not importable; using placeholder.")
        return None
    for path in CERES_CANDIDATES:
        if os.path.exists(path):
            print(f"  Using CERES file: {path}")
            ds = xr.open_dataset(path)
            # Prefer pre-computed CRE_net; else derive from clr/all sky TOA
            if 'toa_cre_net_mon' in ds.data_vars:
                cre_net = ds['toa_cre_net_mon'].mean(dim='time')
            else:
                needed = ['toa_sw_all_mon', 'toa_lw_all_mon',
                          'toa_sw_clr_c_mon', 'toa_lw_clr_c_mon']
                if not all(v in ds.data_vars for v in needed):
                    # try alt names
                    alt = ['toa_sw_all_mon', 'toa_lw_all_mon',
                           'toa_sw_clr_mon', 'toa_lw_clr_mon']
                    if not all(v in ds.data_vars for v in alt):
                        print("  CERES file lacks expected variables; "
                              f"have {list(ds.data_vars)[:8]}...")
                        return None
                    needed = alt
                sw_all, lw_all, sw_clr, lw_clr = [
                    ds[v].mean(dim='time') for v in needed]
                # CRE_net at TOA (positive = warming Earth):
                #   CRE_net = (SW_clr - SW_all) + (LW_clr - LW_all)
                cre_net = (sw_clr - sw_all) + (lw_clr - lw_all)
            lons = ds['lon'].values
            lats = ds['lat'].values
            data = cre_net.values
            ds.close()
            # Shift to [-180, 180] if needed
            if lons.max() > 180:
                lons_shifted = np.where(lons > 180, lons - 360, lons)
                idx = np.argsort(lons_shifted)
                lons = lons_shifted[idx]
                data = data[:, idx]
            return lons, lats, data
    print("  No CERES file found at known paths; using placeholder.")
    return None


def build_fig4():
    print("Figure 4: study regions on CRE_net map ...")
    try:
        import cartopy.crs as ccrs
        import cartopy.feature as cfeature
        HAS_CARTOPY = True
    except ImportError:
        HAS_CARTOPY = False
        print("  cartopy not available; drawing in plain PlateCarree-equivalent axes.")

    ceres = _load_ceres_cre_net()

    fig = plt.figure(figsize=(7.5, 4.0))
    if HAS_CARTOPY:
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
        ax.set_extent([-100, 150, -30, 30], crs=ccrs.PlateCarree())
        ax.add_feature(cfeature.COASTLINE, lw=0.5, color='#333333')
        ax.add_feature(cfeature.BORDERS, lw=0.3, color='#666666')
        trans = ccrs.PlateCarree()
    else:
        ax = fig.add_subplot(1, 1, 1)
        ax.set_xlim(-100, 150); ax.set_ylim(-30, 30)
        ax.set_aspect('equal')
        trans = ax.transData
        # stub coastline: just an equator line
        ax.axhline(0, color='#cccccc', lw=0.5, ls=':')

    placeholder = False
    if ceres is None:
        placeholder = True
        # synthetic smooth gradient as placeholder
        lons = np.linspace(-180, 180, 361)
        lats = np.linspace(-40, 40, 81)
        LO, LA = np.meshgrid(lons, lats)
        data = -25 * np.exp(-((LA) / 18) ** 2) * np.cos(np.deg2rad(LO) * 0.5)
    else:
        lons, lats, data = ceres

    pcm_kwargs = dict(cmap='RdBu_r', vmin=-60, vmax=20, shading='auto')
    if HAS_CARTOPY:
        pcm_kwargs['transform'] = ccrs.PlateCarree()
    im = ax.pcolormesh(lons, lats, data, **pcm_kwargs)

    # Basin rectangles
    basin_colors = {'Amazon': C_NET, 'Congo': C_LW, 'SE Asia': C_SW}
    for name, (lon0, lon1, lat0, lat1) in BASINS.items():
        rect = Rectangle((lon0, lat0), lon1 - lon0, lat1 - lat0,
                         linewidth=1.8, edgecolor='black',
                         facecolor='none',
                         transform=trans if HAS_CARTOPY else None)
        ax.add_patch(rect)
        label_y = lat1 + 3
        ax.text((lon0 + lon1) / 2, label_y, name,
                ha='center', va='bottom',
                fontsize=10, fontweight='bold', color='black',
                bbox=dict(boxstyle='round,pad=0.25',
                          facecolor='white', edgecolor='black',
                          linewidth=0.6, alpha=0.85),
                transform=trans if HAS_CARTOPY else None)

    # Colorbar
    cb = plt.colorbar(im, ax=ax, orientation='horizontal',
                      pad=0.12, shrink=0.7, aspect=32)
    cb.set_label("Annual-mean CRE$_{net}$ (W m$^{-2}$)", fontsize=10)
    cb.ax.tick_params(labelsize=8)

    # Title
    title = ("Study regions on annual-mean CRE$_{net}$ "
             "(CERES EBAF Ed4.2, 2003\u20132023)")
    if placeholder:
        title += "  [PLACEHOLDER DATA]"
    ax.set_title(title, fontsize=11, fontweight='bold', pad=8)

    if HAS_CARTOPY:
        gl = ax.gridlines(draw_labels=True, lw=0.3,
                          color='gray', alpha=0.5)
        gl.top_labels = False
        gl.right_labels = False
    else:
        ax.set_xlabel("Longitude (\u00b0)")
        ax.set_ylabel("Latitude (\u00b0)")

    save(fig, "fig4_study_regions")

    if placeholder:
        readme = os.path.join(OUT_DIR, "fig4_study_regions_README.txt")
        with open(readme, 'w', encoding='utf-8') as f:
            f.write(
                "fig4_study_regions — DATA REQUIRED\n"
                "====================================\n\n"
                "The current PDF/PNG uses a synthetic gradient placeholder.\n"
                "To produce the final figure, make the CERES EBAF Ed4.2\n"
                "monthly file available at one of:\n\n"
                + "\n".join(f"  - {p}" for p in CERES_CANDIDATES)
                + "\n\nRequired variables (any of these two paths works):\n"
                "  (a) toa_cre_net_mon   (pre-computed net CRE)\n"
                "  (b) toa_sw_all_mon, toa_lw_all_mon,\n"
                "      toa_sw_clr_c_mon (or toa_sw_clr_mon),\n"
                "      toa_lw_clr_c_mon (or toa_lw_clr_mon)\n"
                "      from which CRE_net = (SW_clr - SW_all) + (LW_clr - LW_all).\n\n"
                "Then rerun:  python build_figures_v4_diagrams.py\n"
            )
        print(f"  Placeholder README written: {readme}")


if __name__ == "__main__":
    build_fig1()
    build_fig4()
    print("Done.")
