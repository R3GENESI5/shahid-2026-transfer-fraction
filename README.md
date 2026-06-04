# Empirical constraints on the fraction of surface latent heat flux reaching the top of atmosphere as net radiative cooling

Supplementary code and figures for:

**Shahid, A. B. (2026).** *Empirical constraints on the fraction of surface latent heat flux reaching the top of atmosphere as net radiative cooling.* ESSOAr preprint.

Current version: **v5** (n = 341 sites; FluxDataKit-v3 pooled with JapanFlux2024; matches Paper 1 v3 site universe).

---

## What this repository contains

The analysis pipeline and the 9 published figures for the paper. 

## Core results (v5)

| Quantity | Value |
|----------|-------|
| Sample size | **341 FLUXNET sites** (FluxDataKit-v3 + JapanFlux2024, five continents) |
| Global median η, all biomes | **31.6%** [95% CI 28.3–35.8%] |
| Tropical evergreen broadleaf forest median η (12 sites, 5 continents) | **14.7%** (range 5.6–31.0% excluding the subtropical-monsoon outlier CN-Din) |
| Amazon basin η | **20.8%** (CRE_net = −19.8 W/m², LE = 95.1 W/m²) |
| Congo basin η / SE Asia basin η | 17.1% / 20.1% |
| Recycling amplification (Amazon / Congo / SE Asia) | 1.62× / 1.63× / 1.57× (forward) |
| SE Asia tropical EBF anchors (FLUXNET, n = 5) | mean 13.3%, median 6.7%; sites MY-LHP (24.2%), ID-PaB (5.8%), ID-Pag (7.1% FDK / 6.4% JF), KH-Kmp (5.6%), TH-Kog (31.0%) |
| Congo basin FLUXNET anchor | None (largest unresolved limitation; awaits AfriFlux) |
| CRE_LW vs CAPE regression | R² = 0.74, slope = 0.032 W/m² per J/kg, n = 19 regions |
| Trajectory control, Amazon − Atlantic (n=28) | +0.44 W/m² (t = 0.21, p = 0.83; null indistinguishable) |

**Note on valuation**: v5 deliberately omits per-hectare dollar valuation. The TOA radiative pathway is one of several biophysical mechanisms; translating η into per-hectare conservation value (with social cost of carbon, counterfactual land cover, and scale-dependent attribution assumptions) is the subject of the companion cascade-valuation paper (Paper 8, in preparation). Earlier v4.2 contained `$86/ha/yr` and `$139/ha/yr` estimates; these have been pulled per the scope discipline of v5.

## Version history

| Version | Sites | Global median η | Key change |
|---------|-------|------------------|------------|
| v4.2 | 314 (FluxDataKit-v3 only) | 30.0% | Universal reframe; dual-anchor disclosure |
| **v5** | **341** (+ JapanFlux2024; matches Paper 1 v3) | **31.6%** | SE Asia tropical EBF anchors explicit; dollar valuation moved to Paper 8 |

## Repository layout

```
shahid-2026-transfer-fraction/
├── README.md                  ← this file
├── LICENSE                    ← MIT
├── CITATION.cff               ← citation metadata
├── .gitignore
│
├── figures/                   ← 9 published figures (PDF + PNG, 300 DPI; both _titled and _notitled variants)
│   ├── 06_build_figs_v5.py                Unified v5 figure builder (all 9 figures)
│   ├── fig1_three_streams_{titled,notitled}.{pdf,png}        Three-stream Sankey schematic at BR-Sa1
│   ├── fig2_le_vs_cre_net_{titled,notitled}.{pdf,png}        Surface LE vs TOA CRE_net (341 sites)
│   ├── fig3_global_consistency_{titled,notitled}.{pdf,png}   η histogram + biome medians + latitude (1+2 layout)
│   ├── fig4_study_regions_{titled,notitled}.{pdf,png}        Basin polygons on CRE_net map
│   ├── fig5_cape_cre_lw_{titled,notitled}.{pdf,png}          CAPE vs CRE_LW regression (adjustText labels)
│   ├── fig6_cross_basin_transects_{titled,notitled}.{pdf,png}    Amazon/Congo/SE Asia transects (1+2 layout)
│   ├── fig7_recycling_amplification_{titled,notitled}.{pdf,png}  Eltahir-Bras recycling model
│   ├── fig8_seasonal_transect_{titled,notitled}.{pdf,png}    Wet vs dry Amazon seasonal transect
│   └── fig9_deforestation_counterfactual_{titled,notitled}.{pdf,png}    Intact vs arc CRE difference
│
├── analysis/                  ← v5 data pipeline
│   ├── requirements.txt
│   ├── data/
│   │   ├── site_summary_v5_n342.csv      ★ 341-site joint table with η column (v5 production data)
│   │   ├── jf_sites_extended_ceres.csv   JapanFlux2024 sites with full CERES columns
│   │   └── site_summary_v3_full.csv      314-site FluxDataKit-v3 base (v4.2 reference)
│   ├── scripts/
│   │   ├── 01_jf_sites_extended_ceres.py     CERES extraction for JapanFlux2024 sites
│   │   ├── 02_merge_n342.py                  Merge 314 + 27 + MY-LHP → 341 + η computation
│   │   ├── 05_patch_manuscript.py            v4.2 → v5 number patches (text)
│   │   ├── 07_remove_dollars.py              Dollar valuation extraction (Paper 8 redirect)
│   │   ├── 08_build_docx.py                  DOCX build (pandoc + python-docx clean-up)
│   │   ├── 01_basin_analysis.py              Basin-scale CRE extraction + η
│   │   ├── 03_download_era5_winds.py         ERA5 6-hourly 200 hPa u,v download
│   │   ├── 04_run_trajectories.py            Forward Lagrangian integration (main ensemble)
│   │   ├── 05_correlate_trajectories_with_ceres.py    Endpoint OLR coupling
│   │   ├── 06_control_test.py / 06b / 06c / 06d_control_test_preloaded.py   Atlantic-source control
│   │   ├── 07_generate_supplementary_figure.py    Supplementary trajectory figure
│   │   └── PIPELINE.md                       Trajectory pipeline reference
│   └── results/
│       ├── merge_diagnostics.txt             v5 merge audit log
│       ├── control_comparison_preloaded.csv  Atlantic control n=28 (primary result)
│       ├── summary_key_numbers.json
│       ├── table1_basin_cre.csv to table10_cloud_top_properties.csv    Per-figure intermediate tables
│       └── (other per-figure CSVs)
│
└── docs/                      ← legacy practitioner guide (v4.2-era; dollar values now apply only with caveats; cf. Paper 8)
    ├── forest_valuation_practitioner_guide.md
    └── forest_valuation_practitioner_guide.pdf
```

## Reproducing the v5 figures

```bash
cd figures
pip install -r ../analysis/requirements.txt
pip install adjustText xarray

# All 9 figures in both titled and notitled variants
python 06_build_figs_v5.py
```

The build script reads `../analysis/data/site_summary_v5_n342.csv`, the CERES EBAF NetCDF (path hardcoded; adjust `CERES_NC` constant), and an ERA5 CAPE NetCDF for figure 5. Outputs go to `./figures/figN_NAME_{titled,notitled}.{pdf,png}`.

`_titled` variants embed the figure title (suitable for slide decks, the practitioner guide). `_notitled` variants are what the manuscript embeds (journal convention: title goes in caption).

## Reproducing v5 site sample (341 sites from 314)

```bash
cd analysis/scripts
python 01_jf_sites_extended_ceres.py   # 44 JapanFlux2024 sites with full CERES columns
python 02_merge_n342.py                # Merge with 314-site FluxDataKit base; compute η
```

Verification: `merge_diagnostics.txt` reports the per-source η medians and the ID-Pag / ID-PaD same-tower dedup decision (kept ID-Pag, dropped ID-PaD as duplicate processing run of the same Borneo peatland).

## Data inputs required (not tracked in this repo)

| Input | Source | Used by |
|-------|--------|---------|
| FluxDataKit-v3 (FLUXNET2015 + ONEFlux synthesis, 314 sites) | [Zenodo 10.5281/zenodo.10885933](https://doi.org/10.5281/zenodo.10885933) | All scripts |
| JapanFlux2024 release (Hirano et al. 2025) | [Earth System Science Data 17:3807](https://doi.org/10.5194/essd-17-3807-2025) and [Arctic Data archive System](https://ads.nipr.ac.jp/japan-flux2024/) | Scripts 01, 02 |
| CERES EBAF Ed4.2 monthly TOA radiation | [NASA LaRC CERES](https://ceres.larc.nasa.gov/data/) | Figs 4, 5, 6, 7, 8, 9; basin extraction; deforestation counterfactual |
| ERA5 6-hourly 200 hPa winds | [Copernicus CDS](https://cds.climate.copernicus.eu/) | Control experiment (scripts 04, 06b–06d) |
| ERA5 CAPE monthly | [Copernicus CDS](https://cds.climate.copernicus.eu/) | Fig 5 |
| MODIS MCD12C1 land cover | [NASA LP DAAC](https://lpdaac.usgs.gov/) | Fig 9 deforestation counterfactual |

The ERA5 winds pipeline (`03_download_era5_winds.py`) requires a Copernicus CDS API key.

## Reproducing the Atlantic-source trajectory control (n=28)

```bash
cd analysis/scripts
python 06d_control_test_preloaded.py
```

Runs the 56-ensemble symmetric control matrix (7 years × 4 seasons × 2 source regions) in approximately 108 seconds on one CPU core. Writes `analysis/results/control_comparison_preloaded.csv` and prints summary statistics. Scripts `06b` (per-parcel, slow) and `06c` (vectorized without preloading) reproduce the same result by different algorithms and are provided for cross-validation.

See `analysis/scripts/PIPELINE.md` for implementation notes.

## Building the DOCX version (companion to the manuscript repo)

```bash
cd analysis/scripts
python 08_build_docx.py
```

Uses pandoc to convert `paper_body_v5.tex` → docx, then python-docx applies:
- Title block restyling (Arial 16 / 12 / 10)
- Body font normalisation (Arial 11)
- Figure sizing to 6.5" page width
- Programmatic rebuild of Table 1, Table 2, Table S1, Table S2 (pandoc longtable conversion mis-aligns these cells; clean rebuild from constants)
- Page numbers in footer

Requires `pandoc` on PATH and the `python-docx` package.

## Citation

If you use this code or figures, please cite both the paper and the code archive:

**Paper** (ESSOAr preprint):

> Shahid, A. B. (2026). *Empirical constraints on the fraction of surface latent heat flux reaching the top of atmosphere as net radiative cooling.* ESSOAr preprint. DOI: *[pending]*.

**Code and figures** (Zenodo):

> Shahid, A. B. (2026). *Empirical constraints on the fraction of surface latent heat flux reaching the top of atmosphere as net radiative cooling: code and figures.* Zenodo. [10.5281/zenodo.20539525](https://doi.org/10.5281/zenodo.20539525) (concept DOI, always resolves to latest version). v1.0.0 specifically: [10.5281/zenodo.20539526](https://doi.org/10.5281/zenodo.20539526).

For machine-readable citation, see `CITATION.cff`.

## Companion papers in the programme

- Shahid, A. B. (2026a). *Biome-specific radiative forcing coefficients reveal ecosystems as active climate regulators.* ESSOAr: [10.22541/essoar.15001972/v2](https://doi.org/10.22541/essoar.15001972/v2) (Paper 1 v3, n = 341)
- Shahid, A. B. (2026b). *Does biome-specific surface energy partitioning propagate to the top of atmosphere?* ESSOAr: [10.22541/essoar.15002157/v1](https://doi.org/10.22541/essoar.15002157/v1) (Paper 2, n = 314)
- Shahid, A. B. (2026c). *Collapse of the moisture corridors that sustain inland rainfall in the Amazon and Congo.* ESSOAr: [10.22541/essoar.15002167/v1](https://doi.org/10.22541/essoar.15002167/v1) (Paper 3)
- Shahid, A. B. (2026, in preparation). *Cascade valuation of tropical forest cooling services across spatial scales.* (Paper 8 — picks up the per-hectare dollar translation that v5 of this paper deliberately omits)

## License

Code is released under the MIT License (see `LICENSE`). Figures are released under CC BY 4.0.

## Contact

Ali Bin Shahid — ab.itzhaq@gmail.com — ORCID [0009-0003-9709-4241](https://orcid.org/0009-0003-9709-4241)
