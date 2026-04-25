import json, os
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GJ = os.path.join(ROOT, 'graphify-out', 'graph.json')
OUT = os.path.join(ROOT, 'Obsidian Vault', 'Graph Top Nodes.md')

with open(GJ, 'r', encoding='utf-8') as f:
    data = json.load(f)

# compute degrees from links
deg = Counter()
links = []
for link in data.get('links', []):
    src = link.get('_src') or link.get('source')
    tgt = link.get('_tgt') or link.get('target')
    if src and tgt:
        deg[src] += 1
        deg[tgt] += 1
        links.append((src, tgt))

# map id->label
id2label = {n['id']: n.get('label', n['id']) for n in data['nodes']}

# select top N
topn = [nid for nid, _ in deg.most_common(12)]

mermaid = ['---','id: graph-top-nodes','tags:','  - graph','  - top-nodes','---','\n# Top Connected Nodes\n','```mermaid','graph LR']

# add nodes
for nid in topn:
    lbl = id2label.get(nid, nid)
    safe = 'N' + nid.replace('-', '_')[:40]
    mermaid.append(f'    {safe}["{lbl}"]')

# add edges among top nodes
for a,b in links:
    if a in topn and b in topn:
        sa = 'N' + a.replace('-', '_')[:40]
        sb = 'N' + b.replace('-', '_')[:40]
        mermaid.append(f'    {sa} --> {sb}')

mermaid.append('```')

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(mermaid))

print('Wrote', OUT)
