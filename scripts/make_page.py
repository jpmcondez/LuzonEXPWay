import json, sys
roads_land, graph, fares, tpl, out = sys.argv[1:6]
a = json.load(open(roads_land)); g = json.load(open(graph))
for r in a['roads']: r.pop('ways', None)
data = {'roads': a['roads'], 'graph': g}
html = open(tpl).read().replace('/*DATA*/', json.dumps(data, ensure_ascii=False, separators=(',', ':'))).replace('/*FARES*/', open(fares).read().strip())
open(out, 'w').write(html); print(out, len(html)//1024, 'KB')
