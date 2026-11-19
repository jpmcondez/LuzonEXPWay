import json, math, re, sys, heapq, collections
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'build.py')).read().split('# booths')[0].replace("src, phsrc, out = sys.argv[1], sys.argv[2], sys.argv[3]","src, phsrc, out = 'data/export.geojson','data/ph.json','/dev/null'"))
# lines[k] = list of original coordinate lists (unnamed already assigned)
def hav(a,b):
    R=6371.0; la1,la2=math.radians(a[1]),math.radians(b[1]); dla=la2-la1; dlo=math.radians(b[0]-a[0])
    h=math.sin(dla/2)**2+math.cos(la1)*math.cos(la2)*math.sin(dlo/2)**2
    return 2*R*math.asin(math.sqrt(h))
key=lambda p:(round(p[0],6),round(p[1],6))
nodes={}; coords=[]; nroad=collections.defaultdict(set)
def nid(p):
    k=key(p)
    if k not in nodes: nodes[k]=len(coords); coords.append(k)
    return nodes[k]
adj=collections.defaultdict(dict)  # u -> {v:(len,road)}
ends=[]
for road, ls in lines.items():
    if road=='Other': continue
    for l in ls:
        ids=[nid(p) for p in l]
        for i in ids: nroad[i].add(road)
        for a,b in zip(ids,ids[1:]):
            if a==b: continue
            L=hav(coords[a],coords[b]); adj[a][b]=(L,road); adj[b][a]=(L,road)
        ends += [(ids[0],road),(ids[-1],road)]
# grid index
cell=0.01; grid=collections.defaultdict(list)
for i,c in enumerate(coords): grid[(int(c[0]/cell),int(c[1]/cell))].append(i)
def near(i, maxkm, pred):
    c=coords[i]; gx,gy=int(c[0]/cell),int(c[1]/cell); best=None; bd=maxkm
    r=int(maxkm/1.0)+1
    for dx in range(-r,r+1):
        for dy in range(-r,r+1):
            for j in grid.get((gx+dx,gy+dy),()):
                if j==i or j in adj[i] or not pred(j): continue
                d=hav(c,coords[j])
                if d<bd: bd,best=d,j
    return best,bd
# components helper
def comps():
    seen={}; cid=0
    for s in adj:
        if s in seen: continue
        st=[s]; seen[s]=cid
        while st:
            u=st.pop()
            for v in adj[u]:
                if v not in seen: seen[v]=cid; st.append(v)
        cid+=1
    return seen,cid

PAIRS=[('CALAX','SLEX'),('SCTEX','NLEX'),('SCTEX','TPLEX'),('STAR Tollway','SLEX'),('Skyway','SLEX'),('NAIAX','Skyway'),('NAIAX','CAVITEX'),('MCX','SLEX'),('CAVITEX','CALAX'),('Skyway Stage 3','NLEX'),('NLEX Connector','NLEX'),('Harbor Link','NLEX'),('CLLEX','SCTEX'),('CLLEX','TPLEX'),('Subic–Tipo','SCTEX'),('Skyway Stage 3','Skyway'),('NLEX Connector','Skyway Stage 3')]
for a,b in PAIRS:
    A=[i for i in adj if a in nroad[i]]; B=[i for i in adj if b in nroad[i]]
    bg=collections.defaultdict(list)
    for j in B: bg[(int(coords[j][0]/cell),int(coords[j][1]/cell))].append(j)
    best=(1.0,None,None)
    for i in A:
        gx,gy=int(coords[i][0]/cell),int(coords[i][1]/cell)
        for dx in (-1,0,1):
            for dy in (-1,0,1):
                for j in bg.get((gx+dx,gy+dy),()):
                    if i==j: best=(0,None,None); break
                    dd=hav(coords[i],coords[j])
                    if dd<best[0]: best=(dd,i,j)
    if best[1] is not None and best[0]>0:
        adj[best[1]][best[2]]=(best[0],b); adj[best[2]][best[1]]=(best[0],b); print('interchange',a,b,round(best[0],3))
seen,n=comps(); print('components before',n)
stitched=0
for i,road in ends:
    if len(adj[i])!=1: continue
    # connect dead end to nearest node in a different component, or same road farther along
    j,dd0=near(i,1.2,lambda j: seen.get(j)!=seen.get(i) or (len(adj[j])==1 and j!=i))
    if j is not None:
        r2=sorted(nroad[j])[0]; rr=road if road in nroad[j] else r2
        adj[i][j]=(dd0,rr); adj[j][i]=(dd0,rr); stitched+=1
seen,n=comps()
while True:
    cs=collections.defaultdict(list)
    for i,c in seen.items(): cs[c].append(i)
    if len(cs)==1: break
    big=max(cs,key=lambda c:len(cs[c])); merged=False
    for c,members in sorted(cs.items(),key=lambda x:len(x[1])):
        if c==big: continue
        best=(1.5,None,None)
        for i in members:
            j,dd=near(i,best[0],lambda j: seen.get(j) is not None and seen.get(j)!=c)
            if j is not None and dd<best[0]: best=(dd,i,j)
        if best[1] is not None:
            i,j=best[1],best[2]; r=sorted(nroad[j])[0]
            adj[i][j]=(best[0],r); adj[j][i]=(best[0],r); print('joined',sorted({rr for m in members for rr in nroad[m]}),'via',round(best[0],2),'km to',sorted(nroad[j])); merged=True; break
    if not merged: break
    seen,n=comps()
# dead ends that are close to another road but far from it along the graph (missing ramps): connect them
def gdist(a,b,limit):
    dist={a:0};pq=[(0,a)]
    while pq:
        d,u=heapq.heappop(pq)
        if u==b: return d
        if d>limit: return None
        for v,(L,_) in adj[u].items():
            if d+L<dist.get(v,1e9): dist[v]=d+L; heapq.heappush(pq,(d+L,v))
    return None
detour=0
for i in list({e for e,_ in ends}):
    j,dd=near(i,0.8 if len(adj[i])==1 else 0.35,lambda j: j in adj and len(adj[j])>=1)
    if j is None: continue
    g=gdist(i,j,max(4*dd+1.5,3))
    if g is None:
        r=sorted(nroad[j])[0]; adj[i][j]=(dd,r); adj[j][i]=(dd,r); detour+=1
print('detour stitches',detour)
seen,n=comps(); sizes=collections.Counter(seen.values()); print('stitched',stitched,'components after',n, sizes.most_common(6))
for c,_ in sizes.most_common(): print(c, sorted({r for i,cc in seen.items() if cc==c for r in nroad[i]}))
# exits
def clean(n):
    n=re.sub(r'\s+(Toll Plaza|Toll Gate)(\s+[AB])?$','',n); n=re.sub(r'\s+(Northbound|Southbound)\s+(Entry|Exit)$','',n)
    n=re.sub(r'^SLEX\s+|\s+Exit$','',n); n=re.sub(r'^NLEX Mindanao$','Mindanao Avenue',n); n=n.replace('City Toll Plaza','City')
    return n.strip()
ex={}
for f in d['features']:
    if f['geometry']['type']!='Point': continue
    p=f['properties']; x,y=f['geometry']['coordinates']; nm=p.get('name')
    pay='Easytrip' if p.get('payment:easytrip')=='yes' else 'Autosweep' if p.get('payment:autosweep_rfid')=='yes' else None
    # nearest graph node
    gx,gy=int(x/cell),int(y/cell); best=None; bd=0.35
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for j in grid.get((gx+dx,gy+dy),()):
                if j not in adj: continue
                dd=hav((x,y),coords[j])
                if dd<bd: bd,best=dd,j
    if best is None: continue
    road=sorted(nroad[best], key=lambda r: ROADS[r][2] is None)[0]
    if road=='CLLEX': continue
    net=pay or ROADS[road][0]
    name=clean(nm) if nm else None
    k=(name or f'_{best}', road)
    e=ex.setdefault(k,{'name':name,'road':road,'net':net,'pts':[],'nodes':set()})
    e['pts'].append((x,y)); e['nodes'].add(best)
# plazas from data/plazas.csv that are missing or unnamed in OSM: snap onto their road
import csv, os
preg=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','plazas.csv')
if os.path.exists(preg):
    lines_=[l for l in open(preg,encoding='utf-8') if l.strip() and not l.startswith('#')]
    for r in csv.DictReader(lines_):
        if not r.get('lat'): continue
        lat,lon,road=float(r['lat']),float(r['lon']),r['road']
        cand=[j for j in adj if road in nroad[j]]
        j=min(cand,key=lambda j:hav((lon,lat),coords[j]))
        # rename an unnamed OSM plaza nearby, else add a new one
        hit=None
        for k_,e in ex.items():
            if e['name'] is None and e['road']==road and min(hav(coords[n],coords[j]) for n in e['nodes'])<0.6: hit=k_;break
        if hit:
            e=ex.pop(hit); e['name']=r['name']; e['approx']=False; ex[(r['name'],road)]=e
        else:
            ex[(r['name'],road)]={'name':r['name'],'road':road,'net':ROADS[road][0],'pts':[coords[j]],'nodes':{j},'approx':True}
        print('registry plaza',r['name'],road,'renamed OSM' if hit else 'added (approx)')
exits=[]
for (k,road),e in ex.items():
    x=sum(p[0] for p in e['pts'])/len(e['pts']); y=sum(p[1] for p in e['pts'])/len(e['pts'])
    exits.append(e|{'x':x,'y':y})
names=collections.Counter(e['name'] for e in exits if e['name'])
for e in exits:
    e['label']=e['name'] and (e['name'] if names[e['name']]==1 else f"{e['name']} ({e['road'].replace(' Tollway','')})")
# keep nodes: junctions, endpoints, exit nodes, road changes
keep=set(i for i in adj if len(adj[i])!=2)
for e in exits: keep|=e['nodes']
for i in adj:
    if len(adj[i])==2:
        rs={r for (_,r) in adj[i].values()}
        if len(rs)>1: keep.add(i)
# compress
idx={}; N=[]
def kid(i):
    if i not in idx: idx[i]=len(N); N.append([round(coords[i][0],5),round(coords[i][1],5)])
    return idx[i]
E=[]; done=set()
for s in keep:
    for v in adj[s]:
        if (s,v) in done: continue
        path=[s,v]; L=adj[s][v][0]; road=adj[s][v][1]; prev,cur=s,v
        while cur not in keep:
            nxt=[w for w in adj[cur] if w!=prev][0]
            L+=adj[cur][nxt][0]; prev,cur=cur,nxt; path.append(cur)
        done.add((s,path[1])); done.add((cur,path[-2]))
        pts=dp([list(coords[i]) for i in path],0.0001)
        E.append([kid(s),kid(cur),round(L,3),road,[[round(a,5),round(b,5)] for a,b in pts[1:-1]]])
print('graph nodes',len(N),'edges',len(E),'exits',len(exits),'labelled',sum(1 for e in exits if e['label']))
# sanity routes
G=collections.defaultdict(list)
for a,b,L,r,_ in E: G[a].append((b,L,r)); G[b].append((a,L,r))
def route(A,B):
    src=[idx[n] for n in A['nodes']]; dst={idx[n] for n in B['nodes']}
    dist={s:0 for s in src}; pq=[(0,s) for s in src]; prev={}
    while pq:
        dd,u=heapq.heappop(pq)
        if u in dst:
            rs=collections.Counter()
            while u in prev: p,r,L=prev[u]; rs[r]+=L; u=p
            return round(dd,1),dict((k,round(v,1)) for k,v in rs.items())
        if dd>dist.get(u,1e9): continue
        for v,L,r in G[u]:
            if dd+L<dist.get(v,1e9): dist[v]=dd+L; prev[v]=(u,r,L); heapq.heappush(pq,(dd+L,v))
    return None
byl={e['label']:e for e in exits if e['label']}
for a,b in [('Balintawak','Dau'),('Balintawak','Rosario'),('Magallanes','Calamba'),('Nichols','Calamba'),('Calamba','Batangas City'),('Balintawak','Batangas City'),('Kawit','Mamplasan'),('Tipo','Rosario'),('Quezon Avenue','Alabang (Skyway)'),('Karuhatan','Sucat (CAVITEX)')]:
    A=byl.get(a) or next((e for l,e in byl.items() if l.startswith(a)),None); B=byl.get(b) or next((e for l,e in byl.items() if l.startswith(b)),None)
    print(a,'->',b, A and A['label'], B and B['label'], route(A,B) if A and B else 'missing')
out={'nodes':N,'edges':E,'exits':[{'l':e['label'],'r':e['road'],'net':e['net'],'x':round(e['x'],5),'y':round(e['y'],5),'n':sorted(idx[i] for i in e['nodes']),**({'a':1} if e.get('approx') else {})} for e in exits]}
json.dump(out,open('data/graph.json','w'),separators=(',',':'))
print(sorted(byl))
