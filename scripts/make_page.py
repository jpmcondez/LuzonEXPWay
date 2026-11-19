"""Build index.html: embeds the map data, the plaza registry and a fallback copy of fares.csv.
usage: python3 scripts/make_page.py data/roads.json data/graph.json data/plazas.csv fares.csv template.html index.html"""
import csv, json, sys
roads_land, graph, plazas, fares, tpl, out = sys.argv[1:7]
a = json.load(open(roads_land)); g = json.load(open(graph))
for r in a['roads']: r.pop('ways', None)
reg = [l for l in open(plazas, encoding='utf-8') if l.strip() and not l.startswith('#')]
pl = [{'system': r['system'], 'name': r['name'], 'aliases': [x.strip() for x in r['aliases'].split(';') if x.strip()]} for r in csv.DictReader(reg)]
data = {'roads': a['roads'], 'graph': g, 'plazas': pl}
html = open(tpl).read().replace('/*DATA*/', json.dumps(data, ensure_ascii=False, separators=(',', ':'))).replace('/*FARES*/', open(fares, encoding='utf-8').read().strip())
open(out, 'w').write(html); print(out, len(html)//1024, 'KB')
