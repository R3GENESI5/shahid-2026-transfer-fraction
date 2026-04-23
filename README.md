# Empirical constraints on the fraction of surface latent heat flux reaching the top of atmosphere as net radiative cooling

Supplementary code and figures for:

**Shahid, A. B. (2026).** *Empirical constraints on the fraction of surface latent heat flux reaching the top of atmosphere as net radiative cooling.* ESSOAr preprint.

---

## What this repository contains

The analysis pipeline, the 9 published figures, and the forest valuation practitioner guide for the paper. The manuscript PDF and LaTeX source are not in this repository; the ESSOAr preprint is the authoritative document.

## Core results

| Quantity | Value |
|----------|-------|
| Global median η (314 FLUXNET sites, all biomes) | **30.0%** [95% CI 27.1–34.5%] |
| Tropical evergreen broadleaf forest median η (8 sites, 4 continents) | **14.7%** (range 6.9–22.2%) |
| Amazon basin η | **20.8%** (CRE_net = −19.8 W/m², LE = 95.1 W/m²) |
| Congo basin η / SE Asia basin η | 17.1% / 20.1% |
| Recycling amplification (Amazon / Congo / SE Asia) | 1.62× / 1.63× / 1.57× |
| CRE_LW vs CAPE regression | R² = 0.74, slope = 0.032 W/m² per J/kg |
| Trajectory control, Amazon − Atlantic (n=28) | +0.44 W/m² (t = 0.21, p = 0.83; null indistinguishable) |
| Forest valuation, small patch (site-level anchor) | $86/ha/yr at SCC $120 |
| Forest valuation, basin-scale contiguous forest | $139/ha/yr at SCC $120 |

## Repository layout

```
shahid-2026-transfer-fraction/
├── README.md                  ← this file
├── LICENSE                    ← MIT
├── CITATION.cff               ← citation metadata
├── .gitignore
│
├── figures/                   ← the 9 published figures (PDF + PNG, 300 DPI)
│   ├── build_figures_v4_diagrams.py       Fig 1, Fig 4
│   ├── build_figures_v4_scatter.py        Fig 2, Fig 3, Fig 5
│   ├── build_figures_v4_transects.py      Fig 6, Fig 7, Fig 8, Fig 9
│   ├── fig1_three_streams.{pdf,png}       Three-stream decomposition at BR-Sa1
│   ├── fig2_le_vs_cre_net.{pdf,png}       Surface LE vs TOA CRE_net across 314 sites
│   ├── fig3_global_consistency.{pdf,png}  η histogram + biome medians + latitude
│   ├── fig4_study_regions.{pdf,png}       Basin polygons on CRE_net map
│   ├── fig5_cape_cre_lw.{pdf,png}         CAPE vs CRE_LW regression
│   ├── fig6_cross_basin_transects.{pdf,png}  Coast-to-interior CRE transects
│   ├── fig7_recycling_amplification.{pdf,png}  Eltahir–Bras recycling model
│   ├── fig8_seasonal_transect.{pdf,png}   Wet vs dry Amazon seasonal transect
│   ├── fig9_deforestation_counterfactual.{pdf,png}  Intact vs arc CRE difference
│   └── fig5_region_data.csv               Provenance: per-region CAPE + CRE values
│
├── analysis/                  ← data pipeline cited in the supplementary
│   ├── requirements.txt
│   ├── data/
│   │   └── site_summary_v3_full.csv       314 FLUXNET sites joined with CERES
│   ├── scripts/
│   │   ├── 01_basin_analysis.py           Basin-scale CRE extraction + η
│   │   ├── 02_build_figures.py            Intermediate figure-build (reference)
│   │   ├── 03_download_era5_winds.py      ERA5 6-hourly 200 hPa u, v download
│   │   ├── 04_run_trajectories.py         Forward Lagrangian integration (main ensemble)
│   │   ├── 05_correlate_trajectories_with_ceres.py   Endpoint OLR coupling
│   │   ├── 06_control_test.py             Original v3 Atlantic control (n=4, 2010 only)
│   │   ├── 06b_control_test_extended.py   Extended control n=28, per-parcel (slow, documentation)
│   │   ├── 06c_control_test_vectorized.py Vectorized control, no preloading (I/O-bound, documentation)
│   │   ├── 06d_control_test_preloaded.py  ★ Production: preloaded vectorized, ~108s for 56 ensembles
│   │   ├── 07_generate_supplementary_figure.py       Supplementary trajectory figure
│   │   └── PIPELINE.md                    Trajectory pipeline reference doc
│   └── results/
│       ├── control_comparison_preloaded.csv          Atlantic control n=28 (primary result)
│       ├── summary_key_numbers.json
│       ├── table1_basin_cre.csv           Basin-mean CRE_SW, CRE_LW, CRE_net, LE
│       ├── table2_amazon_transect.csv     Amazon coast-to-interior profile
│       ├── table3_congo_transect.csv      Congo coast-to-interior profile
│       ├── table4_se_asia_transect.csv    SE Asia coast-to-interior profile
│       ├── table5_seasonal_amazon_wet.csv Wet-season transect
│       ├── table6_seasonal_amazon_dry.csv Dry-season transect
│       ├── table7_deforestation_counterfactual.csv   Intact vs arc CRE
│       ├── table8_cre_lw_vs_cape.csv      19-region regression data
│       ├── table9_recycling_model.csv     Eltahir-Bras amplification sensitivity
│       └── table10_cloud_top_properties.csv          Cloud top temperature diagnostic
│
└── docs/
    ├── forest_valuation_practitioner_guide.md
    └── forest_valuation_practitioner_guide.pdf
```

## Reproducing the figures

```bash
cd figures
pip install -r ../analysis/requirements.txt
pip install adjustText cartopy

# Figures 1 + 4 (three-stream diagram + study-region map)
python build_figures_v4_diagrams.py

# Figures 2 + 3 + 5 (scatter + global consistency + CAPE regression)
python build_figures_v4_scatter.py

# Figures 6 + 7 + 8 + 9 (transects + recycling + seasonal + deforestation counterfactual)
python build_figures_v4_transects.py
```

Each build script reads the inputs listed below and writes PDF (vector) and PNG (300 DPI) outputs in place.

## Data inputs required (not tracked in this repo)

| Input | Source | Used by |
|-------|--------|---------|
| FLUXNET2015 + ONEFlux joined site summary | `analysis/data/site_summary_v3_full.csv` (included) | Figs 1, 2, 3 |
| CERES EBAF Ed4.2 monthly TOA radiation | [NASA LaRC CERES](https://ceres.larc.nasa.gov/data/) | Figs 4, 5, 6, 7, 8, 9; basin extraction; deforestation counterfactual |
| ERA5 6-hourly 200 hPa winds | [Copernicus CDS](https://cds.climate.copernicus.eu/) | Control experiment (scripts 04, 06b, 06c, 06d) |
| ERA5 CAPE monthly | [Copernicus CDS](https://cds.climate.copernicus.eu/) | Fig 5 |
| MODIS MCD12C1 land cover | [NASA LP DAAC](https://lpdaac.usgs.gov/) | Fig 9 deforestation counterfactual |

The ERA5 winds pipeline (`03_download_era5_winds.py`) requires a Copernicus CDS API key.

## Reproducing the Atlantic-source trajectory control (n=28)

```bash
cd analysis/scripts
python 06d_control_test_preloaded.py
```

Runs the 56-ensemble symmetric control matrix (7 years × 4 seasons × 2 source regions) in approximately 108 seconds on one CPU core. Writes `analysis/results/control_comparison_preloaded.csv` and prints summary statistics: mean Amazon−Atlantic endpoint OLR difference, std, range, one-sample t-test, and per-ENSO-phase breakdown. Scripts `06b` (per-parcel, slow) and `06c` (vectorized without preloading) reproduce the same result by different algorithms and are provided for cross-validation.

See `analysis/scripts/PIPELINE.md` for implementation notes and performance targets.

## Forest valuation practitioner guide

For practitioners applying η to specific forest valuation cases, see `docs/forest_valuation_practitioner_guide.pdf`. Summary:

| Forest type | η applicable | Central $/ha/yr at SCC $120 |
|------------|-------------|------------------------------|
| Small patch, plantation, <50 km contiguous | **12.9%** (BR-Sa1 single-site anchor) | **$86** |
| Basin-scale contiguous tropical forest (Amazon) | **20.8%** | **$139** |

Full decision tree, SCC sensitivity (at $51, $120, $200), alternative counterfactuals (pasture, savanna, shrubland), worked example for 5.5 M ha Amazon, and the list of biophysical cooling pathways this number does not capture are all in the guide.

## Citation

If you use this code or figures:

> Shahid, A. B. (2026). *Empirical constraints on the fraction of surface latent heat flux reaching the top of atmosphere as net radiative cooling.* ESSOAr preprint. DOI: *[pending]*.

For machine-readable citation, see `CITATION.cff`.

## Companion papers in the programme

- Shahid, A. B. (2026a). *Biome-specific radiative forcing coefficients reveal ecosystems as active climate regulators.* ESSOAr: [10.22541/essoar.15001972/v1](https://doi.org/10.22541/essoar.15001972/v1)
- Shahid, A. B. (2026b). *Does biome-specific surface energy partitioning propagate to the top of atmosphere?* ESSOAr: [10.22541/essoar.15002157/v1](https://doi.org/10.22541/essoar.15002157/v1)
- Shahid, A. B. (2026c). *Collapse of the moisture corridors that sustain inland rainfall in the Amazon and Congo.* ESSOAr: [10.22541/essoar.15002167/v1](https://doi.org/10.22541/essoar.15002167/v1)

## License

Code is released under the MIT License (see `LICENSE`). Figures are released under CC BY 4.0.

## Contact

Ali Bin Shahid — ab.itzhaq@gmail.com — ORCID [0009-0003-9709-4241](https://orcid.org/0009-0003-9709-4241)
