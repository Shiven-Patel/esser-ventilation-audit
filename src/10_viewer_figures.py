"""
10_viewer_figures.py
--------------------
Turn raw viewer screenshots into the two interface figures that appear at the
end of the manuscript (Figures 9 and 10).

These two figures document the interactive companion tool rather than adding
analysis. Nothing in them is computed here; they are crops of the browser view
of viewer/index.html, with a hairline border so the frame edge is visible
against a white page.

The Oklahoma County capture has a band of unloaded basemap tiles down its left
side, an artefact of screenshotting immediately after the map re-fits. That band
is cropped away rather than recaptured, since the map pane it leaves is complete.

INPUTS   raw screenshots (path given by --src)
OUTPUTS  output/figures/fig9_viewer_national.png
         output/figures/fig10_viewer_oklahoma.png
"""
from __future__ import annotations
import argparse, os
from PIL import Image, ImageOps

# (source file, left crop edge) for each output figure.
JOBS = {
    'fig9_viewer_national.png':  ('screenshot-1787446317963-0.jpg',   0),
    'fig10_viewer_oklahoma.png': ('screenshot-1787446394840-4.jpg', 332),
}
BORDER = '#bbbbbb'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True, help='directory holding the screenshots')
    ap.add_argument('--outdir', default='output/figures')
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)

    for name, (fn, left) in JOBS.items():
        im = Image.open(os.path.join(a.src, fn)).convert('RGB')
        im = im.crop((left, 0, im.width, im.height))
        im = ImageOps.expand(im, border=1, fill=BORDER)
        p = os.path.join(a.outdir, name)
        im.save(p, 'PNG')
        print(f'    wrote {p}  ({im.width}x{im.height})')


if __name__ == '__main__':
    main()
