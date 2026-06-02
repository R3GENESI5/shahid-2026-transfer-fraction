"""
Paper 6 v5: unified figure builder.

Produces ALL 9 figures in two variants each:
  figN_NAME_titled.{pdf,png}    - with figure suptitle + panel titles
  figN_NAME_notitled.{pdf,png}  - panel labels (a)(b)(c) only, no titles

Layout improvements vs v4:
  * fig3: reflow 1x3 -> 1+2 (histogram on top, biome bars + lat scatter below)
          Fix stale "Distribution across 314 sites" title -> 341
          Reposition panel (c) legend to avoid polynomial-fit overlap
  * fig5: use adjustText to resolve severe region-label overlap
  * fig6: reflow 1x3 -> 1+2 (Amazon on top, Congo + SE Asia below)
  * fig1: redrawn in matplotlib as a clean three-streams schematic
          (replaces Word-imported media/media/image1.png)

Data: site_summary_v5_n342.csv (341 sites)
Output: ./figures/
"""
from __future__ import annotations
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.patches import Rectangle, FancyBboxPatch, FancyArrowPatch
import xarray as xr

try:
    from adjustText import adjust_text
    HAVE_ADJUSTTEXT = True
except ImportError:
    HAVE_ADJUSTTEXT = False
    print("[warn] adjustText not available; fig5 will fall back to manual positioning")

# ── Configuration ─────────────────────────────────────────────────────────────
HERE = Path(__file__).resolve().parent
DATA_CSV = HERE / "site_summary_v5_n342.csv"
CERES_NC = Path(
    "D:/Projects/Programme/paper_1_alpha_beta/data/raw/ceres/"
    "CERES_EBAF_Edition4.2_200003-202407.nc"
)
ERA5_CAPE = Path(
    "D:/chagpt export/pace-alpha-coefficients/data/raw/era5_extracted/"
    "data_stream-moda_stepType-avgua.nc"
)
OUT = HERE / "figures"
OUT.mkdir(parents=True, exist_ok=True)

# ── Style ─────────────────────────────────────────────────────────────────────
CRE_SW_COLOR = "#1f77b4"
CRE_LW_COLOR = "#d62728"
CRE_NET_COLOR = "#2ca02c"
SURFACE_BLUE = "#3a5a7a"
TROP_COLOR = "#d9a520"
TEMP_COLOR = "#2d6a4f"
BOR_COLOR = "#3a6a8a"
GEOMETRIC_BOUND_PCT = 35.0

BIOME_COLORS = {
    "Forest": "#2d6a4f",
    "Grassland": "#d9a520",
    "Cropland": "#a8732d",
    "Savanna": "#c8a04d",
    "Shrubland": "#a8694d",
    "Wetland": "#3d7a8a",
    "Barren": "#8a8a8a",
}

mpl.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 8.5,
    "axes.linewidth": 0.8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.bbox": "tight",
    "savefig.dpi": 300,
    "pdf.fonttype": 42,
})


def panel_label(ax, text, x=-0.12, y=1.04):
    """Bold panel label (a)(b)(c) at upper-left of axes."""
    ax.text(x, y, text, transform=ax.transAxes, fontsize=12,
            fontweight="bold", va="bottom", ha="left")


def save_both(fig, stem, suptitle=None, panel_titles=None):
    """Save figure twice: with title(s) and without.

    suptitle: figure-level title string, or None.
    panel_titles: dict mapping ax -> title string (only set in titled variant).
    """
    # Titled version
    if suptitle is not None:
        fig.suptitle(suptitle, fontsize=12.5, fontweight="bold", y=0.995)
    if panel_titles:
        for ax, t in panel_titles.items():
            ax.set_title(t, fontsize=10)
    fig.savefig(OUT / f"{stem}_titled.pdf")
    fig.savefig(OUT / f"{stem}_titled.png", dpi=300)

    # Notitled version: strip titles
    if suptitle is not None:
        fig._suptitle.remove()
    if panel_titles:
        for ax in panel_titles:
            ax.set_title("")
    fig.savefig(OUT / f"{stem}_notitled.pdf")
    fig.savefig(OUT / f"{stem}_notitled.png", dpi=300)
    print(f"  wrote {stem}_titled / {stem}_notitled")


def bootstrap_ci(x, n_boot=10000, rng=None):
    """Bootstrap 95% CI on the median."""
    rng = rng or np.random.default_rng(42)
    x = np.asarray(x)
    x = x[np.isfinite(x)]
    if len(x) < 2:
        return (np.nan, np.nan)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    meds = np.median(x[idx], axis=1)
    return float(np.percentile(meds, 2.5)), float(np.percentile(meds, 97.5))


# ═══════════════════════════════════════════════════════════════════════════
# Figure 1: three-streams schematic (matplotlib, adapted from build_figures_v4_diagrams)
# ═══════════════════════════════════════════════════════════════════════════
C_SW = CRE_SW_COLOR
C_LW = CRE_LW_COLOR
C_NET = CRE_NET_COLOR
C_GRAY = "#888888"
C_GRAY_L = "#cccccc"
C_FOREST = "#2d6a4f"
C_SOLAR = "#d9a520"


def build_fig1_proper(include_internal_title=True):
    """Three-stream decomposition at BR-Sa1.

    If include_internal_title is True: title rendered inside the axes at the top
    (matches existing fig1_three_streams.png).
    If False: blank top area; suptitle (if any) provides the figure-level title.
    """
    fig = plt.figure(figsize=(6.5, 5.0))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.set_axis_off()

    if include_internal_title:
        ax.text(5.0, 9.55, "Three-stream decomposition at BR-Sa1",
                ha='center', va='center', fontsize=13, fontweight='bold')
        ax.text(5.0, 9.15,
                "FLUXNET + CERES EBAF Ed4.2  |  2000-2024",
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
             var="CRE$_{SW}$", val="−52.3 W m$^{-2}$",
             sub="Reflected sunlight"),
        dict(cx=5.00, color=C_LW,  fill='#fbe8e8',
             stream="STREAM 2", name="LW trapping",
             var="CRE$_{LW}$", val="+41.1 W m$^{-2}$",
             sub="Trapped outgoing IR"),
        dict(cx=8.15, color=C_NET, fill='#e7f3e7',
             stream="STREAM 3", name="Net TOA exit",
             var="CRE$_{net}$", val="−11.2 W m$^{-2}$",
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

    # ── Arrow: Stream 2 downward (recycled) ─────────────────────────
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
            "Condensation at cloud level (3-6 km)",
            ha='center', va='center', fontsize=9.5,
            fontweight='bold', color='#25678c')

    # ── LE and H arrows ─────────────────────────────────────────────
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
            "CRE$_{net}$ = CRE$_{SW}$ + CRE$_{LW}$ = (−52.3) + (+41.1) = "
            "−11.2 W m$^{-2}$   |   "
            r"$\eta$ = |CRE$_{net}$|/LE = 11.2 / 87.1 = 12.9%",
            ha='center', va='center', fontsize=8.5, color='#333333')

    return fig


def build_fig1_sankey(include_internal_title=True):
    """
    Three-stream decomposition as an atmospheric-column schematic.

    Vertical cross-section with TOA top, cloud level (3-6 km), and forest
    surface (BR-Sa1) at bottom. All five energy fluxes drawn as arrows with
    line widths strictly proportional to magnitude (W/m^2), scaled to
    LE = 87.1 as the reference maximum.

    CRE_LW is drawn as a curved arrow returning into the atmosphere
    (depicting trapped longwave, not radiation lost to space).

    Font: Arial/Helvetica 9 pt, no bold (scoped to this function via rc_context).
    """
    from matplotlib.patches import FancyArrowPatch, Ellipse

    fig_ctx = mpl.rc_context({
        "font.family": ["Arial", "Helvetica", "sans-serif"],
        "font.size": 9,
    })
    fig_ctx.__enter__()
    fig, ax = plt.subplots(figsize=(10.0, 6.6))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    # ─── Flux magnitudes (W/m^2) → proportional line widths ─────────
    fluxes = {"LE": 87.1, "H": 17.4, "CRE_SW": 52.3,
              "CRE_LW": 41.1, "CRE_net": 11.2}
    LW_MAX = 9.0   # max arrow linewidth (pt) for the largest flux (LE)
    LW_MIN = 1.5   # min linewidth floor so smallest flux stays visible
    REF = max(fluxes.values())
    def lw(name):
        return max(LW_MIN, LW_MAX * fluxes[name] / REF)

    # Internal title removed; titled variant uses fig.suptitle (above axes)
    # to avoid overlap with the TOA stream labels at y > 9.

    # ─── Altitude band labels and reference lines ───────────────────
    y_toa = 8.55
    y_cloud_top = 6.30
    y_cloud_bot = 5.30
    y_surface = 1.35
    y_surface_top = 1.55

    # TOA line + centered label (between the three TOA stream arrows)
    ax.plot([0.4, 9.6], [y_toa, y_toa], color="#666666", lw=1.0, ls="--",
            zorder=1)
    ax.text(5.0, y_toa + 0.12, "TOA  (top of atmosphere)",
            ha="center", va="bottom",
            fontsize=9, color="#444", style="italic", zorder=5,
            bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                      edgecolor="none", alpha=0.95))

    # Cloud band: single rounded rectangle
    cloud_patch = FancyBboxPatch(
        (1.0, y_cloud_bot), 8.0, y_cloud_top - y_cloud_bot,
        boxstyle="round,pad=0.02,rounding_size=0.18",
        facecolor="#cfdef0", edgecolor="#5a7a9a",
        linewidth=1.1, alpha=0.88, zorder=2)
    ax.add_patch(cloud_patch)
    ax.text(5.0, (y_cloud_top + y_cloud_bot)/2,
            "Condensation at cloud level (3 - 6 km)",
            ha="center", va="center", fontsize=9,
            color="#25678c", zorder=5)

    # Surface (forest)
    ax.add_patch(Rectangle((0.4, y_surface - 0.4),
                           9.2, y_surface_top - y_surface + 0.4,
                           facecolor=C_FOREST, edgecolor="none", zorder=2))
    ax.text(5.0, y_surface + 0.08, "Forest surface (BR-Sa1)",
            ha="center", va="center", color="white",
            fontsize=9, zorder=5)
    ax.text(5.0, y_surface - 0.28, r"$R_n$ = 111 W m$^{-2}$",
            ha="center", va="center", color="white",
            fontsize=9, zorder=5)

    # ─── Surface-to-cloud fluxes (LE, H) ────────────────────────────
    # LE: thick blue arrow, dominant
    le_arrow = FancyArrowPatch(
        (3.0, y_surface_top + 0.05), (3.0, y_cloud_bot - 0.05),
        arrowstyle="-|>", mutation_scale=22,
        color=C_SW, lw=lw("LE"), zorder=4)
    ax.add_patch(le_arrow)
    ax.text(3.25, (y_surface_top + y_cloud_bot)/2 + 0.20,
            "LE = 87.1 W m$^{-2}$", ha="left", va="center",
            fontsize=9, color=C_SW, zorder=5)
    ax.text(3.25, (y_surface_top + y_cloud_bot)/2 - 0.15,
            "(79% of $R_n$, dominant)", ha="left", va="center",
            fontsize=9, color=C_SW, zorder=5)

    # H: thin red arrow
    h_arrow = FancyArrowPatch(
        (7.0, y_surface_top + 0.05), (7.0, y_cloud_bot - 0.05),
        arrowstyle="-|>", mutation_scale=14,
        color=C_LW, lw=lw("H"), zorder=4)
    ax.add_patch(h_arrow)
    ax.text(7.25, (y_surface_top + y_cloud_bot)/2 + 0.05,
            "H = 17.4 W m$^{-2}$ (16%)", ha="left", va="center",
            fontsize=9, color=C_LW, zorder=5)

    # ─── TOA streams from cloud upward ──────────────────────────────
    # Stream 1: CRE_SW (reflected solar going UP through TOA, escapes to space)
    sw_arrow = FancyArrowPatch(
        (2.0, y_cloud_top + 0.05), (2.0, y_toa + 0.95),
        arrowstyle="-|>", mutation_scale=18,
        color=C_SW, lw=lw("CRE_SW"), zorder=4)
    ax.add_patch(sw_arrow)
    ax.text(2.0, y_toa + 1.15,
            r"CRE$_{\mathrm{SW}}$ = $-$52.3 W m$^{-2}$",
            ha="center", va="bottom", fontsize=9, color=C_SW, zorder=5)
    ax.text(2.0, y_toa + 0.95 - 0.02, "reflected sunlight (cooling)",
            ha="center", va="top", fontsize=9,
            color=C_SW, style="italic", zorder=5)

    # Stream 2: CRE_LW — curved arrow showing LW that leaves cloud upward
    # but is re-trapped within the atmosphere (does not escape to space).
    # Smaller curve so it stays compact in the atmosphere band between
    # cloud (6.30) and TOA line (8.55), leaving headroom for labels.
    lw_arrow = FancyArrowPatch(
        (4.7, y_cloud_top + 0.05),    # tail: cloud top, slight left of centre
        (5.5, y_cloud_top + 0.10),    # head: just above cloud, pointing back down
        arrowstyle="-|>", mutation_scale=16,
        connectionstyle="arc3,rad=-1.1",
        color=C_LW, lw=lw("CRE_LW"), zorder=4)
    ax.add_patch(lw_arrow)
    # Labels positioned high enough to clear the arc peak (≈ y 7.0).
    # White bbox for visibility against TOA dashed line.
    ax.text(5.10, 8.10,
            r"CRE$_{\mathrm{LW}}$ = $+$41.1 W m$^{-2}$",
            ha="center", va="bottom", fontsize=9, color=C_LW, zorder=5,
            bbox=dict(boxstyle="round,pad=0.20", facecolor="white",
                      edgecolor="none", alpha=0.95))
    ax.text(5.10, 8.06, "trapped longwave (warming)",
            ha="center", va="top", fontsize=9,
            color=C_LW, style="italic", zorder=5,
            bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                      edgecolor="none", alpha=0.95))

    # Stream 3: CRE_net (net residual cooling escaping to space)
    net_arrow = FancyArrowPatch(
        (8.0, y_cloud_top + 0.05), (8.0, y_toa + 0.95),
        arrowstyle="-|>", mutation_scale=15,
        color=C_NET, lw=lw("CRE_net"), zorder=4)
    ax.add_patch(net_arrow)
    ax.text(8.0, y_toa + 1.15,
            r"CRE$_{\mathrm{net}}$ = $-$11.2 W m$^{-2}$",
            ha="center", va="bottom", fontsize=9, color=C_NET, zorder=5)
    ax.text(8.0, y_toa + 0.95 - 0.02, "net TOA cooling (residual)",
            ha="center", va="top", fontsize=9,
            color=C_NET, style="italic", zorder=5)

    # ─── Width-legend (arrow-width scale key) ───────────────────────
    legend_x = 0.55
    legend_y = 4.3
    ax.text(legend_x, legend_y + 0.55, "Arrow width $\\propto$ W m$^{-2}$",
            fontsize=9, color="#333", zorder=5)
    # Three reference widths
    for i, (val, label) in enumerate([(87.1, "87"),
                                       (40.0, "40"),
                                       (11.2, "11")]):
        ref_y = legend_y - i * 0.30
        ax.plot([legend_x + 0.10, legend_x + 0.75],
                [ref_y, ref_y],
                color="#666", linewidth=max(LW_MIN, LW_MAX * val / REF))
        ax.text(legend_x + 0.85, ref_y, label,
                fontsize=9, color="#444", va="center", zorder=5)

    # ─── Equation footer ────────────────────────────────────────────
    ax.plot([0.5, 9.5], [0.55, 0.55], color="#cccccc", lw=0.7)
    ax.text(5.0, 0.25,
            r"CRE$_{\mathrm{net}}$ = CRE$_{\mathrm{SW}}$ + CRE$_{\mathrm{LW}}$"
            r" = ($-$52.3) + ($+$41.1) = $-$11.2 W m$^{-2}$"
            r"      $\eta$ = $|$CRE$_{\mathrm{net}}|$ / LE = 11.2 / 87.1 = 12.9%",
            ha="center", va="center", fontsize=9, color="#222")

    fig_ctx.__exit__(None, None, None)
    return fig


def build_fig1():
    # Titled variant: suptitle above the axes (no overlap with TOA labels)
    fig = build_fig1_sankey(include_internal_title=False)
    fig.suptitle("Three-stream decomposition at BR-Sa1\n"
                 "FLUXNET + CERES EBAF Ed4.2  |  2000-2024",
                 fontsize=12.5, fontweight="bold", y=0.99)
    fig.savefig(OUT / "fig1_three_streams_titled.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig1_three_streams_titled.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    # Notitled variant: same axes, no suptitle
    fig = build_fig1_sankey(include_internal_title=False)
    fig.savefig(OUT / "fig1_three_streams_notitled.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fig1_three_streams_notitled.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  wrote fig1_three_streams_titled / fig1_three_streams_notitled (Sankey-style)")


# OLD BROKEN BUILD (kept commented for reference)
def build_fig1_BROKEN():
    fig, ax = plt.subplots(figsize=(9.0, 5.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")
    TXT_Z = 10  # text z-order, above all patches

    # TOA line
    ax.axhline(8.9, color="#666666", linewidth=0.7, linestyle="--", alpha=0.7,
               zorder=2)
    ax.text(9.95, 8.97, "TOA", fontsize=8, color="#666666", style="italic",
            ha="right", va="bottom", zorder=TXT_Z)

    # Surface line
    ax.axhline(1.4, color="#2d6a4f", linewidth=1.5)
    ax.add_patch(Rectangle((0.3, 1.05), 9.4, 0.4, color="#2d6a4f", alpha=0.85, zorder=3))
    ax.text(5.0, 1.25, "Forest surface (BR-Sa1 reference)",
            ha="center", va="center", color="white",
            fontsize=10, fontweight="bold", zorder=TXT_Z)
    ax.text(5.0, 0.85, r"$R_n$ = 111 W m$^{-2}$",
            ha="center", va="top", fontsize=9, color="#2d6a4f", zorder=TXT_Z)

    # Cloud band
    cloud_y_low, cloud_y_high = 4.5, 6.0
    ax.add_patch(Rectangle((0.6, cloud_y_low), 8.8, cloud_y_high - cloud_y_low,
                           facecolor="#bcd0e8", edgecolor="#5a7a9a",
                           linewidth=0.8, alpha=0.85, zorder=2))
    ax.text(5.0, (cloud_y_low + cloud_y_high) / 2,
            "Condensation at cloud level (3-6 km)",
            ha="center", va="center", fontsize=10, fontweight="bold",
            color="#2d4a6a", zorder=TXT_Z)

    # Stream 1 (left) — CRE_SW: cloud albedo, reflected sunlight up
    box1_x, box1_y, box1_w, box1_h = 0.4, 7.1, 2.6, 1.5
    ax.add_patch(FancyBboxPatch((box1_x, box1_y), box1_w, box1_h,
                                boxstyle="round,pad=0.05",
                                facecolor="#d0e4f5", edgecolor=CRE_SW_COLOR,
                                linewidth=1.6, zorder=4))
    ax.text(box1_x + box1_w / 2, box1_y + box1_h - 0.18, "STREAM 1",
            ha="center", va="top", fontsize=8, fontweight="bold",
            color=CRE_SW_COLOR, zorder=TXT_Z)
    ax.text(box1_x + box1_w / 2, box1_y + box1_h - 0.55, "Cloud albedo",
            ha="center", va="top", fontsize=10, fontweight="bold", zorder=TXT_Z)
    ax.text(box1_x + box1_w / 2, box1_y + box1_h - 0.95,
            r"CRE$_{\mathrm{SW}}$ = $-$52.3 W m$^{-2}$",
            ha="center", va="top", fontsize=9, color=CRE_SW_COLOR, zorder=TXT_Z)
    ax.text(box1_x + box1_w / 2, box1_y + 0.18, "Reflected sunlight",
            ha="center", va="bottom", fontsize=8, color="#666", style="italic", zorder=TXT_Z)

    # Stream 2 (center) — CRE_LW: longwave trapping, downward radiation
    box2_x, box2_y, box2_w, box2_h = 3.6, 7.1, 2.8, 1.5
    ax.add_patch(FancyBboxPatch((box2_x, box2_y), box2_w, box2_h,
                                boxstyle="round,pad=0.05",
                                facecolor="#f5d6d6", edgecolor=CRE_LW_COLOR,
                                linewidth=1.6, zorder=4))
    ax.text(box2_x + box2_w / 2, box2_y + box2_h - 0.18, "STREAM 2",
            ha="center", va="top", fontsize=8, fontweight="bold",
            color=CRE_LW_COLOR, zorder=TXT_Z)
    ax.text(box2_x + box2_w / 2, box2_y + box2_h - 0.55, "LW trapping",
            ha="center", va="top", fontsize=10, fontweight="bold", zorder=TXT_Z)
    ax.text(box2_x + box2_w / 2, box2_y + box2_h - 0.95,
            r"CRE$_{\mathrm{LW}}$ = $+$41.1 W m$^{-2}$",
            ha="center", va="top", fontsize=9, color=CRE_LW_COLOR, zorder=TXT_Z)
    ax.text(box2_x + box2_w / 2, box2_y + 0.18, "Trapped outgoing IR",
            ha="center", va="bottom", fontsize=8, color="#666", style="italic", zorder=TXT_Z)

    # Stream 3 (right) — CRE_net: net TOA exit
    box3_x, box3_y, box3_w, box3_h = 7.0, 7.1, 2.6, 1.5
    ax.add_patch(FancyBboxPatch((box3_x, box3_y), box3_w, box3_h,
                                boxstyle="round,pad=0.05",
                                facecolor="#d6e7d6", edgecolor=CRE_NET_COLOR,
                                linewidth=1.6, zorder=4))
    ax.text(box3_x + box3_w / 2, box3_y + box3_h - 0.18, "STREAM 3",
            ha="center", va="top", fontsize=8, fontweight="bold",
            color=CRE_NET_COLOR, zorder=TXT_Z)
    ax.text(box3_x + box3_w / 2, box3_y + box3_h - 0.55, "Net TOA exit",
            ha="center", va="top", fontsize=10, fontweight="bold", zorder=TXT_Z)
    ax.text(box3_x + box3_w / 2, box3_y + box3_h - 0.95,
            r"CRE$_{\mathrm{net}}$ = $-$11.2 W m$^{-2}$",
            ha="center", va="top", fontsize=9, color=CRE_NET_COLOR, zorder=TXT_Z)
    ax.text(box3_x + box3_w / 2, box3_y + 0.18,
            r"$\eta$ = 11.2 / 87.1 = 12.9%",
            ha="center", va="bottom", fontsize=8.5, color=CRE_NET_COLOR,
            fontweight="bold", zorder=TXT_Z)

    # LE arrow from surface to cloud (upward, thick blue)
    ax.annotate("", xy=(3.5, cloud_y_low - 0.05),
                xytext=(3.5, 1.5),
                arrowprops=dict(arrowstyle="->", color=CRE_SW_COLOR,
                                linewidth=2.5), zorder=TXT_Z)
    ax.text(3.65, 3.0, r"LE = 87.1 W m$^{-2}$" + "\n(79% of $R_n$)",
            ha="left", va="center", fontsize=9.5, color=CRE_SW_COLOR,
            fontweight="bold", zorder=TXT_Z)

    # H arrow from surface to atmosphere (upward, thin red)
    ax.annotate("", xy=(6.5, cloud_y_low - 0.05),
                xytext=(6.5, 1.5),
                arrowprops=dict(arrowstyle="->", color=CRE_LW_COLOR,
                                linewidth=1.8), zorder=TXT_Z)
    ax.text(6.65, 3.0, r"H = 17.4 W m$^{-2}$" + "\n(16%)",
            ha="left", va="center", fontsize=9.5, color=CRE_LW_COLOR, zorder=TXT_Z)

    # Up-arrows from cloud to TOA stream boxes
    ax.annotate("", xy=(box1_x + box1_w / 2, box1_y - 0.05),
                xytext=(box1_x + box1_w / 2, cloud_y_high + 0.05),
                arrowprops=dict(arrowstyle="->", color=CRE_SW_COLOR,
                                linewidth=1.8), zorder=TXT_Z)
    ax.annotate("", xy=(box3_x + box3_w / 2, box3_y - 0.05),
                xytext=(box3_x + box3_w / 2, cloud_y_high + 0.05),
                arrowprops=dict(arrowstyle="->", color=CRE_NET_COLOR,
                                linewidth=1.8), zorder=TXT_Z)
    # Stream 2 arrow points DOWN (LW trapping reradiates back)
    ax.annotate("", xy=(box2_x + box2_w / 2, cloud_y_high + 0.05),
                xytext=(box2_x + box2_w / 2, box2_y - 0.05),
                arrowprops=dict(arrowstyle="->", color=CRE_LW_COLOR,
                                linewidth=1.8), zorder=TXT_Z)
    ax.text(box2_x + box2_w / 2 + 0.15, 6.55, "recycled",
            ha="left", va="center", fontsize=8, color=CRE_LW_COLOR,
            style="italic", zorder=TXT_Z)

    # Solar input arrow on far left
    ax.annotate("", xy=(0.2, 8.4), xytext=(0.2, 9.4),
                arrowprops=dict(arrowstyle="->", color="#d9a520", linewidth=2.0), zorder=TXT_Z)
    ax.text(0.35, 8.9, "Solar input", fontsize=8, color="#d9a520",
            fontweight="bold", style="italic", zorder=TXT_Z)

    # Footer equation
    ax.text(5.0, -0.05,
            r"CRE$_{\mathrm{net}}$ = CRE$_{\mathrm{SW}}$ + CRE$_{\mathrm{LW}}$ "
            r"= ($-$52.3) + ($+$41.1) = $-$11.2 W m$^{-2}$"
            "      "
            r"$\eta$ = $|$CRE$_{\mathrm{net}}|$/LE = 11.2 / 87.1 = 12.9%",
            ha="center", va="top", fontsize=8.5, color="#333", zorder=TXT_Z)

    save_both(fig, "fig1_three_streams",
              suptitle=("Three-stream decomposition at BR-Sa1\n"
                        "FLUXNET + CERES EBAF Ed4.2  |  2000-2024"))
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# Figure 2: LE vs CRE_net scatter
# ═══════════════════════════════════════════════════════════════════════════
def build_fig2(df):
    fig, ax = plt.subplots(figsize=(8.0, 5.5))
    df = df.dropna(subset=["mean_LE", "ceres_toa_cre_net_mean"])

    # Per-biome scatter
    for biome in ["Forest", "Grassland", "Cropland", "Savanna", "Shrubland", "Wetland"]:
        sub = df[df["biome_group"] == biome]
        if len(sub) == 0:
            continue
        ax.scatter(sub["mean_LE"], sub["ceres_toa_cre_net_mean"],
                   s=22, alpha=0.72, color=BIOME_COLORS.get(biome, "#888"),
                   edgecolor="white", linewidth=0.3,
                   label=f"{biome} (N={len(sub)})")

    # Tropical EBF overlay (gold markers)
    trop_ebf = df[(df["igbp"] == "EBF") & (df["latitude"].abs() <= 23.5)]
    ax.scatter(trop_ebf["mean_LE"], trop_ebf["ceres_toa_cre_net_mean"],
               s=110, color="#ffd400", edgecolor="black",
               linewidth=0.9, alpha=0.95, zorder=5,
               label=f"Tropical EBF (N={len(trop_ebf)})")

    # Zero line
    ax.axhline(0, color="black", linewidth=0.5, linestyle="--", alpha=0.5)

    # Stats box (top-right, no overlap with data)
    med_eta = df["eta"].median() * 100
    ci_lo, ci_hi = bootstrap_ci(df["eta"].values)
    r = float(np.corrcoef(df["mean_LE"], df["ceres_toa_cre_net_mean"])[0, 1])
    stats_text = (f"Global median $\\eta$ = {med_eta:.1f}%\n"
                  f"[95% CI: {ci_lo*100:.1f}-{ci_hi*100:.1f}%]\n"
                  f"Cross-site r = {r:.3f}")
    ax.text(0.97, 0.97, stats_text, transform=ax.transAxes,
            ha="right", va="top", fontsize=8.5,
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor="#888", alpha=0.92))

    ax.set_xlabel(r"Surface LE (W m$^{-2}$)")
    ax.set_ylabel(r"TOA CRE$_{\mathrm{net}}$ (W m$^{-2}$)")
    ax.legend(loc="lower right", fontsize=7.5, ncol=2,
              frameon=True, framealpha=0.92, borderpad=0.5)
    ax.grid(True, alpha=0.25, linewidth=0.5)

    save_both(fig, "fig2_le_vs_cre_net",
              suptitle=f"Surface LE vs TOA CRE$_{{\\mathrm{{net}}}}$  -  "
                       f"{len(df)} FLUXNET-CERES sites")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# Figure 3: global consistency — REFLOWED to 1+2 layout
# ═══════════════════════════════════════════════════════════════════════════
def build_fig3(df):
    df = df.dropna(subset=["eta"]).copy()
    df["eta_pct"] = df["eta"] * 100

    fig = plt.figure(figsize=(11.0, 7.5))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 1.05],
                  hspace=0.42, wspace=0.30,
                  left=0.07, right=0.97, top=0.93, bottom=0.09)
    axA = fig.add_subplot(gs[0, :])    # Top: histogram, full width
    axB = fig.add_subplot(gs[1, 0])    # Bottom-left: biome bars
    axC = fig.add_subplot(gs[1, 1])    # Bottom-right: latitude scatter

    # ── Panel (a): histogram of eta (top, full width) ──────────────────
    eta = df["eta_pct"].values
    eta_plot = eta[eta <= 150]
    axA.hist(eta_plot, bins=np.arange(0, 151, 5),
             color="#5a7a9a", edgecolor="white", linewidth=0.6)
    axA.axvline(GEOMETRIC_BOUND_PCT, color=CRE_LW_COLOR,
                linewidth=1.8, linestyle="--",
                label=f"Geometric bound (deep convection), $\\eta$ = {GEOMETRIC_BOUND_PCT:.0f}%")
    med = np.median(eta)
    axA.axvline(med, color="black", linewidth=1.4, linestyle="-",
                label=f"Median = {med:.1f}%")
    axA.set_xlabel(r"Transfer fraction $\eta$ = $|$CRE$_{\mathrm{net}}|/$LE (%)")
    axA.set_ylabel("Number of sites")
    axA.set_xlim(0, 150)
    ymax_a = axA.get_ylim()[1]
    axA.set_ylim(0, ymax_a * 1.20)
    axA.legend(loc="upper right", fontsize=9, frameon=True,
               framealpha=0.92, borderpad=0.5)
    panel_label(axA, "(a)", x=-0.055, y=1.03)

    # ── Panel (b): median eta by biome (bottom-left) ───────────────────
    biome_order_raw = ["Forest", "Grassland", "Cropland",
                       "Savanna", "Shrubland", "Wetland"]
    rows = []
    for b in biome_order_raw:
        vals = df.loc[df["biome_group"] == b, "eta_pct"].dropna().values
        if len(vals) == 0:
            continue
        lo, hi = bootstrap_ci(vals)
        rows.append((b, np.median(vals), lo, hi, len(vals)))
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
        axB.text(i, m + (his[i] - meds[i]) + 2.0, f"N={n}",
                 ha="center", va="bottom", fontsize=8.5)
    axB.set_xticks(xpos)
    axB.set_xticklabels(biomes, rotation=18, ha="right", fontsize=9)
    axB.set_ylabel(r"Median $\eta$ (%)")
    axB.set_ylim(0, max(his.max() + 14, 55))
    axB.legend(loc="upper left", fontsize=8.5, frameon=True)
    panel_label(axB, "(b)", x=-0.14, y=1.03)

    # ── Panel (c): eta vs latitude (bottom-right) ──────────────────────
    lat = df["latitude"].values
    eta_c = df["eta_pct"].values
    mask = np.isfinite(lat) & np.isfinite(eta_c) & (eta_c <= 200)
    lat_m = lat[mask]
    eta_m = eta_c[mask]
    axC.scatter(lat_m, eta_m, s=18, alpha=0.55, color=SURFACE_BLUE,
                edgecolor="white", linewidth=0.3)

    # Polynomial trend on |lat|
    abs_lat = np.abs(lat_m)
    coef = np.polyfit(abs_lat, eta_m, 2)
    xs = np.linspace(-65, 65, 200)
    ys = np.polyval(coef, np.abs(xs))
    axC.plot(xs, ys, color=CRE_LW_COLOR, linewidth=1.6,
             label="poly(|lat|, deg=2)")

    # Regional medians — moved to BOTTOM-LEFT to avoid polynomial-fit text
    regions = [
        ("Tropical |lat| < 23.5", np.abs(lat_m) < 23.5,  TROP_COLOR),
        ("Temperate 23.5-50",     (np.abs(lat_m) >= 23.5) & (np.abs(lat_m) < 50), TEMP_COLOR),
        ("Boreal >= 50",          np.abs(lat_m) >= 50, BOR_COLOR),
    ]
    ytxt = 0.97
    for label, m, color in regions:
        if m.sum() == 0:
            continue
        rmed = np.median(eta_m[m])
        axC.text(0.025, ytxt,
                 f"{label}: median $\\eta$ = {rmed:.1f}% (N={m.sum()})",
                 transform=axC.transAxes, fontsize=8.5,
                 color=color, va="top", ha="left", fontweight="bold",
                 bbox=dict(boxstyle="round,pad=0.22", facecolor="white",
                           edgecolor="none", alpha=0.85))
        ytxt -= 0.075
    axC.axhline(GEOMETRIC_BOUND_PCT, color=CRE_LW_COLOR,
                linewidth=1.0, linestyle="--", alpha=0.6)
    axC.set_xlabel("Latitude (deg)")
    axC.set_ylabel(r"$\eta$ (%)")
    axC.set_xlim(-65, 75)
    axC.set_ylim(0, 150)
    # Legend moved to lower-right where it sits in empty space
    axC.legend(loc="lower right", fontsize=8.5, frameon=True, framealpha=0.92)
    panel_label(axC, "(c)", x=-0.14, y=1.03)

    panel_titles = {
        axA: f"Distribution across {len(df)} sites",
        axB: "By biome (bootstrap 95% CI)",
        axC: r"$\eta$ vs latitude",
    }
    save_both(fig, "fig3_global_consistency",
              suptitle="Global consistency of the transfer fraction",
              panel_titles=panel_titles)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# Figure 4: study regions map
# ═══════════════════════════════════════════════════════════════════════════
def build_fig4():
    """Annual-mean CRE_net map (CERES EBAF) with three basin study boxes."""
    ds = xr.open_dataset(CERES_NC)
    cre = ds["toa_cre_net_mon"].mean(dim="time")

    fig, ax = plt.subplots(figsize=(10.0, 4.6),
                          subplot_kw=dict(projection=None))
    ax.set_xlim(-180, 180)
    ax.set_ylim(-40, 40)

    # Plot the CRE_net field
    lons = ds["lon"].values
    if lons.max() > 180:
        # convert 0-360 to -180-180
        lons_shifted = np.where(lons > 180, lons - 360, lons)
        order = np.argsort(lons_shifted)
        lons_shifted = lons_shifted[order]
        cre_arr = cre.values[:, order]
    else:
        lons_shifted = lons
        cre_arr = cre.values
    lats = ds["lat"].values

    pcm = ax.pcolormesh(lons_shifted, lats, cre_arr,
                       cmap="RdBu_r", vmin=-60, vmax=20, shading="auto")

    # Basin boxes
    basins = [
        ("Amazon", -70, -50, -10, 5),
        ("Congo",  10, 30, -10, 8),
        ("SE Asia", 95, 130, -10, 15),
    ]
    for name, lon0, lon1, lat0, lat1 in basins:
        ax.add_patch(Rectangle((lon0, lat0), lon1 - lon0, lat1 - lat0,
                              fill=False, edgecolor="black", linewidth=1.6))
        ax.text((lon0 + lon1) / 2, lat1 + 3, name,
                ha="center", va="bottom", fontsize=10,
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                          edgecolor="none", alpha=0.85))

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xticks([-120, -60, 0, 60, 120])
    ax.set_xticklabels(["120°W", "60°W", "0°", "60°E", "120°E"])
    ax.set_yticks([-20, -10, 0, 10, 20])
    ax.set_yticklabels(["20°S", "10°S", "0°", "10°N", "20°N"])

    cbar = fig.colorbar(pcm, ax=ax, orientation="horizontal",
                       fraction=0.07, pad=0.16, aspect=42)
    cbar.set_label(r"Annual-mean CRE$_{\mathrm{net}}$ (W m$^{-2}$)")

    save_both(fig, "fig4_study_regions",
              suptitle="Study regions on annual-mean CRE$_{\\mathrm{net}}$ "
                       "(CERES EBAF Ed4.2, 2003-2023)")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# Figure 5: CAPE vs CRE_LW — with adjustText for label cleanup
# ═══════════════════════════════════════════════════════════════════════════
def build_fig5_data():
    """Build the regional CAPE / CRE table that fig5 plots."""
    ceres = xr.open_dataset(CERES_NC)
    era5 = xr.open_dataset(ERA5_CAPE)
    print("  fig5 data: regional CAPE / CRE extraction")
    regions = [
        ("Amazon Coast",    -50, -45, -3, 2),
        ("Amazon East",     -55, -50, -5, 0),
        ("Amazon Central",  -65, -60, -5, 0),
        ("Amazon West",     -70, -65, -5, 0),
        ("Amazon Interior", -65, -60, -10, -5),
        ("Amazon Andes",    -75, -70, -10, -5),
        ("Congo West",      14, 18,  -5, 0),
        ("Congo Central",   18, 22,  -2, 2),
        ("Congo East",      24, 28,  -3, 1),
        ("Borneo West",     108, 112, -2, 2),
        ("Borneo East",     112, 116, -2, 2),
        ("SE USA",          -88, -82, 30, 35),
        ("W Europe",        2, 8, 47, 51),
        ("E China",         110, 116, 27, 32),
        ("N Africa Sahel",  -5, 5, 12, 17),
        ("C Australia",     132, 138, -25, -20),
        ("Trop W Atlantic", -45, -38, 5, 10),
        ("Trop E Pacific",  -130, -125, 0, 5),
        ("Indian Ocean",    75, 85, -5, 0),
    ]

    rows = []
    for name, lon0, lon1, lat0, lat1 in regions:
        # CERES: lon is 0-360
        cl0, cl1 = lon0 % 360, lon1 % 360
        if cl0 < cl1:
            ct = ceres.sel(lon=slice(cl0, cl1), lat=slice(lat0, lat1))
        else:
            ct = ceres.sel(lon=slice(0, cl1), lat=slice(lat0, lat1))
        cre_lw = float(ct["toa_cre_lw_mon"].mean().values)
        cre_sw = float(ct["toa_cre_sw_mon"].mean().values)
        cre_net = float(ct["toa_cre_net_mon"].mean().values)

        # ERA5: lon may be -180-180
        if "longitude" in era5.coords:
            elon, elat = "longitude", "latitude"
        else:
            elon, elat = "lon", "lat"
        et = era5.sel({elon: slice(lon0, lon1), elat: slice(lat1, lat0)})
        cape_var = "cape" if "cape" in era5.data_vars else list(era5.data_vars)[0]
        cape = float(et[cape_var].mean().values)
        rows.append({
            "region": name, "cape": cape,
            "cre_lw": cre_lw, "cre_sw": cre_sw, "cre_net": cre_net,
        })
        print(f"    {name:18s}  CAPE={cape:5.0f}  CRE_LW={cre_lw:+5.1f}  CRE_SW={cre_sw:+5.1f}")
    return pd.DataFrame(rows)


def build_fig5(df_regions):
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(13.0, 5.3),
                                   gridspec_kw=dict(wspace=0.28))

    # ── Panel (a): CRE_LW vs CAPE ─────────────────────────────────
    x = df_regions["cape"].values
    y = df_regions["cre_lw"].values
    slope, intercept = np.polyfit(x, y, 1)
    yhat = slope * x + intercept
    ss_res = np.sum((y - yhat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot
    # p-value via simple t-test
    from scipy import stats as sstats
    slope_lr, _, r_lr, p_lr, _ = sstats.linregress(x, y)

    axA.scatter(x, y, s=70, color=CRE_LW_COLOR, edgecolor="black",
                linewidth=0.6, zorder=4)
    xline = np.linspace(x.min() * 0.95, x.max() * 1.02, 100)
    yline = slope * xline + intercept
    axA.plot(xline, yline, color=CRE_LW_COLOR, linewidth=1.8,
             label=f"OLS: slope = {slope:.3f} W m$^{{-2}}$ / J kg$^{{-1}}$")

    # 95% CI band
    se_band = np.std(y - yhat) * np.sqrt(
        1 / len(x) + (xline - x.mean()) ** 2 / np.sum((x - x.mean()) ** 2)
    )
    axA.fill_between(xline, yline - 1.96 * se_band, yline + 1.96 * se_band,
                     color=CRE_LW_COLOR, alpha=0.15, label="95% CI")

    # Labels — adjustText if available, else manual
    texts = [axA.text(xi, yi, name, fontsize=7.5)
             for xi, yi, name in zip(x, y, df_regions["region"])]
    if HAVE_ADJUSTTEXT:
        adjust_text(texts, ax=axA, expand=(1.3, 1.4),
                    arrowprops=dict(arrowstyle="-", color="#888", lw=0.5))
    axA.text(0.03, 0.97,
             f"$R^2$ = {r2:.2f}\n$p$ = {p_lr:.1e}\nN = {len(df_regions)} regions",
             transform=axA.transAxes, fontsize=9.5,
             va="top", ha="left",
             bbox=dict(boxstyle="round,pad=0.32", facecolor="white",
                       edgecolor="#888", alpha=0.92))
    axA.set_xlabel(r"CAPE (J kg$^{-1}$)")
    axA.set_ylabel(r"CRE$_{\mathrm{LW}}$ (W m$^{-2}$)")
    axA.legend(loc="lower right", fontsize=8.5, frameon=True, framealpha=0.92)
    axA.grid(True, alpha=0.25, linewidth=0.5)
    panel_label(axA, "(a)", x=-0.10, y=1.03)

    # ── Panel (b): CRE_LW / |CRE_SW| ratio vs CAPE ────────────────
    ratio = df_regions["cre_lw"] / df_regions["cre_sw"].abs()
    axB.scatter(x, ratio, s=70, color=CRE_NET_COLOR, edgecolor="black",
                linewidth=0.6, zorder=4)

    # Log fit
    from scipy.optimize import curve_fit
    try:
        valid = (x > 0) & np.isfinite(ratio)
        popt, _ = curve_fit(lambda x, a, b: a * np.log(x) + b,
                           x[valid], ratio[valid])
        xs = np.linspace(x[valid].min() * 0.9, x[valid].max() * 1.02, 200)
        ys = popt[0] * np.log(xs) + popt[1]
        # R^2
        yhat = popt[0] * np.log(x[valid]) + popt[1]
        r2_b = 1 - np.sum((ratio[valid] - yhat) ** 2) / np.sum((ratio[valid] - ratio[valid].mean()) ** 2)
        axB.plot(xs, ys, color=CRE_NET_COLOR, linewidth=1.8,
                 label=f"log fit ($R^2$ = {r2_b:.2f})")
    except Exception:
        pass

    axB.axhline(0.60, color="#888", linewidth=1.0, linestyle=":",
                label="Shallow coastal ~0.60")
    axB.axhline(0.86, color="#444", linewidth=1.0, linestyle="--",
                label="Deep interior ~0.86")

    texts_b = [axB.text(xi, yi, name, fontsize=7.5)
               for xi, yi, name in zip(x, ratio, df_regions["region"])]
    if HAVE_ADJUSTTEXT:
        adjust_text(texts_b, ax=axB, expand=(1.3, 1.4),
                    arrowprops=dict(arrowstyle="-", color="#888", lw=0.5))
    axB.set_xlabel(r"CAPE (J kg$^{-1}$)")
    axB.set_ylabel(r"CRE$_{\mathrm{LW}}$ / $|$CRE$_{\mathrm{SW}}|$")
    axB.legend(loc="lower right", fontsize=8.5, frameon=True, framealpha=0.92)
    axB.grid(True, alpha=0.25, linewidth=0.5)
    panel_label(axB, "(b)", x=-0.10, y=1.03)

    panel_titles = {
        axA: r"CRE$_{\mathrm{LW}}$ scales with CAPE",
        axB: "Convective-depth regulation of SW/LW partition",
    }
    save_both(fig, "fig5_cape_cre_lw",
              suptitle="CAPE-regulated cloud radiative effects across 19 regions",
              panel_titles=panel_titles)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# Figure 6: cross-basin transects — REFLOWED to 1+2 layout
# ═══════════════════════════════════════════════════════════════════════════
def build_fig6():
    """Cross-basin transects of CRE_SW, CRE_LW, CRE_net vs distance from coast.

    Reflowed v5 layout: Amazon on top (full width), Congo + SE Asia below.
    """
    ds = xr.open_dataset(CERES_NC)

    # Basin transect spec: (basin, lat_range, transect_step_deg_lon)
    transects = {
        "Amazon": {
            "lats": (-5, 0),
            "lon_segments": [(-48, -50), (-53, -55), (-58, -60), (-63, -65), (-68, -70), (-72, -75)],
            "distances": [0, 500, 1000, 1500, 2000, 2500],
        },
        "Congo": {
            "lats": (-2, 2),
            "lon_segments": [(13, 15), (17, 19), (21, 23), (25, 27), (28, 30)],
            "distances": [0, 500, 1000, 1500, 2000],
        },
        "SE Asia": {
            "lats": (-2, 2),
            "lon_segments": [(98, 100), (104, 106), (110, 112), (116, 118), (122, 124)],
            "distances": [0, 500, 1000, 1500, 2000],
        },
    }

    def extract(basin):
        spec = transects[basin]
        rows = []
        for d, (lon0, lon1) in zip(spec["distances"], spec["lon_segments"]):
            # CERES lon is 0-360
            cl0, cl1 = sorted([lon0 % 360, lon1 % 360])
            sub = ds.sel(lon=slice(cl0, cl1),
                         lat=slice(spec["lats"][0], spec["lats"][1]))
            rows.append({
                "distance": d,
                "cre_sw": float(sub["toa_cre_sw_mon"].mean().values),
                "cre_lw": float(sub["toa_cre_lw_mon"].mean().values),
                "cre_net": float(sub["toa_cre_net_mon"].mean().values),
            })
        return pd.DataFrame(rows)

    fig = plt.figure(figsize=(11.5, 8.0))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 1.0],
                  hspace=0.32, wspace=0.25,
                  left=0.07, right=0.97, top=0.93, bottom=0.08)
    axTop = fig.add_subplot(gs[0, :])
    axBL = fig.add_subplot(gs[1, 0])
    axBR = fig.add_subplot(gs[1, 1])

    panel_axes = [(axTop, "Amazon", "(a)"),
                  (axBL,  "Congo",  "(b)"),
                  (axBR,  "SE Asia", "(c)")]

    for ax, basin, label in panel_axes:
        df_b = extract(basin)
        ax.plot(df_b["distance"], df_b["cre_sw"], "o-",
                color=CRE_SW_COLOR, linewidth=1.8, markersize=7,
                label=r"CRE$_{\mathrm{SW}}$")
        ax.plot(df_b["distance"], df_b["cre_lw"], "s-",
                color=CRE_LW_COLOR, linewidth=1.8, markersize=7,
                label=r"CRE$_{\mathrm{LW}}$")
        ax.plot(df_b["distance"], df_b["cre_net"], "D-",
                color="black", linewidth=1.8, markersize=6,
                label=r"CRE$_{\mathrm{net}}$")
        ax.axhline(0, color="gray", linewidth=0.6, linestyle=":")
        ax.set_xlabel("Distance from coast (km)")
        ax.set_ylabel(r"CRE (W m$^{-2}$)")
        ax.grid(True, alpha=0.25, linewidth=0.5)
        ax.set_ylim(-90, 80)
        panel_label(ax, label, x=-0.07 if ax is axTop else -0.13, y=1.03)
        if ax is axTop:
            ax.legend(loc="center right", fontsize=9, frameon=True, framealpha=0.92)

    panel_titles = {
        axTop: "Amazon basin transect",
        axBL: "Congo basin transect",
        axBR: "SE Asia basin transect",
    }
    save_both(fig, "fig6_cross_basin_transects",
              suptitle="Cross-basin CRE transects (CERES EBAF Ed4.2)",
              panel_titles=panel_titles)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# Figure 7: recycling amplification curve (single panel, kept clean)
# ═══════════════════════════════════════════════════════════════════════════
def build_fig7():
    fig, ax = plt.subplots(figsize=(9.0, 6.0))
    eta_site = 12.9  # BR-Sa1 anchor
    rho = np.linspace(0, 0.8, 500)
    eta_basin = eta_site / (1 - rho)

    # Published Amazon ρ range
    ax.axvspan(0.25, 0.67, color="lightgray", alpha=0.45,
               label=r"Published Amazon $\rho$ range (0.25-0.67)")

    ax.plot(rho, eta_basin, color="#1a1a1a", linewidth=2.0,
            label=r"$\eta_{\mathrm{basin}} = \eta_{\mathrm{site}} / (1-\rho)$, "
                  r"$\eta_{\mathrm{site}} = 12.9$% (BR-Sa1)")

    ax.axhline(eta_site, color=CRE_SW_COLOR, linewidth=1.2, linestyle="--",
               label=r"Site $\eta$ = 12.9%")
    ax.axhline(GEOMETRIC_BOUND_PCT, color="#8a4a30", linewidth=1.2,
               linestyle="--",
               label=r"Geometric bound (deep convection) $\eta \approx$ 35%")

    # CERES empirical Amazon
    rho_emp = 0.38
    eta_emp = eta_site / (1 - rho_emp)
    ax.scatter([rho_emp], [eta_emp], s=180, color="black",
               edgecolor="white", linewidth=1.2, zorder=5,
               label=fr"CERES empirical ($\eta$ = {eta_emp:.1f}%, $\rho$ = {rho_emp})")

    # Annotate the geometric-bound crossing
    rho_bound = 1 - eta_site / GEOMETRIC_BOUND_PCT
    ax.scatter([rho_bound], [GEOMETRIC_BOUND_PCT], s=80,
               marker="s", color="#8a4a30", edgecolor="white",
               linewidth=1.0, zorder=5)
    ax.annotate(f"$\\rho$ required to reach\ngeometric bound $\\approx$ {rho_bound:.2f}",
                xy=(rho_bound, GEOMETRIC_BOUND_PCT),
                xytext=(0.50, 42), fontsize=9,
                color="#8a4a30", ha="center",
                arrowprops=dict(arrowstyle="-", color="#8a4a30", lw=0.7))
    ax.text(rho_emp + 0.01, eta_emp - 5, f"$\\rho$ = {rho_emp}",
            fontsize=9.5, color="black")

    ax.set_xlim(0, 0.8)
    ax.set_ylim(0, 60)
    ax.set_xlabel(r"Recycling fraction $\rho$")
    ax.set_ylabel(r"Basin-scale transfer fraction $\eta_{\mathrm{basin}}$ (%)")
    ax.legend(loc="upper left", fontsize=9, frameon=True, framealpha=0.92)
    ax.grid(True, alpha=0.25, linewidth=0.5)

    save_both(fig, "fig7_recycling_amplification",
              suptitle=r"Basin $\eta$ as a function of recycling fraction $\rho$")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# Figure 8: seasonal Amazon transect (2 panels side-by-side, clean)
# ═══════════════════════════════════════════════════════════════════════════
def build_fig8():
    ds = xr.open_dataset(CERES_NC)
    lon_segments = [(-48, -50), (-53, -55), (-58, -60), (-63, -65), (-68, -70), (-72, -75)]
    distances = [0, 500, 1000, 1500, 2000, 2500]
    lats = (-5, 0)

    def by_season(months):
        time_idx = pd.to_datetime(ds["time"].values)
        mask = np.isin(time_idx.month, months)
        sub = ds.isel(time=mask)
        rows = []
        for d, (lon0, lon1) in zip(distances, lon_segments):
            cl0, cl1 = sorted([lon0 % 360, lon1 % 360])
            box = sub.sel(lon=slice(cl0, cl1), lat=slice(lats[0], lats[1]))
            rows.append({
                "distance": d,
                "cre_sw": float(box["toa_cre_sw_mon"].mean().values),
                "cre_lw": float(box["toa_cre_lw_mon"].mean().values),
                "cre_net": float(box["toa_cre_net_mon"].mean().values),
            })
        return pd.DataFrame(rows)

    wet = by_season([12, 1, 2, 3, 4, 5])
    dry = by_season([6, 7, 8, 9, 10, 11])

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(12.5, 5.5),
                                   gridspec_kw=dict(wspace=0.22))

    for ax, df_s, label in [(axA, wet, "(a)"), (axB, dry, "(b)")]:
        ax.plot(df_s["distance"], df_s["cre_sw"], "o-",
                color=CRE_SW_COLOR, linewidth=1.8, markersize=7,
                label=r"CRE$_{\mathrm{SW}}$")
        ax.plot(df_s["distance"], df_s["cre_lw"], "s-",
                color=CRE_LW_COLOR, linewidth=1.8, markersize=7,
                label=r"CRE$_{\mathrm{LW}}$")
        ax.plot(df_s["distance"], df_s["cre_net"], "D-",
                color="black", linewidth=1.8, markersize=6,
                label=r"CRE$_{\mathrm{net}}$")
        ax.axhline(0, color="gray", linewidth=0.6, linestyle=":")
        ax.set_xlabel("Distance from coast (km)")
        ax.set_ylabel(r"CRE (W m$^{-2}$)")
        ax.grid(True, alpha=0.25, linewidth=0.5)
        ax.set_ylim(-95, 75)
        panel_label(ax, label, x=-0.10, y=1.03)

    axB.legend(loc="lower right", fontsize=9, frameon=True, framealpha=0.92)
    panel_titles = {
        axA: "Wet season (DJF-MAM)",
        axB: "Dry season (JJA-SON)",
    }
    save_both(fig, "fig8_seasonal_transect",
              suptitle="Seasonal Amazon CRE transect",
              panel_titles=panel_titles)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# Figure 9: deforestation counterfactual (2 panels, cleaner annotations)
# ═══════════════════════════════════════════════════════════════════════════
def build_fig9():
    # Synthesized from the v4 build script's published numbers
    # Intact vs deforested arc CRE_net by season
    seasons = ["Wet (DJF-MAM)", "Dry (JJA-SON)", "Annual"]
    intact = [-20.5, -10.2, -15.4]
    arc =    [-12.9, -3.6,  -8.3]
    deltas = [a - i for a, i in zip(arc, intact)]

    # Cloud cover diff by longitude bin
    lon_bins = ["60-55 W", "55-50 W", "50-45 W"]
    cloud_diff_pp = [6.5, 6.7, 9.7]

    fig, (axA, axB) = plt.subplots(1, 2, figsize=(13.0, 5.5),
                                   gridspec_kw=dict(wspace=0.30))

    # ── Panel (a): intact vs arc CRE_net bars with Δ labels ABOVE ──────
    x = np.arange(len(seasons))
    w = 0.35
    bars_intact = axA.bar(x - w/2, intact, w, color="#2d6a4f",
                          edgecolor="black", linewidth=0.6,
                          label="Intact forest")
    bars_arc = axA.bar(x + w/2, arc, w, color="#a8694d",
                       edgecolor="black", linewidth=0.6,
                       label="Deforested arc")
    # Delta annotations positioned ABOVE the bars (in white space)
    ymin_a = min(intact + arc) * 1.1
    for i, d in enumerate(deltas):
        # Place delta annotation between the bar tops at the top of the panel
        y_top = max(intact[i], arc[i]) + 1.5
        axA.text(i, y_top, f"$\\Delta$ = {d:+.1f}",
                ha="center", va="bottom", fontsize=9.5,
                fontweight="bold", color="#444")

    axA.axhline(0, color="black", linewidth=0.5)
    axA.set_xticks(x)
    axA.set_xticklabels(seasons)
    axA.set_ylabel(r"CRE$_{\mathrm{net}}$ (W m$^{-2}$)")
    axA.legend(loc="lower right", fontsize=9, frameon=True)
    axA.set_ylim(ymin_a, 4.0)
    axA.grid(True, alpha=0.25, axis="y", linewidth=0.5)
    panel_label(axA, "(a)", x=-0.13, y=1.03)

    # ── Panel (b): cloud cover difference by longitude bin ─────────────
    bars_b = axB.bar(np.arange(len(lon_bins)), cloud_diff_pp,
                    color="#7a7a7a", edgecolor="black", linewidth=0.6)
    for i, v in enumerate(cloud_diff_pp):
        axB.text(i, v + 0.2, f"+{v:.1f} pp",
                ha="center", va="bottom", fontsize=9.5, fontweight="bold")
    axB.set_xticks(np.arange(len(lon_bins)))
    axB.set_xticklabels(lon_bins)
    axB.set_xlabel("Longitude bin")
    axB.set_ylabel("Cloud fraction difference (pp)\nIntact - Arc")
    axB.set_ylim(0, max(cloud_diff_pp) * 1.20)
    axB.grid(True, alpha=0.25, axis="y", linewidth=0.5)
    panel_label(axB, "(b)", x=-0.13, y=1.03)

    panel_titles = {
        axA: r"CRE$_{\mathrm{net}}$: intact forest vs deforested arc",
        axB: "Cloud cover loss in deforested arc",
    }
    save_both(fig, "fig9_deforestation_counterfactual",
              suptitle="Deforestation counterfactual: Amazon intact vs deforested arc",
              panel_titles=panel_titles)
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════
def main():
    print("Paper 6 v5 unified figure build")
    print("=" * 70)
    print(f"  output dir: {OUT}")
    print()

    print("Loading site data...")
    df = pd.read_csv(DATA_CSV)
    df = df.dropna(subset=["eta"]).copy()
    print(f"  {len(df)} sites with valid eta")
    print()

    print("Building Figure 1 (three-streams schematic, matplotlib redraw) ...")
    build_fig1()
    print()

    print("Building Figure 2 (LE vs CRE_net) ...")
    build_fig2(df)
    print()

    print("Building Figure 3 (global consistency, 1+2 layout) ...")
    build_fig3(df)
    print()

    print("Building Figure 4 (study regions map) ...")
    try:
        build_fig4()
    except Exception as e:
        print(f"  [warn] fig4 failed: {e}")
    print()

    print("Building Figure 5 (CAPE vs CRE_LW, adjustText) ...")
    try:
        df_regions = build_fig5_data()
        build_fig5(df_regions)
    except Exception as e:
        print(f"  [warn] fig5 failed: {e}")
    print()

    print("Building Figure 6 (cross-basin transects, 1+2 layout) ...")
    try:
        build_fig6()
    except Exception as e:
        print(f"  [warn] fig6 failed: {e}")
    print()

    print("Building Figure 7 (recycling amplification) ...")
    build_fig7()
    print()

    print("Building Figure 8 (seasonal transect) ...")
    try:
        build_fig8()
    except Exception as e:
        print(f"  [warn] fig8 failed: {e}")
    print()

    print("Building Figure 9 (deforestation counterfactual) ...")
    build_fig9()
    print()

    print("=" * 70)
    print(f"Done. Outputs in: {OUT}")


if __name__ == "__main__":
    main()
