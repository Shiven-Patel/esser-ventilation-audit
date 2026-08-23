"""
09_docs_html.py
---------------
Emit Google Docs-ready HTML for the manuscript and the computation record.

Google Docs applies inline styles on paste and largely ignores a <style> block,
so every element here carries its own style attribute. Figures are referenced by
their public raw.githubusercontent.com URL rather than embedded as data URIs:
Docs fetches remote images during the paste and stores its own copy, which keeps
the clipboard payload small enough to move through a browser automation call.

The two files are committed to the repository so the paste step can fetch them
over CORS (raw.githubusercontent.com sends Access-Control-Allow-Origin: *)
instead of carrying tens of kilobytes of HTML through a tool call.

INPUTS   docs/manuscript.md
         output/math_workbook.html
OUTPUTS  docs/manuscript_for_docs.html
         docs/computation_record_for_docs.html
"""
from __future__ import annotations
import argparse, html, os, re

RAW = ('https://raw.githubusercontent.com/Shiven-Patel/esser-ventilation-audit'
       '/main/output/figures/')

FIG_FILES = {
    1: 'fig1_exposure_tail.png',
    2: 'fig2_specification_sensitivity.png',
    3: 'fig3_within_state_gap.png',
    4: 'fig4_identifier_coverage.png',
    5: 'fig5_race_gradient.png',
    6: 'fig6_funding_map.png',
    7: 'fig7_top_exposure_map.png',
    8: 'fig8_case_maps.png',
    9: 'fig9_viewer_national.png',
    10: 'fig10_viewer_oklahoma.png',
}
# Rendered width in pixels inside a Google Doc with default margins.
FIG_WIDTH = {3: 380, 8: 620, 9: 620, 10: 620}   # tall one narrow, wide ones wide
DEFAULT_WIDTH = 560

BODY = ("font-family:'Times New Roman',Times,serif;font-size:12pt;color:#000000;"
        "line-height:1.5;margin:0 0 10pt 0;")
H1 = ("font-family:'Times New Roman',Times,serif;font-size:15pt;color:#000000;"
      "font-weight:bold;margin:0 0 12pt 0;")
H2 = ("font-family:'Times New Roman',Times,serif;font-size:12pt;color:#000000;"
      "font-weight:bold;margin:18pt 0 8pt 0;")
H3 = ("font-family:'Times New Roman',Times,serif;font-size:12pt;color:#000000;"
      "font-weight:bold;font-style:italic;margin:14pt 0 6pt 0;")
CAP = ("font-family:'Times New Roman',Times,serif;font-size:10pt;color:#000000;"
       "line-height:1.35;margin:4pt 0 16pt 0;")
NOTE = ("font-family:'Times New Roman',Times,serif;font-size:10pt;color:#000000;"
        "line-height:1.35;margin:0 0 6pt 0;")
FORMULA = ("font-family:'Times New Roman',Times,serif;font-size:12pt;color:#000000;"
           "font-style:italic;text-align:center;margin:10pt 0 14pt 0;")


def inline(t: str) -> str:
    """Markdown inline spans to HTML, escaping everything else."""
    out, last = [], 0
    pat = re.compile(r'(\[\^(\d+)\]|\*\*[^*]+\*\*|\^[^^\s]+\^|\*[^*]+\*|`[^`]+`)')
    for m in pat.finditer(t):
        out.append(html.escape(t[last:m.start()]))
        s = m.group(0)
        if s.startswith('[^'):
            out.append(f'<sup>{m.group(2)}</sup>')
        elif s.startswith('**'):
            out.append(f'<b>{html.escape(s[2:-2])}</b>')
        elif s.startswith('^'):
            out.append(f'<sup>{html.escape(s[1:-1])}</sup>')
        elif s.startswith('`'):
            out.append(f'<span style="font-family:Consolas,monospace;font-size:10.5pt">'
                       f'{html.escape(s[1:-1])}</span>')
        else:
            out.append(f'<i>{html.escape(s[1:-1])}</i>')
        last = m.end()
    out.append(html.escape(t[last:]))
    return ''.join(out)


def figure_block(n: int, caption: str) -> str:
    w = FIG_WIDTH.get(n, DEFAULT_WIDTH)
    return (f'<p style="text-align:center;margin:14pt 0 2pt 0">'
            f'<img src="{RAW}{FIG_FILES[n]}" width="{w}"></p>'
            f'<p style="{CAP}">{inline(f"Figure {n}. {caption}")}</p>')


def build_manuscript(md_path: str) -> str:
    src = open(md_path).read()
    captions = {int(m[0]): m[1].strip()
                for m in re.findall(r'^\*\*Figure (\d+)\.\*\*\s*(.+)$', src, re.M)}

    out, placed, in_notes, in_figlist = [], set(), False, False
    for line in src.split('\n'):
        if re.match(r'^---\s*$', line) or line.startswith('**Target journal:**'):
            continue
        if line.startswith('## '):
            t = line[3:].strip()
            in_figlist = (t == 'Figures')
            if in_figlist:
                continue
            in_notes = (t == 'Notes')
            out.append(f'<p style="{H2}">{html.escape(t)}</p>')
            continue
        if in_figlist:
            continue
        if line.startswith('### '):
            out.append(f'<p style="{H3}">{html.escape(line[4:].strip())}</p>')
            continue
        if line.startswith('# '):
            out.append(f'<p style="{H1}">{html.escape(line[2:].strip())}</p>')
            continue
        if line.startswith('$$'):
            out.append(f'<p style="{FORMULA}">'
                       'E<sub>s</sub> &nbsp;=&nbsp; &#8721; over facilities f within 50 km of'
                       '&nbsp;&nbsp; m<sub>f</sub> / max(d<sub>sf</sub>, 0.1 km)<sup>2</sup></p>')
            continue
        fn = re.match(r'^\[\^(\d+)\]:\s*(.*)$', line)
        if fn:
            out.append(f'<p style="{NOTE}padding-left:18pt;text-indent:-18pt">'
                       f'{fn.group(1)}. {inline(fn.group(2))}</p>')
            continue
        if not line.strip():
            continue

        style = NOTE if in_notes else BODY
        out.append(f'<p style="{style}">{inline(line.strip())}</p>')
        for m in re.finditer(r'Figure (\d+)', line):
            n = int(m.group(1))
            if n not in placed and n in FIG_FILES:
                placed.add(n)
                out.append(figure_block(n, captions.get(n, '')))

    for n in sorted(FIG_FILES):
        if n not in placed:
            placed.add(n)
            out.append(figure_block(n, captions.get(n, '')))
    return '\n'.join(out)


def build_record(html_path: str) -> str:
    """Re-style the computation record for Docs.

    The source file carries a <style> block, which Docs drops on paste, so the
    class-based rules are converted to inline styles here.
    """
    s = open(html_path).read()
    s = s.split('</style>', 1)[1] if '</style>' in s else s
    reps = [
        ('<h1>', f'<p style="{H1}">'), ('</h1>', '</p>'),
        ('<h2>', f'<p style="{H2}">'), ('</h2>', '</p>'),
        ('<h3>', f'<p style="{H3}">'), ('</h3>', '</p>'),
        ('<p class="note">', f'<p style="{NOTE}padding-left:16pt">'),
        ('<p class="src">', f'<p style="{NOTE}color:#555555">'),
        ('<div class="flag">',
         f'<p style="{BODY}background-color:#fff4e5;padding:8pt;'
         'border-left:3px solid #d55e00">'),
        ('</div>', '</p>'),
        ('<pre class="formula">',
         '<p style="font-family:Consolas,monospace;font-size:10pt;color:#000000;'
         'background-color:#f6f6f6;padding:8pt;white-space:pre-wrap;margin:8pt 0">'),
        ('</pre>', '</p>'),
        ('<p>', f'<p style="{BODY}">'),
        ('<table>', '<table style="border-collapse:collapse;font-family:Arial,sans-serif;'
                    'font-size:9.5pt;color:#000000">'),
        ('<th>', '<th style="border:1px solid #cccccc;padding:3pt 6pt;'
                 'background-color:#f0f0f0;font-weight:bold">'),
        ('<td>', '<td style="border:1px solid #cccccc;padding:3pt 6pt">'),
        ('<code>', '<span style="font-family:Consolas,monospace;font-size:10pt">'),
        ('</code>', '</span>'),
    ]
    for a, b in reps:
        s = s.replace(a, b)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--md', default='docs/manuscript.md')
    ap.add_argument('--record', default='output/math_workbook.html')
    ap.add_argument('--outdir', default='docs')
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    m = build_manuscript(a.md)
    p1 = os.path.join(a.outdir, 'manuscript_for_docs.html')
    open(p1, 'w').write(m)
    print(f'    wrote {p1}  ({len(m)/1000:.0f} KB, {m.count("<img")} figures)')

    r = build_record(a.record)
    p2 = os.path.join(a.outdir, 'computation_record_for_docs.html')
    open(p2, 'w').write(r)
    print(f'    wrote {p2}  ({len(r)/1000:.0f} KB)')


if __name__ == '__main__':
    main()
