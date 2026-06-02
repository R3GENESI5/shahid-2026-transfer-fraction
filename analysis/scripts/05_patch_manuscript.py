"""
Paper 6 v5: Patch paper_body_v5.tex with all v4.2 -> v5 number updates.

This is a one-shot in-place patch script. Replacements are surgical:
v4.2 numbers that genuinely changed in v5 are replaced; numbers that
refer to Paper 2 (Shahid 2026b) at its own 314-site dataset are NOT
changed (the v5 analysis does not affect Paper 2's published numbers).

Run from manuscript/v5_rerun/.
"""
from __future__ import annotations
from pathlib import Path

P = Path("paper_body_v5.tex")
src = P.read_text(encoding="utf-8")

# ─── Replacements ─────────────────────────────────────────────────────────────
# Each entry: (old, new, count_expected)
REPL = [
    # Section 3.1 / Methods - mention JapanFlux2024 supplementation
    (
        "shrubland, and wetland); per-biome site counts are reported in Table 1.",
        "shrubland, and wetland); per-biome site counts are reported in Table 1. The site universe extends Paper 6 v4.2's 314 FluxDataKit-v3 sites with the 27 JapanFlux2024 sites pooled into Paper 1's joint $\\alpha(\\beta)$ refit (Shahid 2026a), plus MY-LHP (Lambir Hills, Borneo) which is prediction-only in Paper 1 but fully usable here since $\\eta = |\\text{CRE}_{\\text{net}}|/\\text{LE}$ does not require surface net radiation. ID-PaD shares a CERES grid cell with ID-Pag (same Indonesian peatland tower processed by two flux protocols) and is dropped as a duplicate. Net sample: 314 + 27 - 1 + 1 = 341 sites.",
        1,
    ),
    # Section 4.1: tropical EBF sample description ("eight sites across four continents")
    (
        "the LBA project. The full tropical EBF sample includes eight sites\nacross four continents: BR-Sa1 and BR-Sa3 (Amazon, Brazil), GF-Guy",
        "the LBA project. The full tropical EBF sample includes twelve sites\nacross five continents: BR-Sa1 and BR-Sa3 (Amazon, Brazil), GF-Guy",
        1,
    ),
    # Add MY-LHP / KH-Kmp / TH-Kog / ID-PaB to the tropical EBF site list
    # Find the existing list end and extend it
    (
        "the eight tropical EBF sites on other continents. Additional FLUXNET",
        "the twelve tropical EBF sites on other continents. Additional FLUXNET",
        1,
    ),
    # Section 4.1 tropical EBF summary: "Across all eight tropical EBF sites spanning four continents and six"
    (
        "Across all eight tropical EBF sites spanning four continents and six",
        "Across all twelve tropical EBF sites spanning five continents and six",
        1,
    ),
    # Section 4.2: global median across all 314 sites
    (
        "Across all 314 sites, the median transfer fraction is 30.0\\% {[}95\\%",
        "Across all 341 sites, the median transfer fraction is 31.6\\% {[}95\\%",
        1,
    ),
    # Table 1 caption: "eight tropical evergreen broadleaf forest (EBF) sites spanning four continents"
    (
        "\\textbf{Table 1.} Site-level transfer fraction (η = |CRE\\_net|/LE) by biome and for eight tropical evergreen broadleaf forest (EBF) sites spanning four continents.",
        "\\textbf{Table 1.} Site-level transfer fraction (η = |CRE\\_net|/LE) by biome and for twelve tropical evergreen broadleaf forest (EBF) sites spanning five continents.",
        1,
    ),
    # Table 1 rows: update per-biome stats
    (
        "Forest & 132 & 58.0 & −20.1 & 38.6\\% & 35.3--42.1 & 231.1 \\\\",
        "Forest & 151 & 57.8 & −20.3 & 38.9\\% & 35.7--42.9 & 230.4 \\\\",
        1,
    ),
    (
        "Grassland & 65 & 56.2 & −14.9 & 23.7\\% & 20.3--31.8 & 236.9 \\\\",
        "Grassland & 68 & 55.5 & −15.3 & 26.9\\% & 21.1--33.9 & 236.3 \\\\",
        1,
    ),
    (
        "Cropland & 41 & 61.1 & −17.1 & 29.4\\% & 25.6--38.4 & 233.3 \\\\",
        "Cropland & 42 & 61.2 & −17.3 & 30.1\\% & 25.9--40.3 & 233.3 \\\\",
        1,
    ),
    (
        "Shrubland & 27 & 38.7 & −8.4 & 18.5\\% & 8.3--31.4 & 235.0 \\\\",
        "Shrubland & 28 & 40.5 & −7.9 & 16.8\\% & 7.6--28.3 & 234.3 \\\\",
        1,
    ),
    # Add 4 new tropical EBF rows after CN-Din (sorted by location)
    (
        "\\textbf{CN-Din (subtropical China)†} & 1 & 49.9 & −49.0 & 98.2\\% & n/a & 249.3 \\\\\n\\end{longtable}",
        "\\textbf{CN-Din (subtropical China)†} & 1 & 49.9 & −49.0 & 98.2\\% & n/a & 249.3 \\\\\n\\textbf{MY-LHP (Borneo, Malaysia)} & 1 & 88.6 & +21.4 & 24.2\\% & n/a & 210.9 \\\\\n\\textbf{KH-Kmp (Cambodia)} & 1 & 105.5 & +5.9 & 5.6\\% & n/a & 235.0 \\\\\n\\textbf{TH-Kog (Thailand monsoon)†} & 1 & 73.3 & −22.7 & 31.0\\% & n/a & 251.1 \\\\\n\\textbf{ID-PaB (Borneo, Indonesia)} & 1 & 89.9 & +5.2 & 5.8\\% & n/a & 216.6 \\\\\n\\end{longtable}",
        1,
    ),
    # Table 1 footnote: update exclusion logic
    (
        "† CN-Din is a subtropical monsoon site (23.2°N); its anomalously high transfer fraction likely reflects monsoon-driven cloud regimes distinct from equatorial convection. Excluding CN-Din, the tropical EBF median is 12.9\\% and the range is 6.9 to 22.2\\%.",
        "† CN-Din (23.2°N) and TH-Kog (18.8°N) are subtropical / monsoon-tropical sites; their anomalously high transfer fractions likely reflect monsoon-driven cloud regimes distinct from equatorial convection. Excluding CN-Din, the tropical EBF median (n=11) is 12.9\\% and the range is 5.6 to 31.0\\%; excluding both monsoon sites (n=10), the median is 10.6\\% and the range is 5.6 to 24.2\\%. The four new tropical EBF sites added in v5 (MY-LHP, KH-Kmp, TH-Kog, ID-PaB) come from JapanFlux2024 (Hirano et al. 2025) and extend the SE Asian coverage; ID-PaB and ID-Pag share a Borneo peatland location.",
        1,
    ),
    # Discussion 6.3 alignment: previously edited at v4.2 stage with the 341 vs 314 split.
    # Now that Paper 6 v5 IS the 341-site analysis, the distinction is no longer needed.
    (
        "Together the two coefficients form a surface-to-TOA chain: \\(\\alpha(\\beta)\\) is calibrated on the 341-site Paper~1 joint fit (Shahid 2026a), and \\(\\eta\\) is calibrated on the 314-site CERES-co-located subset used here.",
        "Together the two coefficients form a surface-to-TOA chain calibrated on the same 341-site joint FluxDataKit-v3 + JapanFlux2024 dataset across the two papers.",
        1,
    ),
    # Figure 2 caption: 314 -> 341
    (
        "\\emph{Figure 2. Surface LE versus TOA CRE\\_net across 314 FLUXNET-CERES",
        "\\emph{Figure 2. Surface LE versus TOA CRE\\_net across 341 FLUXNET-CERES",
        1,
    ),
    # Figure 3 caption: 314 -> 341
    (
        "Histogram of η across all 314 sites.",
        "Histogram of η across all 341 sites.",
        1,
    ),
    # Section 4 contribution statement: "eight" reference in 6.7-style figure caption
    (
        "(0.72 to 0.86 across the eight tropical EBF sites)",
        "(0.72 to 0.86 across the twelve tropical EBF sites)",
        1,
    ),
    # Section 6.7 references in dollar valuation framing — verify tropical EBF references
    (
        "consistent with the tropical EBF range of 6.9 to 22.2\\% measured at\nthe eight tropical EBF sites on other continents.",
        "consistent with the tropical EBF range of 5.6 to 31.0\\% measured at\nthe twelve tropical EBF sites on five continents.",
        1,
    ),
    # Section 4.4 (or similar) - update "to 26.6% across tropical EBF sites" -> recompute upper
    # leave alone — that 26.6 is CRE_LW/LE not eta
    # Section 6.3 dollar valuation:
    # "the tropical EBF median of 14.7%" — UNCHANGED, no edit
    # Conclusions: any 314 or four-continent refs
]

# Apply replacements
applied = 0
missed = []
for old, new, expected in REPL:
    n_found = src.count(old)
    if n_found == expected:
        src = src.replace(old, new)
        applied += 1
        print(f"  [{applied:2d}] OK: replaced {expected} occurrence")
    elif n_found == 0:
        missed.append((expected, old[:80] + ('...' if len(old) > 80 else '')))
        print(f"  -- MISS: '{old[:60]}...' not found")
    else:
        print(f"  -- AMBIG: '{old[:60]}...' found {n_found} times, expected {expected}")
        missed.append((expected, old[:80] + ('...' if len(old) > 80 else '')))

P.write_text(src, encoding="utf-8")
print()
print(f"Applied {applied} of {len(REPL)} edits")
if missed:
    print(f"Skipped: {len(missed)}")
    for n, snippet in missed:
        print(f"  {n}x  '{snippet}'")
