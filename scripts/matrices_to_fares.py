"""Convert TRB-style matrices (fares/matrices/<system>.class<N>.csv) into the long fares.csv the page reads.
Matrix file: '# system:', '# class:', '# effective:', '# source:' header lines, then a grid whose first row
lists entry plazas and whose first column lists exit plazas. Blank or '--' cells are skipped. Fares are two-way."""
import csv, glob, io, os, re, sys
src = sys.argv[1] if len(sys.argv) > 1 else 'fares/matrices'
out = sys.argv[2] if len(sys.argv) > 2 else 'fares.csv'
rows = {}
for path in sorted(glob.glob(os.path.join(src, '*.csv'))):
    meta, body = {}, []
    for line in open(path, encoding='utf-8'):
        m = re.match(r'#\s*(\w+)\s*:\s*(.*)', line)
        if m: meta[m.group(1).lower()] = m.group(2).strip()
        elif line.strip(): body.append(line)
    sysname, cls = meta['system'], int(meta['class'])
    grid = list(csv.reader(io.StringIO(''.join(body))))
    entries = [h.strip() for h in grid[0][1:]]
    for r in grid[1:]:
        ex = r[0].strip()
        for en, v in zip(entries, r[1:]):
            v = v.strip().replace(',', '').replace('₱', '')
            if not v or v in ('--', '-', '–') or en == ex: continue
            a, b = sorted([en, ex])
            k = (sysname, a, b)
            d = rows.setdefault(k, {'c': [None] * 4, 'eff': meta.get('effective', ''), 'src': meta.get('source', '')})
            d['c'][cls] = float(v)
with open(out, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['system', 'from', 'to', 'class1', 'class2', 'class3', 'effective', 'note'])
    for (s, a, b), d in sorted(rows.items()):
        fmt = lambda x: '' if x is None else (str(int(x)) if x == int(x) else str(x))
        w.writerow([s, a, b, fmt(d['c'][1]), fmt(d['c'][2]), fmt(d['c'][3]), d['eff'], d['src']])
print(out, len(rows), 'fare pairs')
