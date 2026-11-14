# Erzeugt Umriss-Logo und Übersichtskarte des Somalia aus Natural Earth (gemeinfrei).
# Eingabe: Ordner mit a0.geojson (ne_10m_admin_0_countries) und pp.geojson (ne_10m_populated_places_simple)
# aus https://github.com/nvkelso/natural-earth-vector/tree/master/geojson
# Aufruf: python3 werkzeuge/karten.py <ordner> <zielordner>
import json, math, sys, os
NE, OUT = sys.argv[1], sys.argv[2]
a0 = json.load(open(os.path.join(NE, 'a0.geojson')))
pp = json.load(open(os.path.join(NE, 'pp.geojson')))
def land(code):
    for f in a0['features']:
        if f['properties']['ADM0_A3'] == code: return f['geometry']
def rings(g):
    if g['type'] == 'Polygon': return g['coordinates']
    return [r for poly in g['coordinates'] for r in poly]
def dp(pts, eps):
    if len(pts) < 3: return pts
    (x1,y1),(x2,y2) = pts[0], pts[-1]
    dx,dy = x2-x1, y2-y1; L = math.hypot(dx,dy) or 1e-9
    dmax, idx = 0, 0
    for i in range(1, len(pts)-1):
        x,y = pts[i]; d = abs(dy*x-dx*y+x2*y1-y2*x1)/L
        if d > dmax: dmax, idx = d, i
    if dmax > eps: return dp(pts[:idx+1], eps)[:-1] + dp(pts[idx:], eps)
    return [pts[0], pts[-1]]
def pfad(g, proj, eps):
    out = []
    for r in rings(g):
        pts = [proj(*c[:2]) for c in r]
        m = len(pts)//2
        s = dp(pts[:m+1], eps)[:-1] + dp(pts[m:], eps)
        if len(s) < 3: continue
        out.append('M' + ' L'.join(f'{x:.1f} {y:.1f}' for x,y in s) + 'Z')
    return ''.join(out)
K = math.cos(math.radians(5.0))
som, sol = land('SOM'), land('SOL')
# Logo: Somalia in den international anerkannten Grenzen (Natural Earth führt Somaliland gesondert)
ringe = rings(som) + rings(sol)
xs = [c[0] for r in ringe for c in r]; ys = [c[1] for r in ringe for c in r]
lon0, lon1, lat0, lat1 = min(xs), max(xs), min(ys), max(ys)
w, h = (lon1-lon0)*K, lat1-lat0
s = 54/max(w, h)
ox, oy = (64-w*s)/2, (64-h*s)/2
lp = lambda lon,lat: (ox+(lon-lon0)*K*s, oy+(lat1-lat)*s)
logo = pfad(som, lp, 0.35) + pfad(sol, lp, 0.35)
open(os.path.join(OUT, 'logo-pfad.txt'), 'w').write(logo)
# Karte: Horn von Afrika
B = (38.6, 52.0, -4.8, 12.9)  # lon min, lon max, lat min, lat max
S = 40
W, H = (B[1]-B[0])*K*S, (B[3]-B[2])*S
pk = lambda lon,lat: ((lon-B[0])*K*S, (B[3]-lat)*S)
teile = [f'<rect class="wasser" width="{W:.0f}" height="{H:.0f}"/>']
for code, name in [('ETH','Äthiopien'),('KEN','Kenia'),('DJI','Dschibuti'),('YEM','Jemen'),('ERI','Eritrea')]:
    teile.append(f'<path class="nachbar" d="{pfad(land(code), pk, 0.5)}"><title>{name}</title></path>')
teile.append(f'<path class="kosovo som" d="{pfad(som, pk, 0.5)}"><title>Somalia</title></path>')
teile.append(f'<path class="kosovo som" d="{pfad(sol, pk, 0.5)}"><title>Somalia (Somaliland)</title></path>')
orte = {'Mogadishu': 'Mogadischu', 'Beledweyne': 'Belet Uen', 'Kismaayo': 'Kismayo', 'Baydhabo': 'Baidoa', 'Hargeisa': 'Hargeisa', 'Djibouti': 'Dschibuti', 'Mombasa': 'Mombasa'}
punkte = {}
for f in pp['features']:
    p = f['properties']
    if p['name'] in orte and p.get('adm0name') in ('Somalia', 'Somaliland', 'Djibouti', 'Kenya'):
        punkte[orte[p['name']]] = pk(p['longitude'], p['latitude'])
def massstab(x, y, km, einh_je_km, fs):
    """Maßstabsleiste (zwei Felder) mit Beschriftung, linke untere Ecke bei (x, y), Kartenmaß in SVG-Einheiten."""
    L = km * einh_je_km; h = fs * .42; sw = fs * .07
    r = lambda v: f'{v:.1f}'.rstrip('0').rstrip('.')
    return (f'<g class="massstab" aria-hidden="true">'
            f'<rect class="a" x="{r(x)}" y="{r(y-h)}" width="{r(L/2)}" height="{r(h)}" stroke-width="{r(sw) if sw>=.05 else f"{sw:.2f}"}"/>'
            f'<rect class="b" x="{r(x+L/2)}" y="{r(y-h)}" width="{r(L/2)}" height="{r(h)}" stroke-width="{r(sw) if sw>=.05 else f"{sw:.2f}"}"/>'
            f'<text x="{r(x)}" y="{r(y-h-fs*.35)}" font-size="{r(fs)}" style="stroke-width:{fs*.25:.2f}px">0</text>'
            f'<text x="{r(x+L)}" y="{r(y-h-fs*.35)}" font-size="{r(fs)}" style="stroke-width:{fs*.25:.2f}px">{km} km</text></g>')
# Maßstab: 1 Grad Breite = 111,32 km = S Karteneinheiten; rechts unten, 200 km
teile.append(massstab(round(W) - 100, round(H) - 14, 200, S / 111.32, 14))
json.dump({'breite': round(W), 'hoehe': round(H), 'pfade': ''.join(teile), 'orte': {k: [round(v[0],1), round(v[1],1)] for k,v in punkte.items()}},
          open(os.path.join(OUT, 'karte.json'), 'w'), ensure_ascii=False)
print(round(W), round(H), punkte)
