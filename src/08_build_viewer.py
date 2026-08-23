"""
08_build_viewer.py
------------------
Build the interactive school map from the corrected analysis dataset.

This replaces the earlier viewer, which was generated before the exposure index
and the ESSER linkage were corrected and therefore shows exposure tiers and a
"not reported" category that the current analysis does not support. The two most
visible changes: schools with no linkable district record are labelled as such
rather than as a state that failed to report, and exposure is shown as a
percentile of the mass-weighted index rather than as a tier on the old scale.

The page loads Leaflet and a basemap from public CDNs, so it needs a network
connection the first time it is opened. Everything else, including the full
school payload, is inlined.

INPUT   data/derived/analysis_dataset.csv
OUTPUT  output/ESSER_viewer.html
"""
from __future__ import annotations
import argparse, json, os
import numpy as np
import pandas as pd

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ESSER ventilation and industrial exposure</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
:root{--ink:#1a1a1a;--muted:#5f6368;--line:#e3e3e0;--bg:#fcfcfb;
      --funded:#0072B2;--unfunded:#D55E00;--missing:#9AA0A6}
*{box-sizing:border-box}
body{margin:0;font:14px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;
     color:var(--ink);background:var(--bg)}
#map{position:absolute;inset:0 340px 0 0}
#side{position:absolute;top:0;right:0;bottom:0;width:340px;overflow-y:auto;
      border-left:1px solid var(--line);background:#fff;padding:18px 18px 40px}
h1{font-size:15px;margin:0 0 2px;letter-spacing:-.01em}
.sub{color:var(--muted);font-size:12px;margin:0 0 16px}
h2{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);
   margin:20px 0 8px;font-weight:600}
.chips{display:flex;flex-wrap:wrap;gap:5px}
.chip{border:1px solid var(--line);background:#fff;border-radius:99px;padding:4px 10px;
      font-size:11.5px;cursor:pointer;color:var(--ink)}
.chip[aria-pressed="true"]{background:var(--ink);color:#fff;border-color:var(--ink)}
select{width:100%;padding:6px 8px;border:1px solid var(--line);border-radius:6px;
       font:inherit;font-size:12.5px;background:#fff;margin-bottom:6px;color:var(--ink)}
.stat{display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--line);
      font-size:12.5px}
.stat b{font-variant-numeric:tabular-nums}
.big{font-size:26px;font-weight:600;letter-spacing:-.02em;margin:2px 0 0;font-variant-numeric:tabular-nums}
.legend{font-size:12px;color:var(--muted)}
.legend div{display:flex;align-items:center;gap:7px;padding:2px 0}
.sw{width:10px;height:10px;border-radius:99px;flex:0 0 auto}
input[type=range]{width:100%}
.note{font-size:11.5px;color:var(--muted);line-height:1.4;margin-top:6px}
.leaflet-popup-content{font-size:12.5px;line-height:1.5}
.leaflet-popup-content b{font-size:13px}
</style></head><body>
<div id="map"></div>
<div id="side">
  <h1>ESSER ventilation and industrial exposure</h1>
  <p class="sub">__NSCHOOLS__ public schools, 2024-25. Funding status is the district's
     answer in the FY2023 ESSER Annual Performance Report.</p>

  <h2>Colour by</h2>
  <div class="chips" id="mode">
    <button class="chip" data-m="fund" aria-pressed="true">Funding status</button>
    <button class="chip" data-m="exp" aria-pressed="false">Exposure percentile</button>
    <button class="chip" data-m="poc" aria-pressed="false">County % people of color</button>
  </div>
  <div class="legend" id="legend"></div>

  <h2>Where</h2>
  <select id="st"><option value="">All states</option></select>
  <select id="co"><option value="">All counties</option></select>

  <h2>Minimum exposure percentile</h2>
  <input type="range" id="ex" min="0" max="100" value="0" step="1"/>
  <div class="note" id="exlab">Showing all schools</div>

  <h2>Show</h2>
  <div class="chips" id="filt">
    <button class="chip" data-f="linked" aria-pressed="false">Linked records only</button>
  </div>

  <h2>Current selection</h2>
  <div class="big" id="rate">--</div>
  <div class="note" style="margin-top:0">recorded ventilation funding, among linked schools</div>
  <div style="margin-top:10px">
    <div class="stat"><span>Schools shown</span><b id="n">0</b></div>
    <div class="stat"><span>Linked to a district record</span><b id="nl">0</b></div>
    <div class="stat"><span>Recorded funding</span><b id="nf">0</b></div>
    <div class="stat"><span>Median county income</span><b id="mi">--</b></div>
    <div class="stat"><span>Mean county % people of color</span><b id="pc">--</b></div>
  </div>
  <p class="note">A blank in the federal file means the district did not answer. It is
     not the same as answering "no", and is never counted as unfunded here. Arizona,
     Connecticut, Texas and Washington answered for every district but supplied no
     district identifier, so their schools cannot be linked at all.</p>
</div>
<script>
const D = __DATA__;              // [lt, ln, pct, hv, st, co, nm, ci, pc, mi]
const LT=0, LN=1, PCT=2, HV=3, ST=4, CO=5, NM=6, CI=7, PC=8, MI=9;
const FUNDED='#0072B2', UNFUNDED='#D55E00', MISSING='#9AA0A6';

const map = L.map('map',{preferCanvas:true, zoomControl:true}).setView([39.3,-96.5],4);
L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
  {attribution:'&copy; OpenStreetMap &copy; CARTO', subdomains:'abcd', maxZoom:19}).addTo(map);
const layer = L.layerGroup().addTo(map);

let mode='fund', minEx=0, stSel='', coSel='', linkedOnly=false;

function ramp(v, lo, hi){            // single-hue sequential, light to dark
  const t = Math.max(0, Math.min(1, (v-lo)/(hi-lo)));
  const c0=[222,235,247], c1=[8,48,107];
  return 'rgb('+c0.map((a,i)=>Math.round(a+(c1[i]-a)*t)).join(',')+')';
}
function colour(d){
  if(mode==='fund') return d[HV]===null ? MISSING : (d[HV] ? FUNDED : UNFUNDED);
  if(mode==='exp')  return ramp(d[PCT], 0, 100);
  return d[PC]===null ? MISSING : ramp(d[PC], 0, 100);
}
const LEGENDS = {
  fund:[[FUNDED,'District recorded ventilation spending'],
        [UNFUNDED,'District recorded none'],
        [MISSING,'No linkable district record']],
  exp:[[ramp(5,0,100),'Low exposure percentile'],[ramp(50,0,100),'Middle'],
       [ramp(99,0,100),'High']],
  poc:[[ramp(5,0,100),'Fewer people of color'],[ramp(50,0,100),'Middle'],
       [ramp(99,0,100),'More people of color']]
};
function drawLegend(){
  document.getElementById('legend').innerHTML =
    LEGENDS[mode].map(([c,l])=>`<div><span class="sw" style="background:${c}"></span>${l}</div>`).join('');
}

function popup(d){
  const f = d[HV]===null ? 'No linkable district record'
          : (d[HV] ? 'District recorded ventilation spending'
                   : 'District recorded no ventilation spending');
  return `<b>${d[NM]}</b><br>${d[CI]}, ${d[ST]}<br>${d[CO]}<br><br>
          ${f}<br>Exposure percentile: ${d[PCT].toFixed(1)}<br>
          County median income: ${d[MI]===null?'n/a':'$'+d[MI].toLocaleString()}<br>
          County % people of color: ${d[PC]===null?'n/a':d[PC].toFixed(1)+'%'}`;
}

function visible(){
  return D.filter(d =>
    d[PCT] >= minEx &&
    (!stSel || d[ST]===stSel) &&
    (!coSel || d[CO]===coSel) &&
    (!linkedOnly || d[HV]!==null));
}

function median(a){ if(!a.length) return null; const s=[...a].sort((x,y)=>x-y);
  const m=s.length>>1; return s.length%2 ? s[m] : (s[m-1]+s[m])/2; }

let redrawTimer=null;
function redraw(){
  const v = visible();
  layer.clearLayers();
  const z = map.getZoom();
  const r = z<5 ? 1.4 : z<7 ? 2.2 : z<9 ? 3.2 : 4.4;
  // Above roughly 40k points the browser stalls, so a deterministic stride is
  // applied and the count is reported, rather than silently drawing a subset.
  const cap = 45000;
  const stride = Math.ceil(v.length / cap);
  for(let i=0;i<v.length;i+=stride){
    const d=v[i];
    L.circleMarker([d[LT],d[LN]],{radius:r,stroke:false,fillColor:colour(d),fillOpacity:.75})
      .addTo(layer).bindPopup(()=>popup(d));
  }
  const linked = v.filter(d=>d[HV]!==null);
  const funded = linked.filter(d=>d[HV]===1);
  document.getElementById('n').textContent  = v.length.toLocaleString()
      + (stride>1 ? ` (1 in ${stride} drawn)` : '');
  document.getElementById('nl').textContent = linked.length.toLocaleString();
  document.getElementById('nf').textContent = funded.length.toLocaleString();
  document.getElementById('rate').textContent =
      linked.length ? (funded.length/linked.length*100).toFixed(1)+'%' : '--';
  const mi = median(v.map(d=>d[MI]).filter(x=>x!==null));
  document.getElementById('mi').textContent = mi===null?'--':'$'+Math.round(mi).toLocaleString();
  const pc = v.map(d=>d[PC]).filter(x=>x!==null);
  document.getElementById('pc').textContent =
      pc.length ? (pc.reduce((a,b)=>a+b,0)/pc.length).toFixed(1)+'%' : '--';
}
function schedule(){ clearTimeout(redrawTimer); redrawTimer=setTimeout(redraw,60); }

// ---- controls --------------------------------------------------------------
document.getElementById('mode').addEventListener('click',e=>{
  const b=e.target.closest('button'); if(!b) return;
  mode=b.dataset.m;
  [...e.currentTarget.children].forEach(c=>c.setAttribute('aria-pressed', c===b));
  drawLegend(); schedule();
});
document.getElementById('filt').addEventListener('click',e=>{
  const b=e.target.closest('button'); if(!b) return;
  linkedOnly=!linkedOnly; b.setAttribute('aria-pressed',linkedOnly); schedule();
});
document.getElementById('ex').addEventListener('input',e=>{
  minEx=+e.target.value;
  document.getElementById('exlab').textContent =
     minEx===0 ? 'Showing all schools' : `Showing schools at or above the ${minEx}th percentile`;
  schedule();
});

const states=[...new Set(D.map(d=>d[ST]))].sort();
const stEl=document.getElementById('st'), coEl=document.getElementById('co');
states.forEach(s=>stEl.add(new Option(s,s)));
stEl.addEventListener('change',()=>{
  stSel=stEl.value; coSel='';
  coEl.length=1;
  if(stSel){ [...new Set(D.filter(d=>d[ST]===stSel).map(d=>d[CO]))].sort()
              .forEach(c=>coEl.add(new Option(c,c))); }
  if(stSel){ const p=D.filter(d=>d[ST]===stSel);
    map.fitBounds(L.latLngBounds(p.map(d=>[d[LT],d[LN]])).pad(0.1)); }
  else map.setView([39.3,-96.5],4);
  schedule();
});
coEl.addEventListener('change',()=>{
  coSel=coEl.value;
  if(coSel){ const p=D.filter(d=>d[ST]===stSel&&d[CO]===coSel);
    map.fitBounds(L.latLngBounds(p.map(d=>[d[LT],d[LN]])).pad(0.15)); }
  schedule();
});
map.on('zoomend moveend', schedule);
drawLegend(); redraw();
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='data/derived/analysis_dataset.csv')
    ap.add_argument('--out', default='output/ESSER_viewer.html')
    a = ap.parse_args()

    df = pd.read_csv(a.data, low_memory=False, dtype={'NCESSCH': str, 'LEAID': str})

    # Exposure is shown as a percentile of the unnormalised index, which is what
    # the manuscript reports. The normalised 0-100 column is clipped at the 99th
    # percentile and would collapse the top of the range.
    pct = df.E_air_raw_lbs_per_km2.rank(pct=True) * 100

    def val(x, nd=None):
        if pd.isna(x):
            return None
        return round(float(x), nd) if nd is not None else float(x)

    rows = []
    for (_, r), p in zip(df.iterrows(), pct):
        rows.append([
            round(float(r.LAT), 4), round(float(r.LON), 4), round(float(p), 2),
            None if pd.isna(r.HAS_VENT) else int(r.HAS_VENT),
            str(r.STATE), str(r.NMCNTY), str(r.NAME), str(r.CITY),
            val(r.pct_poc, 1),
            None if pd.isna(r.median_income) else int(r.median_income),
        ])

    html = (TEMPLATE
            .replace('__DATA__', json.dumps(rows, separators=(',', ':')))
            .replace('__NSCHOOLS__', f'{len(rows):,}'))
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    with open(a.out, 'w') as f:
        f.write(html)
    print(f'    wrote {a.out}  ({len(rows):,} schools, {os.path.getsize(a.out)/1e6:.1f} MB)')


if __name__ == '__main__':
    main()
