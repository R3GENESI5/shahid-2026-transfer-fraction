# TOA Radiative Forest Valuation — Practitioner Guide

**Source**: Shahid (2026). Empirical constraints on the fraction of surface latent heat flux reaching the top of atmosphere as net radiative cooling. ESSOAr preprint.

**Purpose**: This guide lets a user put up a defensible case for the biophysical cooling value of a specific forest area, using empirically constrained TOA radiative transfer fractions. It covers what number to use, how to compute the value, worked examples, and what the number does and does not capture.

---

## 1. Decide which η to use (2 steps)

### Step 1 — Classify the forest area by size

| Area classification | Threshold | Applicable η | Central $/ha/yr |
|--------------------|-----------|--------------|-----------------|
| **Small patch** | < ~50 km across, or plantation, or isolated restoration plot | **12.9%** (single-site BR-Sa1 anchor) | **$86** |
| **Basin-scale contiguous forest** | Large contiguous tropical forest (Amazon, Congo, SE Asia; areas that sustain internal moisture recycling) | **20.8%** (basin-scale, Amazon reference) | **$139** |
| **Intermediate** | 50 km to basin-scale | Interpolate using ρ | See §3 |

The threshold is the characteristic moisture recycling length scale in deep tropical convection. Below it, a forest's own evapotranspiration is advected away before it can re-condense downwind over the same forest, so only single-pass TOA radiative cooling applies. Above it, the forest sustains internal moisture recycling that amplifies TOA cooling by a factor of ~1.6 relative to the BR-Sa1 single-site anchor.

### Step 2 — Choose the social cost of carbon (SCC) anchor

| SCC anchor | Reference | $/ha/yr at 12.9% site | $/ha/yr at 20.8% basin |
|-----------|-----------|----------------------|-----------------------|
| $51 | Conservative / US government 2023 | $36 | $58 |
| **$120** | **Default / this paper's central value** | **$86** | **$139** |
| $200 | Near-term Ramsey estimate | $143 | $232 |

This guide uses **$86/ha/yr** for small patches and **$139/ha/yr** for basin-scale contiguous forest because those two values are arithmetically consistent with the observed **1.62x** recycling amplification. The small-patch valuation anchor is therefore the **BR-Sa1 single-site value of 12.9%**. The broader tropical evergreen broadleaf forest median of **14.7%** remains a paper-level biome statistic, but it is not the valuation anchor used for the dollar figures in this guide.

---

## 2. Core valuation table

This is the table to copy into a case study or valuation memo.

| Counterfactual land cover | Transfer η | SCC ($/tCO₂) | Valuation ($/ha/yr) | Notes |
|---------------------------|-----------|--------------|---------------------|-------|
| Pasture | 6% | $51 | $15 | Conservative lower bound |
| Pasture | 12.9% site | $51 | $36 | Site-scale, low SCC |
| Pasture | 20.8% basin | $51 | $58 | Basin-scale, low SCC |
| Pasture | 6% | $120 | $35 | Conservative, default SCC |
| **Pasture** | **12.9% site (small patch)** | **$120** | **$86** | **Central small-patch estimate** |
| **Pasture** | **20.8% basin (contiguous)** | **$120** | **$139** | **Central basin-scale estimate** |
| Pasture | 6% | $200 | $58 | Conservative, high SCC |
| Pasture | 12.9% site | $200 | $143 | Site, high SCC |
| Pasture | 20.8% basin | $200 | $232 | Basin, high SCC |
| Shrubland | 12.9% site | $120 | $94 | Alternative counterfactual |
| Shrubland | 20.8% basin | $120 | $133 | Alternative counterfactual |

**Central recommended estimates are bolded.** Use these unless you have a specific reason to deviate.

---

## 3. Computation method (if you need to derive a custom value)

### Formula

```
Valuation ($/ha/yr) = η × ΔR_net × 10⁻⁶ × 365 × 86400 × SCC / M_CO₂
```

Where:

| Symbol | Meaning | Units | Typical value |
|--------|---------|-------|---------------|
| η | Transfer fraction | unitless | 0.129 (small patch, BR-Sa1 anchor) or 0.208 (basin) |
| ΔR_net | Surface radiative forcing differential between intact forest and counterfactual land cover | W/m² | 82.5 to 92.2 W/m² (pasture counterfactual, BR-Sa1 reference) |
| 10⁻⁶ × 365 × 86400 | Convert W/m² × ha × yr to equivalent tonnes CO₂ at 1 tCO₂ per 275 GJ (approximation) | — | — |
| SCC | Social cost of carbon | $/tCO₂ | $120 default |
| M_CO₂ | Molar mass CO₂ | kg/mol | 44.01 |

Practically, use the table in §2. The formula is here for auditability.

### Intermediate-scale forest (between small patch and basin)

If your forest is 50 km to 500 km across, interpolate using the recycling ratio ρ:

```
η_intermediate = η_site / (1 − ρ)
```

Published Amazon ρ values range from 0.25 (eastern basin) to 0.67 (western interior), with a mean near 0.38–0.40. For an intermediate-scale contiguous forest, start with ρ = 0.25 and work up based on the fraction of local precipitation that originates from upwind forest within the project boundary.

Example: a 200,000 ha contiguous forest corridor. Assume ρ = 0.25 (conservative) → η = 12.9 / (1 − 0.25) = 17.2%. At SCC $120, this interpolates to roughly $115/ha/yr.

---

## 4. Worked example: Amazon basin (conservation case)

**Scenario**: 5.5 million ha of intact contiguous Amazon rainforest threatened by conversion to pasture.

**Applicable values**:
- Scale: basin-wide contiguous → η = **20.8%**
- Counterfactual: pasture (empirically observed arc-of-deforestation land cover)
- SCC: $120/tCO₂ (default)

**Valuation**: $139/ha/yr × 5.5 × 10⁶ ha = **$764 million per year** in TOA radiative cooling services alone.

**Sensitivity**:
- At $51 SCC: $58 × 5.5M = $319 million/yr
- At $200 SCC: $232 × 5.5M = $1.28 billion/yr
- Range: $319M to $1.28B annually depending on SCC choice

**Comparison to existing markets**:
- Current Amazon forest carbon offsets at $50/tCO₂ yield approximately $50/ha/yr
- TOA radiative valuation at basin scale is approximately 2.8× higher than this carbon-only valuation

---

## 5. What this number captures

The $86 to $139/ha/yr represents only one component of total forest biophysical value: **net TOA radiative cooling via cloud radiative effects driven by surface latent heat flux**. Specifically:

- Surface LE drives cloud formation
- Clouds reflect shortwave (CRE_SW, cooling)
- Clouds also trap longwave (CRE_LW, warming)
- Net effect (CRE_net) = residual cooling after cloud self-blocking
- Fraction of surface LE that becomes net TOA cooling = η

---

## 6. What this number does NOT capture (important caveats)

Do not present the $86 to $139/ha/yr as the total cooling value. It excludes:

1. **Surface cooling.** Forests reduce local land surface temperature by 2 to 8 °C relative to cleared land through evapotranspiration. This operates independently of the TOA radiative pathway and has direct human welfare value (heat mortality, agricultural yield, energy demand).

2. **Rainfall generation.** Amazon forests generate approximately 300 ± 110 L/m²/yr of downwind rainfall (Baker et al., 2026), valued at approximately $59/ha/yr, through moisture recycling that is complementary to but not captured by the TOA pathway.

3. **Continental moisture transport.** The biotic pump mechanism sustains moisture advection from the coast to the continental interior, valued separately through rainfall-dependent agriculture and urban water supply.

4. **Tipping-point prevention.** Amazon deforestation beyond approximately 20 to 40% basin loss may trigger a self-reinforcing transition to savanna, with global climate-system consequences.

5. **Biodiversity, carbon storage, cultural value, soil stabilization, non-Amazon ecosystem services.**

**Recommended framing for a valuation case**: present the $86 to $139/ha/yr as a **lower bound on a single component**, not as the total cooling value.

---

## 7. Template language for valuation memos

> "Based on the first dedicated observational constraint on the surface latent heat to top-of-atmosphere transfer fraction (Shahid, 2026), the TOA radiative cooling value of [project area] is [$86 or $139]/ha/yr (central estimate at social cost of carbon $120/tCO₂), or [$X million]/yr in aggregate. This valuation reflects only the TOA radiative pathway and excludes surface cooling, rainfall generation, continental moisture transport, and tipping-point prevention. The total biophysical cooling value of the project is therefore at least this magnitude, with substantial upside from the excluded components."

---

## 8. Confidence caveats

- The η = 20.8% Amazon basin value is based on CERES EBAF Ed4.2 TOA radiation and FLUXNET surface LE observations across 2003 to 2023.
- The η = 12.9% small-patch valuation anchor is the direct-ratio single-site estimate at BR-Sa1 (Tapajos, Amazon).
- The broader tropical evergreen broadleaf forest median is 14.7% across 8 sites spanning 4 continents.
- The 95% CI on the global η distribution is 27.1 to 34.5%; tropical EBF ranges from 6.9 to 22.2%.
- The numerical values are observationally constrained, not model-derived.
- Independent reconciliation with Paper 2 (Shahid, 2026b) site-level transfer fraction of 8.5% using a regression-based estimator is discussed in Section 6.9 of the source paper; the direct-ratio estimator used here retains the BR-Sa1 12.9% anchor for valuation consistency with the observed 20.8% basin estimate and 1.62x amplification.

---

## Citation

Shahid, A. B. (2026). Empirical constraints on the fraction of surface latent heat flux reaching the top of atmosphere as net radiative cooling. ESSOAr preprint.

## Questions for the valuation practitioner

Before applying this guide, confirm:

- [ ] Is the forest area >50 km contiguous (use basin η) or <50 km / plantation (use site η)?
- [ ] Is the counterfactual land cover pasture, shrubland, or savanna? (Pasture is default; shrubland slightly higher; savanna similar)
- [ ] Which SCC anchor does your jurisdiction use? ($51, $120, or $200)
- [ ] Are you presenting this as total forest cooling value (WRONG) or as a lower bound on one component (CORRECT)?
