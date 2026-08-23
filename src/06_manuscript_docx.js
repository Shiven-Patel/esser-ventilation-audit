/*
 * 06_manuscript_docx.js
 * ---------------------
 * Build the submission Word file from docs/manuscript.md.
 *
 * Typography is deliberately plain: Times New Roman 12 pt, black, single column,
 * US Letter, one-inch margins, no colour anywhere. Headings are the body font in
 * bold rather than a theme style, because docx-js heading styles carry a blue
 * accent colour that a journal template will strip anyway.
 *
 * Figures are placed inline. Each figure is inserted immediately after the first
 * paragraph that refers to it as "(Figure N)", with its caption taken from the
 * "## Figures" list at the end of the markdown; that list is then dropped from the
 * flow so the caption text appears exactly once. Images are scaled to fit the text
 * column, and the tall ones are additionally capped on height so no figure runs
 * past a single page.
 *
 * Run:  node src/06_manuscript_docx.js
 * Out:  docs/ESSER_ventilation_manuscript.docx
 */
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType,
  Footer, PageNumber, convertInchesToTwip, LineRuleType,
} = require('docx');

const ROOT = path.resolve(__dirname, '..');
const SRC = path.join(ROOT, 'docs', 'manuscript.md');
const FIGDIR = path.join(ROOT, 'output', 'figures');
const OUT = path.join(ROOT, 'docs', 'ESSER_ventilation_manuscript.docx');

const BODY_PT = 24;        // half-points: 12 pt
const SMALL_PT = 20;       // 10 pt, for notes and captions
const BLACK = '000000';
const FONT = 'Times New Roman';

// Text column is 6.5 in at 96 dpi. Figures are inset slightly and height-capped.
const MAX_W = 520;
const MAX_H = 470;

const FIG_FILES = {
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
};

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

function fitted(file) {
  const { w, h } = pngSize(file);
  let W = MAX_W, H = Math.round((h / w) * MAX_W);
  if (H > MAX_H) { H = MAX_H; W = Math.round((w / h) * MAX_H); }
  return { width: W, height: H };
}

/* ---- inline markdown -> runs -------------------------------------------- */
function runs(text, opts = {}) {
  const base = { font: FONT, size: opts.size || BODY_PT, color: BLACK };
  const out = [];
  const re = /(\[\^(\d+)\]|\*\*[^*]+\*\*|\^[^^\s]+\^|\*[^*]+\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ ...base, text: text.slice(last, m.index) }));
    const s = m[0];
    if (s.startsWith('[^')) out.push(new TextRun({ ...base, text: m[2], superScript: true }));
    else if (s.startsWith('**')) out.push(new TextRun({ ...base, text: s.slice(2, -2), bold: true }));
    else if (s.startsWith('^')) out.push(new TextRun({ ...base, text: s.slice(1, -1), superScript: true }));
    else if (s.startsWith('`')) out.push(new TextRun({ ...base, text: s.slice(1, -1) }));
    else out.push(new TextRun({ ...base, text: s.slice(1, -1), italics: true }));
    last = re.lastIndex;
  }
  if (last < text.length) out.push(new TextRun({ ...base, text: text.slice(last) }));
  return out.length ? out : [new TextRun({ ...base, text: '' })];
}

const para = (t, o = {}) => new Paragraph({
  children: runs(t, o),
  spacing: { after: o.after ?? 180, line: o.line ?? 300 },
  alignment: o.alignment,
  indent: o.indent,
});

/* ---- captions ------------------------------------------------------------ */
const src = fs.readFileSync(SRC, 'utf8');
const captions = {};
for (const m of src.matchAll(/^\*\*Figure (\d+)\.\*\*\s*(.+)$/gm)) {
  captions[Number(m[1])] = m[2].trim();
}

function figureBlock(n) {
  const file = path.join(FIGDIR, FIG_FILES[n]);
  if (!fs.existsSync(file)) {
    console.warn(`  [warn] missing ${FIG_FILES[n]}, figure ${n} skipped`);
    return [];
  }
  return [
    new Paragraph({
      children: [new ImageRun({
        type: 'png',
        data: fs.readFileSync(file),
        transformation: fitted(file),
      })],
      alignment: AlignmentType.CENTER,
      // The document default sets a line height for body text. An inline image
      // inherits it and gets clipped to that height in LibreOffice and Word, so
      // the image paragraph is put back on automatic line spacing.
      spacing: { before: 260, after: 90, line: 240, lineRule: LineRuleType.AUTO },
    }),
    new Paragraph({
      children: runs(`Figure ${n}. ${captions[n] || ''}`, { size: SMALL_PT }),
      spacing: { after: 300, line: 260 },
      alignment: AlignmentType.LEFT,
      indent: { left: convertInchesToTwip(0.25), right: convertInchesToTwip(0.25) },
    }),
  ];
}

/* ---- walk the document --------------------------------------------------- */
const kids = [];
const lines = src.split('\n');
const placed = new Set();
let inNotes = false, inFigList = false;

for (let i = 0; i < lines.length; i++) {
  const L = lines[i];

  if (/^---\s*$/.test(L)) continue;
  if (L.startsWith('**Target journal:**')) continue;

  if (L.startsWith('## ')) {
    const t = L.slice(3).trim();
    inFigList = /^Figures$/.test(t);
    if (inFigList) continue;                       // captions live with the images
    inNotes = /^Notes$/.test(t);
    kids.push(new Paragraph({
      children: [new TextRun({ text: t, font: FONT, size: BODY_PT, bold: true, color: BLACK })],
      spacing: { before: 380, after: 170 },
    }));
    continue;
  }
  if (inFigList) continue;

  if (L.startsWith('### ')) {
    kids.push(new Paragraph({
      children: [new TextRun({ text: L.slice(4).trim(), font: FONT, size: BODY_PT,
                               bold: true, color: BLACK })],
      spacing: { before: 250, after: 130 },
    }));
    continue;
  }

  if (L.startsWith('# ')) {
    kids.push(new Paragraph({
      children: [new TextRun({ text: L.slice(2).trim(), font: FONT, size: 28,
                               bold: true, color: BLACK })],
      spacing: { after: 300, line: 300 },
    }));
    continue;
  }

  // display formula
  if (/^\$\$/.test(L)) {
    kids.push(new Paragraph({
      children: [new TextRun({
        text: 'E_s  =  ∑ over facilities f within 50 km of   m_f / max(d_sf, 0.1 km)²',
        font: FONT, size: BODY_PT, color: BLACK, italics: true,
      })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 160, after: 220 },
    }));
    continue;
  }

  // footnote definition
  const fn = L.match(/^\[\^(\d+)\]:\s*([\s\S]*)$/);
  if (fn) {
    kids.push(new Paragraph({
      children: [
        new TextRun({ text: fn[1] + '. ', font: FONT, size: SMALL_PT, color: BLACK }),
        ...runs(fn[2], { size: SMALL_PT }),
      ],
      spacing: { after: 120, line: 260 },
      indent: { left: convertInchesToTwip(0.3), hanging: convertInchesToTwip(0.3) },
    }));
    continue;
  }

  if (L.trim() === '') continue;

  kids.push(para(L.trim(), inNotes ? { size: SMALL_PT, after: 120, line: 260 } : {}));

  // Place any figure this paragraph is the first to cite. The text refers to
  // figures both parenthetically and inline, so the match is on the phrase
  // rather than the parentheses.
  for (const m of L.matchAll(/Figure (\d+)/g)) {
    const n = Number(m[1]);
    if (!placed.has(n)) { placed.add(n); kids.push(...figureBlock(n)); }
  }
}

// Anything never cited in text goes at the end, in order, so no figure is lost.
for (const n of Object.keys(FIG_FILES).map(Number).sort((a, b) => a - b)) {
  if (!placed.has(n)) { placed.add(n); kids.push(...figureBlock(n)); }
}

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: FONT, size: BODY_PT, color: BLACK },
        paragraph: { spacing: { line: 300 } },
      },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },              // US Letter, DXA
        margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: [PageNumber.CURRENT],
                                   font: FONT, size: SMALL_PT, color: BLACK })],
        })],
      }),
    },
    children: kids,
  }],
});

Packer.toBuffer(doc).then((b) => {
  fs.writeFileSync(OUT, b);
  console.log(`wrote ${path.relative(ROOT, OUT)}  (figures placed: ${[...placed].sort((a, b) => a - b).join(', ')})`);
});
