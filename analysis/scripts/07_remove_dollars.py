"""
Paper 6 v5: surgical removal of all dollar valuation content.

Removes:
  * Table 3 (sensitivity of biophysical cooling valuation)
  * Section 6.7 (Forest valuation: scale-dependent application) including
    the dual-anchor disclosure paragraph
  * Abstract sentence with $86/$139 dollar values
  * Intro framing of "forest valuation" as one of three application classes
  * Contribution (v) on forest valuation in Section 1.2
  * Dollar values in Section 6.4 basin discussion (line 730)
  * Dollar mentions in Conclusions item 5/6
  * Five-mechanism dollar caveat (line 764)

Replaces "and forest valuation" framings with cleaner physics-only language.
Keeps:
  * Patch-vs-basin distinction (physical scale story)
  * Recycling amplification framework (purely physical)
  * Baker reference is removed where dollar-specific; kept where qualitative
  * Bunyard rebuttal (line 772) - keep but trim dollar coda

Run from manuscript/v5_rerun/.
"""
from __future__ import annotations
from pathlib import Path

P = Path("paper_body_v5.tex")
src = P.read_text(encoding="utf-8")

EDITS = []

# ─── 1. Abstract ────────────────────────────────────────────────────────────
EDITS.append((
    "Abstract: remove dollar application",
    "Despite its relevance to cloud feedback, biophysical forcing, and forest valuation, η has not been directly constrained",
    "Despite its relevance to cloud feedback and biophysical forcing, η has not been directly constrained",
))
EDITS.append((
    "Abstract: replace dollar application list with physics-only",
    "The constrained η supports several applications: a diagnostic for cloud feedback, a TOA counterpart to surface biophysical forcing, and a scale-dependent forest valuation ranging from \\$86/ha/yr for small isolated patches to \\$139/ha/yr for contiguous basin-scale forest.",
    "The constrained η supports two applications: a diagnostic for cloud feedback in atmospheric models, and an observational TOA counterpart to surface biophysical forcing estimates from land-cover-change studies.",
))
EDITS.append((
    "Abstract: trim 'and forest valuation studies' from closing",
    "with applications across cloud feedback, biophysical forcing, and forest valuation studies.",
    "with applications across cloud feedback and biophysical forcing studies.",
))

# ─── 2. Section 1.1 Introduction ────────────────────────────────────────────
EDITS.append((
    "§1.1 intro: remove 'determines biophysical cooling value of ecosystems'",
    "links surface energy partitioning to cloud radiative effects, and determines the biophysical cooling value of ecosystems that regulate land-atmosphere water fluxes.",
    "and links surface energy partitioning to cloud radiative effects.",
))
EDITS.append((
    "§1.1 intro: remove forest-valuation literature paragraph and rebalance",
    "Three literatures converge on η without constraining it directly. Cloud feedback studies (Sherwood et al., 2020; Zelinka et al., 2020; Ceppi and Nowack, 2021) quantify the TOA radiative response to warming and to cloud property changes, but do not resolve the TOA response to surface moisture flux variations that drive cloud formation. Biophysical forcing studies (Bright et al., 2017; Duveiller et al., 2018; Winckler et al., 2019) map surface-level temperature responses to land cover change using satellite retrievals and reanalysis, but stop short of the TOA radiative consequence that determines global-mean forcing. Forest valuation studies (Bonan, 2008; Alkama and Cescatti, 2016; Baker et al., 2026) monetise non-carbon cooling services, yet rely on assumed or inferred transfer fractions rather than direct observational constraints. Each of these literatures would benefit from an independently measured value of η: cloud feedback analyses need it to close the surface-flux branch of the feedback decomposition, biophysical forcing maps need it to translate surface signatures into TOA-relevant forcing, and valuation studies need it to replace assumed transfer efficiencies with observationally bounded ones.",
    "Two literatures converge on η without constraining it directly. Cloud feedback studies (Sherwood et al., 2020; Zelinka et al., 2020; Ceppi and Nowack, 2021) quantify the TOA radiative response to warming and to cloud property changes, but do not resolve the TOA response to surface moisture flux variations that drive cloud formation. Biophysical forcing studies (Bright et al., 2017; Duveiller et al., 2018; Winckler et al., 2019) map surface-level temperature responses to land cover change using satellite retrievals and reanalysis, but stop short of the TOA radiative consequence that determines global-mean forcing. Each of these literatures would benefit from an independently measured value of η: cloud feedback analyses need it to close the surface-flux branch of the feedback decomposition, and biophysical forcing maps need it to translate surface signatures into TOA-relevant forcing.",
))
EDITS.append((
    "§1.1 programme paragraph: remove 'forest valuation' from applications list",
    "and situates η within cloud feedback, biophysical forcing, and forest valuation applications.",
    "and situates η within the cloud feedback and biophysical forcing literatures.",
))

# ─── 3. Section 1.2 Contributions list ──────────────────────────────────────
EDITS.append((
    "§1.2 contributions: drop (v) forest valuation; rebalance closing sentence",
    "and (v) an application to forest valuation with scale-dependent recycling corrections that reconciles site-level and basin-level cooling service estimates. Together these results provide a dedicated, scale-stratified observational constraint on η, extending the preliminary site-level regression estimate of Shahid (2026b) to the basin scale and adding the mechanistic and geometric structure needed for application across cloud feedback diagnostics, biophysical forcing maps, and biosphere-based climate valuation.",
    "Together these results provide a dedicated, scale-stratified observational constraint on η, extending the preliminary site-level regression estimate of Shahid (2026b) to the basin scale and adding the mechanistic and geometric structure needed for application across cloud feedback diagnostics and biophysical forcing maps. Forest valuation applications building on this empirical constraint are developed in the companion cascade-valuation paper (Paper 8).",
))

# ─── 4. Mid-paper "for forest valuation, only CRE_net matters" ──────────────
EDITS.append((
    "Mid-paper: replace forest-valuation framing with TOA-budget-closure framing",
    "for forest valuation, only CRE\\_net matters: it is the quantity that",
    "For closing the TOA radiation budget, only CRE\\_net matters: it is the quantity that",
))

# ─── 5. Section 6.4 (basin) - drop dollar amplification sentence ────────────
EDITS.append((
    "§6.4: drop 'central valuation estimate rises from $86 to $139' sentence",
    "With recycling incorporated, the central valuation estimate rises from \\$86 to \\$139/ha/yr (applying the 1.62x amplification to the \\$86 central estimate). This recycling-corrected estimate is the appropriate basin-scale value for Amazon forest conservation decisions, accounting for the cumulative TOA cooling across all condensation events traceable to a given evapotranspiration source.",
    "The 1.62× amplification quantifies how basin-integrated forest sustains a larger TOA radiative cooling than the site-level value implies, because each unit of evapotranspiration drives multiple condensation events along the moisture-recycling corridor. Translating this physical amplification into a per-hectare conservation value is treated in Paper 8 (cascade valuation), where the social cost of carbon, counterfactual land cover, and scale-dependent attribution are handled with the auxiliary assumptions they require.",
))

# ─── 6. Section 6.4 closing: drop reference to Section 6.7 ──────────────────
EDITS.append((
    "§6.4: drop 'sets up the scale-dependent valuation developed in Section 6.7'",
    "This sets up the scale-dependent valuation developed in Section 6.7.",
    "The scale-dependence of η has direct implications for conservation accounting: a per-hectare radiative value derived from a contiguous basin cannot be applied unchanged to a fragmented landscape. Paper 8 develops this cascade explicitly.",
))

# ─── 7. Delete Table 3 (the sensitivity table) ──────────────────────────────
# Table 3 starts at the caption line and includes the full longtable block.
# We'll use a marker-based delete by finding the Table 3 caption start and
# the next blank line after \end{longtable}.
TABLE3_START = "\\textbf{Table 3.} Sensitivity of biophysical cooling valuation"
TABLE3_END_MARKER = "Shrubland (1.205) & 20.8\\% (basin) & \\$120 & \\$133 \\\\"

t3_start_idx = src.find(TABLE3_START)
if t3_start_idx >= 0:
    # find \end{longtable} after that
    end_table = src.find("\\end{longtable}", t3_start_idx)
    if end_table >= 0:
        # include the trailing }
        end_table = src.find("}\n", end_table)
        if end_table >= 0:
            end_table += 2
            # also strip following blank lines until non-blank content
            removed = src[t3_start_idx:end_table]
            src = src[:t3_start_idx] + src[end_table:]
            print(f"  [Table 3] removed {len(removed)} chars")
        else:
            print("  [Table 3] could not find closing brace after \\end{longtable}")
    else:
        print("  [Table 3] could not find \\end{longtable}")
else:
    print("  [Table 3] caption not found - already removed?")

# ─── 8. Delete Section 6.7 (Forest valuation: scale-dependent application) ──
SEC67_HEADER = "\\textbf{6.7 Forest valuation: scale-dependent application}"
NEXT_SECTION_HEADERS = [
    "\\textbf{6.8 ",
    "\\textbf{6.9 ",
    "\\textbf{6.10 ",
    "\\textbf{6.11 ",
    "\\textbf{7. ",
    "\\textbf{7.",
    "\\textbf{Conclusions",
    "\\textbf{Acknowledgements",
    "\\textbf{References",
]
s67 = src.find(SEC67_HEADER)
if s67 >= 0:
    # Find earliest occurrence of any next-section header
    end_67 = -1
    for h in NEXT_SECTION_HEADERS:
        idx = src.find(h, s67 + len(SEC67_HEADER))
        if idx >= 0 and (end_67 < 0 or idx < end_67):
            end_67 = idx
    if end_67 > 0:
        removed = src[s67:end_67]
        src = src[:s67] + src[end_67:]
        print(f"  [§6.7] removed {len(removed)} chars")
    else:
        print("  [§6.7] could not find next section header")
else:
    print("  [§6.7] header not found - already removed?")

# ─── 9. Conclusions item 5/6 about valuation - replace with physics-only ─────
EDITS.append((
    "Conclusions item 5/6: remove $86 / $139 dollar anchoring",
    "operates simultaneously as a cloud feedback diagnostic, as the TOA\ncounterpart to the surface biophysical forcing coefficient\n$\\alpha(\\beta)$, and as a valuation anchor for forest biophysical\nservices. The recycling-corrected value of intact Amazon rainforest\nvia the TOA radiative pathway is \\$86/ha/yr at the small-patch scale\nand \\$139/ha/yr at the basin-integrated scale, representing a\nscale-dependent envelope rather than a single point estimate.",
    "operates simultaneously as a cloud feedback diagnostic and as\nthe TOA counterpart to the surface biophysical forcing coefficient\n$\\alpha(\\beta)$. The 1.62$\\times$ recycling amplification from site to\nbasin scale is a physical property of the η-ρ system, independent of\nany particular valuation framework. Translating this scale-dependent\nphysical envelope into per-hectare radiative value, with the auxiliary\nassumptions on social cost of carbon and counterfactual land cover,\nis the subject of Paper 8 (cascade valuation).",
))

# ─── 10. Five-mechanism dollar caveat (line 764) - replace with physics ──────
EDITS.append((
    "§6.x: rewrite dollar caveat about 5-mechanism integration",
    "The valuation range of \\$15 to \\$228 per hectare per year should therefore be understood as a lower bound on one component of the total biophysical value of tropical forests. Integrating across the four additional mechanisms requires separate accounting frameworks; the transfer fraction simply provides a rigorous observational anchor for the TOA radiative component, leaving the other arms to be valued on their own terms.",
    "The TOA radiative pathway is one of several biophysical mechanisms by which intact tropical forest regulates climate. The four others (surface albedo modification, surface roughness and sensible-heat partitioning, evapotranspiration-mediated boundary-layer dynamics, and downwind precipitation sustained by moisture recycling) operate on overlapping spatial and temporal scales. The transfer fraction reported here provides a rigorous observational anchor for the TOA radiative arm; integrating across all five mechanisms is the subject of Paper 8.",
))

# ─── 11. Bunyard rebuttal: trim 'valuation implications differ' coda ──────
EDITS.append((
    "Bunyard discussion: trim valuation coda",
    "The Bunyard et al. (2024) gross-LE framing and the net-CRE framing used here therefore address distinct quantities and are not directly comparable on the same axis. The valuation implications differ correspondingly.",
    "The Bunyard et al. (2024) gross-LE framing and the net-CRE framing used here therefore address distinct quantities and are not directly comparable on the same axis.",
))

# Apply remaining text-based EDITS
applied = 0
missed = []
for label, old, new in EDITS:
    n = src.count(old)
    if n == 1:
        src = src.replace(old, new)
        applied += 1
        print(f"  OK: {label}")
    elif n == 0:
        missed.append(label)
        print(f"  MISS: {label}")
    else:
        missed.append(f"{label} (ambig: {n} matches)")
        print(f"  AMBIG ({n}x): {label}")

P.write_text(src, encoding="utf-8")
print()
print(f"Applied {applied}/{len(EDITS)} text edits")
if missed:
    print(f"Skipped: {len(missed)}")
    for m in missed:
        print(f"  - {m}")
print()
print(f"Final paper_body_v5.tex: {P.stat().st_size} bytes "
      f"({len(P.read_text(encoding='utf-8').splitlines())} lines)")
