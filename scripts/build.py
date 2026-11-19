import json, math, sys
src, phsrc, out = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(open(src))
ROADS = {
 'NLEX': ('Easytrip','Metro Pacific Tollways Corporation','84'),
 'SCTEX': ('Easytrip','NLEX Corporation','93.77'),
 'TPLEX': ('Autosweep','Private Infra Dev Corporation','89.21'),
 'SLEX': ('Autosweep','SMC Tollways','49.56'),
 'Skyway': ('Autosweep','SMC Tollways','38.6'),
 'Skyway Stage 3': ('Autosweep','SMC Tollways','18.83'),
 'CALAX': ('Easytrip','Metro Pacific Tollways Corporation','44.6'),
 'CAVITEX': ('Easytrip','Metro Pacific Tollways Corporation','14'),
 'MCX': ('Autosweep','Prime Asset Ventures Inc.','4'),
 'STAR Tollway': ('Autosweep','SMC Tollways','41.9'),
 'NAIAX': ('Autosweep','SMC Tollways','12.65'),
 'NLEX Connector': ('Easytrip','Metro Pacific Tollways Corporation','7.7'),
 'Harbor Link': ('Easytrip','Metro Pacific Tollways Corporation','5.65'),
 'CLLEX': ('Toll-free','Department of Public Works and Highways','30.7'),
 'Subic–Tipo': ('Easytrip','NLEX Corporation',None),
 'Other': ('Other',None,None),
}
NAME = {
 'Tarlac-Pangasinan-La Union Expressway':'TPLEX','South Luzon Expressway':'SLEX','North Luzon Expressway':'NLEX',
 'Cavite–Laguna Expressway':'CALAX','Cavite-Laguna Expressway':'CALAX','Cavite–Laguna Expresswayy':'CALAX','CAVITEX–CALAX Link':'CALAX',
 'Subic-Clark-Tarlac Expressway':'SCTEX','Manila–Cavite Expressway':'CAVITEX','Manila-Cavite Expressway':'CAVITEX','CAVITEX–C-5 Link':'CAVITEX',
 'Southern Tagalog Arterial Road':'STAR Tollway','Subic-Tipo Expressway':'Subic–Tipo','Central Luzon Link Expressway':'CLLEX',
 'NAIA Expressway':'NAIAX','Clark Spur Road':'NLEX','Tabang Spur Road':'NLEX','NLEX-SLEX Connector Road':'NLEX Connector',
 'NLEX Harbor Link Segment 10':'Harbor Link','NLEX Harbor Link Segment 9':'Harbor Link','Muntinlupa-Cavite Expressway':'MCX',
 'NLEX-Mindanao Avenue Link':'NLEX','NLEX Segment 8.2':'NLEX','Balagtas Flyover':'STAR Tollway','NLEX Smart Connect Interchange':'NLEX',
 'Northern Access Link Expressway':'Other','Southern Access Link Expressway':'Other','Southeast Metro Manila Expressway':'Other',
}
def dp(pts, tol):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]
    dx, dy = b[0]-a[0], b[1]-a[1]; L = math.hypot(dx, dy) or 1e-12
    imax, dmax = 0, -1
    for i in range(1, len(pts)-1):
        p = pts[i]
        dd = abs(dy*p[0]-dx*p[1]+b[0]*a[1]-b[1]*a[0])/L if L>1e-12 else math.hypot(p[0]-a[0],p[1]-a[1])
        if dd > dmax: imax, dmax = i, dd
    if dmax > tol:
        return dp(pts[:imax+1], tol)[:-1] + dp(pts[imax:], tol)
    return [a, b]
lines = {k: [] for k in ROADS}; unnamed = []; skipped = 0
for f in d['features']:
    g = f['geometry']; p = f['properties']
    if g['type'] != 'LineString': continue
    if p.get('highway') != 'motorway': skipped += 1; continue
    n = p.get('name'); c = g['coordinates']
    if not n: unnamed.append(c); continue
    k = NAME.get(n)
    if n in ('Skyway', 'Skyway Extension'):
        k = 'Skyway Stage 3' if sum(q[1] for q in c)/len(c) >= 14.565 else 'Skyway'
    if k is None: print('UNMAPPED', n); k = 'Other'
    lines[k].append(c)
def nearest(pt, keys=None):
    best, bk = 1e9, None
    for k, ls in lines.items():
        if keys and k not in keys: continue
        for l in ls:
            for q in l[::3]:
                dd = (q[0]-pt[0])**2 + (q[1]-pt[1])**2
                if dd < best: best, bk = dd, k
    return bk, math.sqrt(best)
for c in unnamed:
    k, _ = nearest(c[len(c)//2]); lines[k].append(c)
roads = []
for k, ls in lines.items():
    if not ls: continue
    net, op, km = ROADS[k]
    simp = [[[round(x,5), round(y,5)] for x, y in dp(l, 0.00015)] for l in ls]
    longest = max(ls, key=len); anchor = longest[len(longest)//2]
    roads.append({'n': k, 'net': net, 'op': op, 'km': km, 'lines': simp, 'anchor': [round(anchor[0],5), round(anchor[1],5)], 'ways': len(ls)})
# booths
raw = []
for f in d['features']:
    if f['geometry']['type'] != 'Point': continue
    p = f['properties']; x, y = f['geometry']['coordinates']
    if p.get('payment:easytrip') == 'yes': net = 'Easytrip'
    elif p.get('payment:autosweep_rfid') == 'yes' or p.get('payment:autosweep') == 'yes': net = 'Autosweep'
    else: net = None
    raw.append([x, y, p.get('name') or 'Toll plaza', net])
booths = []
for x, y, nm, net in raw:
    for b in booths:
        if b['name'] == nm and abs(b['x']-x) < 0.006 and abs(b['y']-y) < 0.006:
            b['pts'].append((x, y)); b['net'] = b['net'] or net; break
    else:
        booths.append({'name': nm, 'x': x, 'y': y, 'net': net, 'pts': [(x, y)]})
bo = []; dropped = 0
for b in booths:
    x = sum(p[0] for p in b['pts'])/len(b['pts']); y = sum(p[1] for p in b['pts'])/len(b['pts'])
    best, k = 1e9, None
    for kk, ls in lines.items():
        for l in ls:
            for q in l:
                dd = (q[0]-x)**2 + (q[1]-y)**2
                if dd < best: best, k = dd, kk
    if math.sqrt(best) > 0.0035 or ROADS[k][0] == 'Toll-free': dropped += 1; continue
    net = b['net'] or ROADS[k][0]
    bo.append([round(x,5), round(y,5), b['name'], net, k])
# land
ph = json.load(open(phsrc))
land = []
for poly in ph['geometry']['coordinates']:
    ring = poly[0]
    xs = [q[0] for q in ring]; ys = [q[1] for q in ring]
    if max(xs) < 119.3 or min(xs) > 122.6 or max(ys) < 13.0 or min(ys) > 17.2: continue
    land.append([[[round(x,4), round(y,4)] for x, y in dp(r, 0.002)] for r in poly])
json.dump({'roads': roads, 'booths': bo, 'land': {'type': 'MultiPolygon', 'coordinates': land}}, open(out, 'w'), separators=(',', ':'))
print('skipped non-motorway', skipped, 'unnamed', len(unnamed))
for r in roads: print(r['n'], r['net'], r['ways'], sum(len(l) for l in r['lines']))
import collections; print('dropped booths',dropped); print(len(bo), collections.Counter(b[3] for b in bo))
