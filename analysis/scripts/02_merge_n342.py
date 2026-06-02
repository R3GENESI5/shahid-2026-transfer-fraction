"""
Paper 6 v5 step 02: Merge Paper 6's 314-site FluxDataKit table with
the JapanFlux2024 sites used by Paper 1 v3 (27 fitted + MY-LHP), and
compute the per-site transfer fraction eta = |CRE_net| / LE.

Rationale for the 342-site universe:
  - Paper 1 v3 joint fit: 314 FluxDataKit + 27 JapanFlux2024 = 341 sites
    for the alpha(beta) sigmoid. Paper 1 keeps ID-Pag and ID-PaD as
    separate rows (two flux processing protocols of the same physical
    tower in Borneo).
  - Paper 6 v5: matches Paper 1's site universe exactly for the 27 JF
    sites, PLUS MY-LHP. MY-LHP was prediction-only in Paper 1 (no NETRAD
    column) but fully usable for Paper 6 since eta = |CRE_net|/LE does
    not require Rn. Net: 314 + 27 + 1 = 342.
  - Method note: 342 > 341 by one because Paper 6's data requirements
    differ from Paper 1's; the eta computation is independent of Rn.

Inputs:
  - D:/Projects/Programme/paper_1_alpha_beta/outputs/toa_tables/
    site_summary_v3_full.csv  (314 FluxDataKit sites, Paper 6's existing data)
  - jf_sites_extended_ceres.csv (44 JF sites with full CERES columns,
    produced by step 01)

Outputs:
  - site_summary_v5_n342.csv (314 + 28 = 342 rows, with eta column added)
  - merge_diagnostics.txt
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

HERE = Path(__file__).parent
P6_314 = Path(
    "D:/Projects/Programme/paper_1_alpha_beta/outputs/toa_tables/"
    "site_summary_v3_full.csv"
)
JF_44 = HERE / "jf_sites_extended_ceres.csv"
OUT = HERE / "site_summary_v5_n342.csv"
DIAG = HERE / "merge_diagnostics.txt"

# Paper 1 v3 joint fit universe: 27 JapanFlux2024 sites
PAPER1_JF_27 = [
    "CN-HaM", "CN-Lsh", "ID-PaB", "ID-PaD", "ID-Pag",
    "JP-Api", "JP-BBY", "JP-Fjy", "JP-Fmt", "JP-KaL",
    "JP-Khw", "JP-Kzw", "JP-MBF", "JP-MMF", "JP-Mse",
    "JP-Om1", "JP-SMF", "JP-Shn", "JP-Spp", "JP-Tef",
    "JP-Tgf", "KH-Kmp", "MN-Kbu", "RU-Ege", "RU-SkP",
    "TH-Kog", "TH-Mae",
]
# Plus the prediction-only-in-Paper-1, fully-usable-here site:
JF_EXTRA = ["MY-LHP"]
JF_UNIVERSE = PAPER1_JF_27 + JF_EXTRA  # 28 sites


def main() -> int:
    lines = []
    def log(msg=""):
        print(msg)
        lines.append(msg)

    log("=" * 70)
    log("Paper 6 v5 merge: 314 FluxDataKit + 28 JapanFlux2024 = 342 sites")
    log("=" * 70)
    log("")

    log(f"[load] {P6_314}")
    df314 = pd.read_csv(P6_314)
    log(f"  rows: {len(df314)}")
    df314 = df314.assign(source="FluxDataKit-v3")

    log(f"[load] {JF_44}")
    jf = pd.read_csv(JF_44)
    log(f"  rows in JF table: {len(jf)}")

    # Filter to Paper 1's 28-site universe
    missing = [s for s in JF_UNIVERSE if s not in jf["site_id"].values]
    if missing:
        log(f"  WARNING: missing from JF table: {missing}")
    jf28 = jf[jf["site_id"].isin(JF_UNIVERSE)].copy()
    log(f"  filtered to Paper 1 v3 + MY-LHP universe: {len(jf28)}")

    # Align columns: Paper 6 314 uses 'bowen_ratio'; JF already renamed.
    # Schema difference: Paper 6 314 has ERA5 columns (cape, tcwv, blh, precip)
    # and cre_jja / cre_djf. JF rows will have NaN for those.
    expected_p6_cols = set(df314.columns) | {"source"}
    expected_jf_cols = set(jf28.columns)
    only_in_p6 = expected_p6_cols - expected_jf_cols
    only_in_jf = expected_jf_cols - expected_p6_cols

    log(f"  cols only in P6 (will be NaN for JF rows): {sorted(only_in_p6)[:10]}{'...' if len(only_in_p6)>10 else ''}")
    log(f"  cols only in JF (will be NaN for P6 rows): {sorted(only_in_jf)[:10]}{'...' if len(only_in_jf)>10 else ''}")

    # Concat with outer alignment
    combined = pd.concat([df314, jf28], ignore_index=True, sort=False)
    log(f"  combined rows: {len(combined)}")

    # Compute eta = |CRE_net| / LE per site
    cre = combined["ceres_toa_cre_net_mean"]
    le = combined["mean_LE"]
    eta = np.where(
        (le > 0) & np.isfinite(cre) & np.isfinite(le),
        np.abs(cre) / le,
        np.nan,
    )
    combined["eta"] = eta

    # Sanity check eta values
    n_eta = np.isfinite(eta).sum()
    log("")
    log(f"[eta] computed for {n_eta}/{len(combined)} sites")
    valid = combined.dropna(subset=["eta"])
    log(f"  median eta (n=314 FluxDataKit-only): "
        f"{valid[valid['source']=='FluxDataKit-v3']['eta'].median():.4f}")
    log(f"  median eta (n=28 JapanFlux2024-only): "
        f"{valid[valid['source']=='JapanFlux2024']['eta'].median():.4f}")
    log(f"  median eta (n=342 combined): {valid['eta'].median():.4f}")

    # Range check
    log(f"  eta range: [{valid['eta'].min():.4f}, {valid['eta'].max():.4f}]")
    extreme = valid[(valid["eta"] < 0.05) | (valid["eta"] > 0.50)]
    log(f"  sites outside [0.05, 0.50]: {len(extreme)}")
    if len(extreme):
        log("  extreme sites (first 10):")
        for _, r in extreme.head(10).iterrows():
            log(f"    {r['site_id']:10s}  igbp={r.get('igbp','?'):4s}  "
                f"eta={r['eta']:.3f}  LE={r['mean_LE']:.1f}  "
                f"CRE_net={r['ceres_toa_cre_net_mean']:+.1f}")

    # Tropical EBF report
    log("")
    log("[tropical EBF check]")
    trop_p6 = valid[(valid["igbp"] == "EBF") & (valid["latitude"].abs() <= 23.5)
                    & (valid["source"] == "FluxDataKit-v3")]
    trop_jf = valid[(valid["igbp"] == "EBF") & (valid["latitude"].abs() <= 23.5)
                    & (valid["source"] == "JapanFlux2024")]
    log(f"  P6 tropical EBF (FluxDataKit-only, n={len(trop_p6)}): "
        f"median eta = {trop_p6['eta'].median():.4f}")
    log(f"  JF tropical EBF (n={len(trop_jf)}): median eta = {trop_jf['eta'].median():.4f}")
    trop_all = valid[(valid["igbp"] == "EBF") & (valid["latitude"].abs() <= 23.5)]
    log(f"  combined tropical EBF (n={len(trop_all)}): median eta = {trop_all['eta'].median():.4f}")
    log("  combined tropical EBF detail:")
    for _, r in trop_all.iterrows():
        log(f"    {r['site_id']:10s}  lat={r['latitude']:+6.2f}  "
            f"eta={r['eta']:.3f}  LE={r['mean_LE']:.1f}  "
            f"CRE={r['ceres_toa_cre_net_mean']:+.1f}  source={r['source']}")

    combined.to_csv(OUT, index=False)
    log("")
    log(f"[write] {OUT}")
    log(f"  rows={len(combined)}, cols={len(combined.columns)}")

    with open(DIAG, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"[write] {DIAG}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
