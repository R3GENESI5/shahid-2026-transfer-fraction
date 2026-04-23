# Lagrangian Trajectory Pipeline — Use 06d

## TL;DR

For any forward-trajectory experiment advecting parcels at 200 hPa over tropical basins with ERA5 winds and extracting CERES OLR at endpoints, **use `06d_control_test_preloaded.py`**. Runs the full 7-year × 4-season × 2-source-region matrix (56 ensembles, ~16,000 parcel trajectories) in about **108 seconds**. Preloads u/v fields as numpy arrays once per season and uses scipy `RegularGridInterpolator` for vectorized per-timestep interpolation on all active parcels at once.

## Three scripts, same algorithm, different speeds

| Script | Approach | Speed | Use for |
|--------|----------|-------|---------|
| `06d_control_test_preloaded.py` | scipy RGI + preloaded numpy stacks | ~108 s / 56-ensemble matrix | **Production runs** |
| `06c_control_test_vectorized.py` | scipy RGI, no preloading | ~8 min / season (I/O bound) | Demonstration that vectorization alone isn't enough |
| `06b_control_test_extended.py` | per-parcel `xarray.interp()` | ~3 hours / 56-ensemble matrix | Cross-validation / documentation only |

The three scripts produce identical numerical results within floating-point tolerance. Use 06d unless you have a specific reason to re-verify against the slow reference.

## Adapt for new experiments

To run a Congo or SE Asia control, a different ENSO year set, or a different altitude, edit `06d_control_test_preloaded.py`:

- `WIND_DIR`, `CERES_PATH` — data file paths
- `YEARS`, `ENSO_PHASE` — which years to cover and their ENSO labels
- `amazon_lats, amazon_lons, atlantic_lats, atlantic_lons` inside `run_year()` — release-box coordinates for the two source regions being compared. Add a third (Congo) if needed.
- `N_STEPS`, `DT_HOURS` — integration duration and timestep
- `LAT_MIN/MAX, LON_MIN/MAX` — advection domain bounds

## Validation reference

The v3 Paper 6 published n=4 control (2010 only, four seasons) gives:

| Season | Amazon (W/m²) | Atlantic (W/m²) | Δ (W/m²) |
|--------|---------------|-----------------|----------|
| Jan | 273.3 | 287.9 | −14.6 |
| Apr | 273.9 | 256.4 | +17.5 |
| Jul | — | — | −3.8 |
| Oct | — | — | +4.2 |

06d's 2010 output reproduces these within 0.3–3.0 W/m² across all four seasons. If you rewrite the script, verify against this reference before trusting results.

## Known gotchas

1. **ERA5 latitude is descending** (90 → −90). scipy RGI needs ascending coordinates. 06d flips the array when needed.
2. **CERES longitude is 0–360**; ERA5 is −180 to +180. Wrap before querying CERES.
3. **`xarray.interp()` per parcel** is a ~1000× slowdown trap. Don't use it inside the advection loop.
4. **`.isel(valid_time=tidx).values` inside the loop** triggers one NetCDF read per timestep. Preload the full slice once per season.
5. **Python stdout is buffered**. Use `python -u` and `flush=True` on print statements for visible progress from background runs.
6. **Boundary-exit parcels**: freeze at last valid position, don't delete. Preserves array shape for endpoint extraction.

## Output

Writes a CSV `control_comparison_preloaded.csv` to `../results/` with columns:
`year, month, enso_phase, amazon_source_ref_olr, amazon_endpoint_olr, atlantic_endpoint_olr, difference, n_amazon_parcels, n_atlantic_parcels`.

Prints summary statistics to stdout: mean, std, min/max, range, one-sample t-test against zero, and per-ENSO-phase breakdown.

## Provenance

Extended from Shahid (2026) Paper 6 v3 supplementary control (n=4 single-year), to n=28 symmetric control matrix, during the v4.2 revision of Paper 6. The n=28 result strengthens the paper's null-result claim by closing two anticipated JGR reviewer counterarguments (2010-anomalous, 4-seasons-insufficient).
