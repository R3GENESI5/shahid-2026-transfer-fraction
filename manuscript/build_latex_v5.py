"""
build_latex.py

Convert the v3 paper docx -> LaTeX -> PDF with proper scientific typography.

Strategy:
1. Extract body with pandoc (done: paper_body.tex)
2. Post-process: convert Unicode symbols to LaTeX math equivalents
3. Wrap with article class + amsmath + siunitx + booktabs + graphicx
4. Compile with xelatex (handles Unicode where conversion fails)

Output: Shahid_2026_v3_FINAL_latex.pdf
"""

import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BODY = os.path.join(HERE, 'paper_body_v5.tex')
SUPP_BODY = os.path.join(HERE, 'supp_body_v5.tex')
MAIN_TEX = os.path.join(HERE, 'Shahid_2026_v5_latex.tex')
SUPP_TEX = os.path.join(HERE, 'Shahid_2026_v5_Supplementary_latex.tex')

# =========================================================================
# Post-processing: replace Unicode symbols with proper LaTeX math
# =========================================================================

def fix_symbols(text):
    """Replace Unicode symbols with LaTeX equivalents for cleaner rendering."""

    # Units: W m-2 (with various Unicode spacings and minus signs)
    # Handles: W~m⁻², W m⁻², W m−2, W/m2, etc.
    unit_patterns = [
        (r'W\s*m\\textsuperscript\{-2\}', r'\\si{\\watt\\per\\metre\\squared}'),
        (r'W\s*m\\textsuperscript\{\\(minus|-)2\}', r'\\si{\\watt\\per\\metre\\squared}'),
        (r'W[\s~]+m[⁻−-]+[²2]', r'\\si{\\watt\\per\\metre\\squared}'),
        (r'W/m[²2]', r'\\si{\\watt\\per\\metre\\squared}'),
        (r'W\s*m\s*[^a-zA-Z]?2\b', r'\\si{\\watt\\per\\metre\\squared}'),
        (r'J\s*kg\\textsuperscript\{-1\}', r'\\si{\\joule\\per\\kilogram}'),
        (r'J[\s~]+kg[⁻−-]+1', r'\\si{\\joule\\per\\kilogram}'),
        (r'J/kg', r'\\si{\\joule\\per\\kilogram}'),
        (r'mm\\s*yr\\textsuperscript\{-1\}', r'\\si{\\milli\\metre\\per\\year}'),
        (r'mm[\s~]+yr[⁻−-]+1', r'\\si{\\milli\\metre\\per\\year}'),
    ]
    for pat, rep in unit_patterns:
        text = re.sub(pat, rep, text)

    # Greek letters in prose (where they appear as stand-alone variables)
    # Only convert specific standalone uses to avoid breaking words
    greek_conversions = [
        (r'(?<!\$)η(?!\$)', r'$\\eta$'),
        (r'(?<!\$)α(?!\$)', r'$\\alpha$'),
        (r'(?<!\$)β(?!\$)', r'$\\beta$'),
        (r'(?<!\$)ρ(?!\$)', r'$\\rho$'),
        (r'(?<!\$)γ(?!\$)', r'$\\gamma$'),
        (r'(?<!\$)σ(?!\$)', r'$\\sigma$'),
        (r'(?<!\$)μ(?!\$)', r'$\\mu$'),
        (r'(?<!\$)Δ(?!\$)', r'$\\Delta$'),
    ]
    for pat, rep in greek_conversions:
        text = re.sub(pat, rep, text)

    # Special math characters
    text = re.sub(r'(?<!\$)±(?!\$)', r'$\\pm$', text)
    text = re.sub(r'(?<!\$)≈(?!\$)', r'$\\approx$', text)
    text = re.sub(r'(?<!\$)≤(?!\$)', r'$\\leq$', text)
    text = re.sub(r'(?<!\$)≥(?!\$)', r'$\\geq$', text)
    text = re.sub(r'(?<!\$)×(?!\$)', r'$\\times$', text)
    text = re.sub(r'(?<!\$)°(?!\$)', r'$^\\circ$', text)

    # R2 etc.
    text = re.sub(r'\bR²', r'$R^2$', text)
    text = re.sub(r'\bR\\textsuperscript\{2\}', r'$R^2$', text)

    # CO2 and similar
    text = re.sub(r'CO₂', r'CO$_2$', text)
    text = re.sub(r'CO\\textsubscript\{2\}', r'CO$_2$', text)
    text = re.sub(r'H₂O', r'H$_2$O', text)

    # Superscripts -2, -1 as standalone
    text = text.replace('⁻²', r'$^{-2}$')
    text = text.replace('⁻¹', r'$^{-1}$')
    text = text.replace('⁻³', r'$^{-3}$')

    # Ensure minus signs in numbers use proper math minus
    # "−19.8" (Unicode minus) becomes "$-19.8$"
    # Only when clearly a negative number (preceded by space or start of line)
    text = re.sub(r'(?<=[\s(])−(\d)', r'$-$\1', text)
    text = re.sub(r'^−(\d)', r'$-$\1', text, flags=re.MULTILINE)

    # Heading conversions: \textbf{1. Introduction} -> \section{Introduction}
    # Match patterns like \textbf{1. Title} or \textbf{1.1 Subtitle}
    # Wrap the remaining text as section headings
    def heading_replace(match):
        content = match.group(1)
        # Top-level sections: "1. Introduction"
        top = re.match(r'^(\d+)\.\s+(.+)$', content)
        if top:
            return f'\\section{{{top.group(2).strip()}}}'
        # Subsections: "1.1 Something"
        sub = re.match(r'^(\d+)\.(\d+)\s+(.+)$', content)
        if sub:
            return f'\\subsection{{{sub.group(3).strip()}}}'
        # Sub-subsections: "1.1.1 Something"
        subsub = re.match(r'^(\d+)\.(\d+)\.(\d+)\s+(.+)$', content)
        if subsub:
            return f'\\subsubsection{{{subsub.group(4).strip()}}}'
        # Abstract, References, etc.
        if content.strip() in {'Abstract', 'References', 'Data Availability',
                               'Code Availability', 'Author Contributions',
                               'Conclusions', 'Acknowledgements'}:
            return f'\\section*{{{content.strip()}}}'
        return match.group(0)

    text = re.sub(r'\\textbf\{([^{}]+?)\}', heading_replace, text)

    # Transfer fraction formula in body: η = |CRE_net| / LE
    # Already has Greek letters handled; make it display math when it appears alone
    # Not auto-detecting for now.

    # CRE_net, CRE_SW, CRE_LW subscripts: use math subscripts for cleaner look
    # In body text: CRE\_net -> $\mathrm{CRE}_{\mathrm{net}}$
    text = re.sub(r'CRE\\_net', r'$\\mathrm{CRE}_{\\mathrm{net}}$', text)
    text = re.sub(r'CRE\\_SW', r'$\\mathrm{CRE}_{\\mathrm{SW}}$', text)
    text = re.sub(r'CRE\\_LW', r'$\\mathrm{CRE}_{\\mathrm{LW}}$', text)
    text = re.sub(r'CRE_net', r'$\\mathrm{CRE}_{\\mathrm{net}}$', text)
    text = re.sub(r'CRE_SW', r'$\\mathrm{CRE}_{\\mathrm{SW}}$', text)
    text = re.sub(r'CRE_LW', r'$\\mathrm{CRE}_{\\mathrm{LW}}$', text)

    # R_net similarly
    text = re.sub(r'R\\_net', r'$R_{\\mathrm{net}}$', text)
    text = re.sub(r'R_net\b', r'$R_{\\mathrm{net}}$', text)

    # Fix double-$ from nested substitutions (cleanup)
    text = re.sub(r'\$\$+', '$', text)

    # Fix f-string placeholders that leaked through from build_paper_e_v3.py
    # These should have been substituted at docx generation but weren't
    text = text.replace('{MINUS_SIGN}', r'$-$')
    text = text.replace('\\{MINUS\\_SIGN\\}', r'$-$')
    text = text.replace('\\{MINUS\\textbackslash{}SIGN\\}', r'$-$')
    text = text.replace('{RHO}', r'$\rho$')
    text = text.replace('\\{RHO\\}', r'$\rho$')
    text = text.replace('{ETA}', r'$\eta$')
    text = text.replace('\\{ETA\\}', r'$\eta$')
    text = text.replace('{ALPHA}', r'$\alpha$')
    text = text.replace('\\{ALPHA\\}', r'$\alpha$')
    text = text.replace('{BETA}', r'$\beta$')
    text = text.replace('\\{BETA\\}', r'$\beta$')
    text = text.replace('{GAMMA}', r'$\gamma$')
    text = text.replace('\\{GAMMA\\}', r'$\gamma$')
    text = text.replace('{ENDASH}', r'--')
    text = text.replace('\\{ENDASH\\}', r'--')
    text = text.replace('{DAGGER}', r'$\dagger$')
    text = text.replace('\\{DAGGER\\}', r'$\dagger$')
    # {WMSQ} custom macro
    text = text.replace('{WMSQ}', r'\si{\watt\per\metre\squared}')
    text = text.replace('\\{WMSQ\\}', r'\si{\watt\per\metre\squared}')

    # Also handle pandoc's escape of underscores in subscripted IDs
    # eta\_site -> $\eta_{\text{site}}$
    text = text.replace('η\\_site', r'$\eta_{\mathrm{site}}$')
    text = text.replace('η\\_basin', r'$\eta_{\mathrm{basin}}$')
    text = text.replace('η_site', r'$\eta_{\mathrm{site}}$')
    text = text.replace('η_basin', r'$\eta_{\mathrm{basin}}$')

    return text


def build_preamble(title, author, is_supplementary=False):
    subtitle = ('Supplementary Materials' if is_supplementary
                else 'Site-level constraints at 341 FLUXNET-CERES sites and basin-scale extension for the Amazon, Congo, and Southeast Asia')
    return r"""\documentclass[11pt,letterpaper]{article}
\usepackage[margin=1in]{geometry}
\usepackage{fontspec}
\setmainfont{Times New Roman}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{siunitx}
\sisetup{per-mode=symbol, inter-unit-product = \ensuremath{{}\cdot{}}}
\usepackage{booktabs}
\usepackage{graphicx}
\usepackage{float}
\usepackage{longtable}
\usepackage{array}
\usepackage{calc}
% Pandoc compatibility: it emits \LTcaptype{none} and \real{...}
\providecommand{\real}[1]{#1}
\newcounter{none}
% Pandoc's tightlist hack
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}
\usepackage{xcolor}
\definecolor{linkblue}{RGB}{0,71,171}
\usepackage[hidelinks,colorlinks=true,linkcolor=linkblue,citecolor=linkblue,urlcolor=linkblue]{hyperref}
\usepackage{microtype}
\usepackage{setspace}
\setstretch{1.15}
\setlength{\parskip}{0.5em}
\setlength{\parindent}{0pt}

% Figure environment that respects default float placement
\renewcommand{\figurename}{Figure}
\renewcommand{\tablename}{Table}

% Better subscript rendering for CRE variables
\newcommand{\CRE}[1]{\ensuremath{\mathrm{CRE}_{\mathrm{#1}}}}
\newcommand{\Rnet}{\ensuremath{R_{\mathrm{net}}}}
\newcommand{\Wm}{\ensuremath{\mathrm{W\,m^{-2}}}}

\title{""" + title + (r""" \\ \vspace{4pt} \Large\textit{""" + subtitle + "}" if subtitle else "") + r"""}
\author{Ali B. Shahid \\ \small Independent researcher. ORCID: 0009-0003-9709-4241}
\date{June 2026}

\begin{document}
\maketitle
"""


POSTAMBLE = r"""
\end{document}
"""


def compile_tex(tex_path, engine='xelatex'):
    """Run compile twice for cross-references."""
    dir_ = os.path.dirname(tex_path)
    name = os.path.basename(tex_path).replace('.tex', '')
    for _ in range(2):
        result = subprocess.run(
            [engine, '-interaction=nonstopmode', '-halt-on-error', name + '.tex'],
            cwd=dir_, capture_output=True, text=True, timeout=300
        )
    pdf = os.path.join(dir_, name + '.pdf')
    return pdf if os.path.exists(pdf) else None, result.stdout[-2000:] if result.returncode else ''


def main():
    # Read the pandoc output body
    with open(BODY, 'r', encoding='utf-8') as f:
        body = f.read()

    # Apply symbol fixes
    body = fix_symbols(body)

    # Strip the title block from the body since \maketitle handles it
    # Pattern: the body starts with \textbf{Title}\n\nAuthor\n\n\emph{...}\n\nVersion...
    # Remove everything up to and including the "Version 3, ..." line
    lines = body.split('\n')
    start = 0
    for i, line in enumerate(lines):
        if 'Version 4' in line or 'Version\\,4' in line or 'Version 3' in line:
            start = i + 1
            break
        # Also catch cases where Abstract heading starts the real content
        if i > 15 and '\\section' in line and 'Abstract' in line:
            start = i
            break
    if start > 0:
        body = '\n'.join(lines[start:])

    # Use existing supp_body_v4.tex (carried over from v3); no pandoc re-extraction in v4
    if os.path.exists(SUPP_BODY):
        with open(SUPP_BODY, 'r', encoding='utf-8') as f:
            supp_body = f.read()
        supp_body = fix_symbols(supp_body)
    else:
        supp_body = None

    # Write main paper LaTeX
    title = 'Empirical constraints on the fraction of surface latent heat flux reaching the top of atmosphere as net radiative cooling'
    preamble = build_preamble(title, 'Ali B. Shahid', is_supplementary=False)
    with open(MAIN_TEX, 'w', encoding='utf-8') as f:
        f.write(preamble)
        f.write(body)
        f.write(POSTAMBLE)
    print(f'Wrote {MAIN_TEX}')

    # Compile main
    print('Compiling main paper with xelatex...')
    pdf, err = compile_tex(MAIN_TEX, 'xelatex')
    if pdf:
        size_kb = os.path.getsize(pdf) / 1024
        print(f'  OK: {pdf} ({size_kb:.1f} KB)')
    else:
        print('  Compile FAILED. Last output:')
        print(err)

    # Write supplementary LaTeX if we have it
    if supp_body:
        supp_preamble = build_preamble(title, 'Ali B. Shahid', is_supplementary=True)
        with open(SUPP_TEX, 'w', encoding='utf-8') as f:
            f.write(supp_preamble)
            f.write(supp_body)
            f.write(POSTAMBLE)
        print(f'Wrote {SUPP_TEX}')

        print('Compiling supplementary with xelatex...')
        pdf2, err2 = compile_tex(SUPP_TEX, 'xelatex')
        if pdf2:
            size_kb = os.path.getsize(pdf2) / 1024
            print(f'  OK: {pdf2} ({size_kb:.1f} KB)')
        else:
            print('  Compile FAILED. Last output:')
            print(err2)


if __name__ == '__main__':
    main()
