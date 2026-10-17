"""Arma la página independiente del tablero AFP Chile y Perú.

Uso: python3 armar.py <carpeta fuente> <d3.min.js> <salida.html> [<carpeta audio> inline|files]
La carpeta fuente tiene index.html (la página del tablero) y un .json por conjunto de datos.
"""
import base64
import json
import sys
from pathlib import Path

base = Path(sys.argv[1])
d3 = Path(sys.argv[2]).read_text()
out = Path(sys.argv[3])
audio_dir = Path(sys.argv[4]) if len(sys.argv) > 4 else None
audio_mode = sys.argv[5] if len(sys.argv) > 5 else "inline"

DATOS = ["chile", "peru", "peru_f2", "equivalencias", "textos", "patrimonio", "legal", "cobertura"]

page = (base / "index.html").read_text()
cut = page.index("<script>")
markup, script = page[:cut], page[cut:]

raw = {}
for name in DATOS:
    f = base / f"{name}.json"
    if f.exists():
        raw[name] = json.loads(f.read_text())["rows"]

tokens = """
:root {
  color-scheme: light;
  --color-bg: #f6f7f9; --color-panel: #ffffff; --color-fg: #1b1f27; --color-fg-muted: #5d6573;
  --color-border-line: #e1e4ea; --color-ok: #1f7a4d; --color-warn: #a86400; --color-bad: #c2342b;
  --cds-chart-grid: #eceef2; --cds-chart-axis: #9aa1ad; --cds-chart-reference: #7d8592; --cds-chart-muted: #c9ced6;
  --cds-chart-status-critical: #d2453b; --cds-surface-popover: #ffffff; --cds-border: #d7dbe2;
  --cds-shadow-popover: 0 6px 20px rgba(20, 24, 32, .14); --cds-text-secondary: #5d6573;
  --chile: #2563c9; --peru: #d4483c;
}
@media (prefers-color-scheme: dark) {
  :root {
    color-scheme: dark;
    --color-bg: #121418; --color-panel: #1b1e24; --color-fg: #eceef2; --color-fg-muted: #a2a9b5;
    --color-border-line: #2c3038; --color-ok: #5cc48d; --color-warn: #e0a64a; --color-bad: #f07067;
    --cds-chart-grid: #262a31; --cds-chart-axis: #5d6573; --cds-chart-reference: #8a919c; --cds-chart-muted: #3a3f48;
    --cds-chart-status-critical: #f07067; --cds-surface-popover: #23272e; --cds-border: #353a43;
    --cds-shadow-popover: 0 6px 20px rgba(0, 0, 0, .5); --cds-text-secondary: #a2a9b5;
    --chile: #6c9cf0; --peru: #f0786c;
  }
}
:root {
  --font-anthropic-sans: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-anthropic-serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, serif;
  --cds-font-size-caption: .8125rem; --cds-font-size-body: .9375rem; --cds-font-size-heading: 1.0625rem; --cds-font-size-title: 1.625rem;
  --cds-font-weight-medium: 600;
  --cds-gap-xs: .25rem; --cds-gap-sm: .5rem; --cds-gap-md: 1rem; --cds-gap-lg: 1.5rem; --cds-gap-xl: 2rem;
  --cds-pad-xs: .25rem; --cds-pad-sm: .5rem; --cds-pad-md: .75rem; --cds-pad-lg: 1.25rem; --cds-pad-xl: 2rem;
  --cds-radius: 10px; --cds-dur-slow: 300ms; --cds-ease-out: cubic-bezier(.2, .8, .2, 1);
}
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--color-bg); color: var(--color-fg); font-family: var(--font-anthropic-sans); font-size: var(--cds-font-size-body);
  padding-block: max(1.25rem, env(safe-area-inset-top, 0px)) 2.5rem; padding-inline: max(16px, 3vw); }
[hidden] { display: none !important; }
.dash-skeleton { color: transparent; }
.lx-pie { margin-top: var(--cds-gap-lg); color: var(--color-fg-muted); font-size: var(--cds-font-size-caption); }
"""

favicon = ("data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 viewBox=%270 0 16 16%27%3E"
           "%3Crect x=%271%27 y=%278%27 width=%274%27 height=%277%27 fill=%27%232563c9%27/%3E"
           "%3Crect x=%276%27 y=%274%27 width=%274%27 height=%2711%27 fill=%27%23d4483c%27/%3E"
           "%3Crect x=%2711%27 y=%271%27 width=%274%27 height=%2714%27 fill=%27%232563c9%27/%3E%3C/svg%3E")

shim = """
<script>
window.dash = (() => {
  const RAW = %s;
  const calcs = {};
  const cbs = [];
  const css = getComputedStyle(document.documentElement);
  const colors = [css.getPropertyValue('--chile').trim() || '#2563c9', css.getPropertyValue('--peru').trim() || '#d4483c'];
  const data = (id) => {
    if (RAW[id]) return { status: 'ok', data: RAW[id], columns: Object.keys(RAW[id][0] || {}), meta: [] };
    const c = calcs[id];
    if (c) {
      if (!c.v) c.v = c.fn(...c.inputs.map((i) => data(i).data));
      return { status: 'ok', data: c.v, columns: Object.keys(c.v[0] || {}), meta: [] };
    }
    return { status: 'missing', data: [], meta: [] };
  };
  let t = null;
  window.addEventListener('resize', () => { clearTimeout(t); t = setTimeout(() => cbs.forEach((f) => f()), 150); });
  return {
    data,
    calc: (id, def) => { calcs[id] = def; },
    loader: () => {},
    onData: (fn) => { cbs.push(fn); fn(); },
    colors,
    refresh: () => {},
    params: () => ({}),
    setParams: () => {},
    resetParams: () => {},
    setLink: (id) => { try { history.replaceState(null, '', '#' + id); } catch (e) { /* archivo local */ } },
  };
})();
</script>
""" % json.dumps(raw, ensure_ascii=False)

audio_js = ""
if audio_dir and audio_dir.exists():
    mapa = {}
    for f in sorted(audio_dir.glob("*.m4a")):
        if audio_mode == "inline":
            mapa[f.stem] = "data:audio/mp4;base64," + base64.b64encode(f.read_bytes()).decode()
        else:
            mapa[f.stem] = "audio/" + f.name
    audio_js = "<script>window.AFP_AUDIO = " + json.dumps(mapa) + ";</script>"

pie = '<p class="lx-pie">Copia del tablero con cifras fijas al corte de septiembre de 2026.</p>'

html = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>AFP Chile y Perú</title>
<link rel="icon" href="{favicon}">
<style>{tokens}</style>
</head>
<body>
<div id="dash-root">
{markup}
</div>
<script>{d3}</script>
{shim}
{audio_js}
{script}
<script>(() => {{ const c = document.getElementById('credito'); const p = document.createElement('div'); p.innerHTML = {json.dumps(pie)}; (c ? c.parentNode.insertBefore(p.firstChild, c) : document.getElementById('lx').appendChild(p.firstChild)); }})();</script>
</body>
</html>
"""
out.write_text(html)
print(out, len(html), "bytes")
