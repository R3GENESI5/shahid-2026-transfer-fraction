"""
Paper 6 v5: build DOCX from paper_body_v5.tex via pandoc, then clean up with
python-docx.

Two-stage pipeline:
  1. pandoc paper_body_v5.tex -> Shahid_2026_v5.docx (skeleton with figures
     embedded, equations rendered as Word OMML, tables converted from longtable)
  2. python-docx post-processing:
     - title page (title, author, ORCID, version)
     - normalise font to Arial 11 throughout (matching v5 fig1 style)
     - size figures to 6.5 inches wide (page width minus margins)
     - section heading styles (level 1, 2)
     - footer page numbers
     - reference list formatting

Outputs:
  Shahid_2026_v5.docx (main manuscript)
  Shahid_2026_v5_Supplementary.docx (supplement)

Both files paginated cleanly for journal submission.
"""
from __future__ import annotations
import subprocess
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

HERE = Path(__file__).resolve().parent
BODY_TEX = HERE / "paper_body_v5.tex"
SUPP_TEX = HERE / "supp_body_v5.tex"
MAIN_DOCX = HERE / "Shahid_2026_v5.docx"
SUPP_DOCX = HERE / "Shahid_2026_v5_Supplementary.docx"


def pandoc_convert(tex_path: Path, docx_path: Path) -> None:
    """Run pandoc with options tuned for LaTeX manuscript -> Word docx."""
    cmd = [
        "pandoc",
        str(tex_path),
        "-f", "latex",
        "-t", "docx",
        "-o", str(docx_path),
        "--resource-path", str(HERE),     # so ./figures/... resolves
        "--standalone",
        "--mathml",                        # equations as Word-native OMML
        "--wrap=preserve",
    ]
    print(f"[pandoc] {tex_path.name} -> {docx_path.name}")
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    if result.returncode != 0:
        print("STDOUT:", result.stdout[:500])
        print("STDERR:", result.stderr[:500])
        raise RuntimeError(f"pandoc failed (exit {result.returncode})")
    print(f"  ok: {docx_path.stat().st_size / 1024:.1f} KB")


def normalise_font(doc: Document, font_name: str = "Arial",
                   font_size_pt: float = 11.0) -> None:
    """Apply Arial 11 (or specified) to every run in every paragraph + table."""
    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.name = font_name
            run.font.size = Pt(font_size_pt)
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = font_name
                        run.font.size = Pt(font_size_pt - 1)  # slightly smaller in tables


def fit_figures(doc: Document, width_inches: float = 6.5) -> None:
    """Resize all embedded images to a target page-width."""
    from docx.shared import Emu
    for shape in doc.inline_shapes:
        # shape.width and .height are EMUs; preserve aspect ratio
        orig_w = shape.width
        orig_h = shape.height
        new_w = Inches(width_inches)
        ratio = new_w / orig_w
        shape.width = new_w
        shape.height = int(orig_h * ratio)


def restyle_pandoc_title(doc: Document) -> None:
    """Pandoc converts the LaTeX `\\textbf{Title}` block into the first few
    paragraphs of the docx. Restyle them as a proper title block instead of
    adding a duplicate title page above.

    Expects paragraph order from pandoc:
      [0] title
      [1] author
      [2] affiliation + ORCID
      [3] version line
      [4] (Abstract heading) — leave alone
    """
    if len(doc.paragraphs) < 4:
        return
    title_p = doc.paragraphs[0]
    author_p = doc.paragraphs[1]
    affil_p = doc.paragraphs[2]
    ver_p = doc.paragraphs[3]

    # Title
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in title_p.runs:
        run.font.name = "Arial"
        run.font.size = Pt(16)
        run.bold = False  # explicit: no bold per v5 style choice

    # Author
    author_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in author_p.runs:
        run.font.name = "Arial"
        run.font.size = Pt(12)
        run.bold = False

    # Affiliation / ORCID
    affil_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in affil_p.runs:
        run.font.name = "Arial"
        run.font.size = Pt(10)
        run.italic = True

    # Version
    ver_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in ver_p.runs:
        run.font.name = "Arial"
        run.font.size = Pt(10)
        run.italic = False
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)


def add_page_numbers(doc: Document) -> None:
    """Add 'Page N of M' page-number field in the footer."""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    section = doc.sections[0]
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.clear()

    run = p.add_run()
    run.font.name = "Arial"
    run.font.size = Pt(9)

    # PAGE field
    fld1 = OxmlElement("w:fldSimple")
    fld1.set(qn("w:instr"), "PAGE")
    r1 = OxmlElement("w:r")
    t1 = OxmlElement("w:t")
    t1.text = "1"
    r1.append(t1)
    fld1.append(r1)

    run._element.append(fld1)
    run._element.append(OxmlElement("w:t"))
    run._element[-1].text = " of "

    fld2 = OxmlElement("w:fldSimple")
    fld2.set(qn("w:instr"), "NUMPAGES")
    r2 = OxmlElement("w:r")
    t2 = OxmlElement("w:t")
    t2.text = "1"
    r2.append(t2)
    fld2.append(r2)
    run._element.append(fld2)


# ── Table data (v5 values; replaces pandoc-corrupted longtable conversion) ──
TABLE1_ROWS = [
    ("Biome / Site",                       "N",   "LE (W m⁻²)", "CRE_net", "Median η", "95% CI",     "OLR (W m⁻²)"),
    # Per-biome
    ("Forest",                             "151", "57.8",                 "−20.3", "38.9%",      "35.7–42.9", "230.4"),
    ("Grassland",                          "68",  "55.5",                 "−15.3", "26.9%",      "21.1–33.9", "236.3"),
    ("Cropland",                           "42",  "61.2",                 "−17.3", "30.1%",      "25.9–40.3", "233.3"),
    ("Savanna",                            "22",  "55.5",                 "−5.5",  "14.9%",      "7.6–18.4",  "256.6"),
    ("Shrubland",                          "28",  "40.5",                 "−7.9",  "16.8%",      "7.6–28.3",  "234.3"),
    ("Wetland",                            "26",  "60.1",                 "−16.7", "30.0%",      "23.5–45.3", "225.2"),
    ("Barren/Snow",                        "1",   "28.4",                 "−7.0",  "24.7%",      "n/a",            "206.0"),
    # Tropical EBF individual sites
    ("BR-Sa1 (Amazon, Brazil)",            "1",   "87.1",                 "−11.2", "12.9%",      "n/a",            "240.2"),
    ("BR-Sa3 (Amazon, Brazil)",            "1",   "111.0",                "−18.3", "16.5%",      "n/a",            "237.4"),
    ("GF-Guy (French Guiana)",             "1",   "99.3",                 "−21.0", "21.1%",      "n/a",            "252.4"),
    ("AU-Rob (tropical Australia)",        "1",   "126.7",                "−28.2", "22.2%",      "n/a",            "265.1"),
    ("AU-Ctr (tropical Australia)",        "1",   "122.0",                "−8.4",  "6.9%",       "n/a",            "264.1"),
    ("AU-Cow (tropical Australia)",        "1",   "102.2",                "−8.4",  "8.2%",       "n/a",            "264.1"),
    ("ID-Pag (Borneo, Indonesia)",         "1",   "97.8",                 "+6.9",       "7.1%",       "n/a",            "214.9"),
    ("CN-Din (subtropical China)†",   "1",   "49.9",                 "−49.0", "98.2%",      "n/a",            "249.3"),
    ("MY-LHP (Borneo, Malaysia)",          "1",   "88.6",                 "+21.4",      "24.2%",      "n/a",            "210.9"),
    ("KH-Kmp (Cambodia)",                  "1",   "105.5",                "+5.9",       "5.6%",       "n/a",            "235.0"),
    ("TH-Kog (Thailand monsoon)†",    "1",   "73.3",                 "−22.7", "31.0%",      "n/a",            "251.1"),
    ("ID-PaB (Borneo, Indonesia)",         "1",   "89.9",                 "+5.2",       "5.8%",       "n/a",            "216.6"),
]

TABLE2_ROWS = [
    ("Source",                       "Scale / sample",          "η estimate",            "Method"),
    ("Shahid 2026b (Paper 2)",       "Site (314 FLUXNET)",      "8.5% (5.9–29.8%)",      "α(β)–CRE regression slope"),
    ("Bunyard et al. 2024",          "Amazon estimate",         "75–100%",               "Top-down gross LE budget"),
    ("Baker et al. 2026",            "Amazon rainfall monetisation", "Indirect; converges with site-level range", "Rainfall-derived indirect estimator"),
    ("This study (site)",            "Tropical EBF median",     "14.7% (5.6–31.0%)",     "Direct |CRE_net|/LE ratio"),
    ("This study (basin)",           "Amazon integrated",       "20.8%",                      "Basin polygon aggregation"),
]

# Supplement Tables — same need for clean rebuild because pandoc longtable conversion
# garbles cell alignment (same failure mode as main paper Tables 1 and 2).
TABLE_S1_ROWS = [
    ("Day", "Mean |latitude|", "Mean OLR (W m⁻²)", "Enhancement (W m⁻²)", "Standard deviation"),
    ("0",   "2.7",              "233.4",                "+1.3",                     "1.4"),
    ("5",   "16.2",             "270.3",                "+38.2",                    "14.8"),
    ("10",  "20.7",             "275.0",                "+42.9",                    "15.4"),
    ("15",  "22.5",             "276.3",                "+44.2",                    "14.7"),
    ("20",  "22.9",             "276.7",                "+44.6",                    "15.3"),
]

TABLE_S2_ROWS = [
    ("Month", "Amazon OLR (W m⁻²)", "Atlantic OLR (W m⁻²)", "Difference (W m⁻²)", "Interpretation"),
    ("Jan",   "273.3",                    "287.9",                      "−14.6",                  "Atlantic higher"),
    ("Apr",   "273.9",                    "256.4",                      "+17.5",                       "Amazon higher"),
    ("Jul",   "265.2",                    "269.0",                      "−3.8",                   "Similar"),
    ("Oct",   "272.1",                    "267.9",                      "+4.2",                        "Similar"),
    ("Mean",  "271.1",                    "270.3",                      "+0.8",                        "No consistent signal"),
]


def find_table_by_marker(doc: Document, marker_text: str):
    """Return (table, caption_paragraph) where the table caption begins with marker_text."""
    paragraphs = list(doc.paragraphs)
    for i, p in enumerate(paragraphs):
        if marker_text in p.text:
            # The next table in document order is the one tied to this caption
            # We need iter order through the body
            body_iter = list(doc.element.body.iterchildren())
            cap_idx = None
            for j, child in enumerate(body_iter):
                if child is p._p:
                    cap_idx = j
                    break
            if cap_idx is None:
                continue
            # Find next w:tbl element after cap_idx
            for k in range(cap_idx + 1, len(body_iter)):
                if body_iter[k].tag.endswith("}tbl"):
                    # Match it against doc.tables
                    for t in doc.tables:
                        if t._tbl is body_iter[k]:
                            return t, p
            return None, p
    return None, None


def replace_table_in_place(table, rows_data) -> None:
    """Wipe a table's existing rows and refill from rows_data (list of tuples)."""
    n_cols = len(rows_data[0])

    # Remove all existing rows
    tbl = table._tbl
    for tr in list(tbl.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr")):
        tbl.remove(tr)

    # Add new rows with the right column count
    for row_data in rows_data:
        row = table.add_row()
        # Pad row if it has fewer cells than required
        while len(row.cells) < n_cols:
            row.add_cell  # placeholder; python-docx adds cells automatically based on grid
        # Set cell text
        for col_idx, val in enumerate(row_data):
            if col_idx >= len(row.cells):
                break
            cell = row.cells[col_idx]
            cell.text = str(val)
            for para in cell.paragraphs:
                for r in para.runs:
                    r.font.name = "Arial"
                    r.font.size = Pt(9)
        # First row = header: make bold
        if row_data is rows_data[0]:
            for col_idx in range(min(n_cols, len(row.cells))):
                cell = row.cells[col_idx]
                for para in cell.paragraphs:
                    for r in para.runs:
                        r.bold = True


def rebuild_tables(doc: Document, kind: str = "main") -> None:
    """Replace pandoc-corrupted tables with clean python-docx tables.

    kind = "main" rebuilds Table 1 and Table 2 (main paper).
    kind = "supp" rebuilds Table S1 and Table S2 (supplement).
    """
    if kind == "main":
        spec = [("Table 1.", TABLE1_ROWS, "Table 1"),
                ("Table 2.", TABLE2_ROWS, "Table 2")]
    elif kind == "supp":
        spec = [("Table S1.", TABLE_S1_ROWS, "Table S1"),
                ("Table S2.", TABLE_S2_ROWS, "Table S2")]
    else:
        raise ValueError(f"unknown kind: {kind}")

    for marker, rows, label in spec:
        t, _ = find_table_by_marker(doc, marker)
        if t is not None:
            replace_table_in_place(t, rows)
            print(f"  rebuilt {label} ({len(rows)} rows)")
        else:
            print(f"  WARN: {label} marker not found")


def post_process(docx_path: Path, add_title: bool = True,
                 table_kind: str | None = "main") -> None:
    """Apply python-docx cleanups to a pandoc-generated docx.

    table_kind: "main" for main paper Table 1/2, "supp" for S1/S2, None to skip.
    """
    print(f"[post] {docx_path.name}")
    doc = Document(str(docx_path))

    # Normalise body font first (Arial 11 across all paragraphs and tables)
    normalise_font(doc, "Arial", 11.0)

    # Then restyle the pandoc-extracted title block so it stands out
    if add_title:
        restyle_pandoc_title(doc)

    # Replace pandoc-corrupted tables with clean python-docx rebuilds
    if table_kind is not None:
        rebuild_tables(doc, kind=table_kind)

    fit_figures(doc, 6.5)
    add_page_numbers(doc)

    doc.save(str(docx_path))
    print(f"  saved: {docx_path.stat().st_size / 1024:.1f} KB")


def main() -> None:
    # Main paper
    pandoc_convert(BODY_TEX, MAIN_DOCX)
    post_process(MAIN_DOCX, add_title=True)

    # Supplement
    if SUPP_TEX.exists():
        pandoc_convert(SUPP_TEX, SUPP_DOCX)
        post_process(SUPP_DOCX, add_title=False, table_kind="supp")

    print()
    print("=" * 60)
    print("Done.")
    print(f"  Main:       {MAIN_DOCX}")
    print(f"              ({MAIN_DOCX.stat().st_size / 1024:.1f} KB)")
    if SUPP_DOCX.exists():
        print(f"  Supplement: {SUPP_DOCX}")
        print(f"              ({SUPP_DOCX.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
