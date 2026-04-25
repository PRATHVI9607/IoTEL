import json
import os
import networkx as nx
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GJ = os.path.join(ROOT, 'graphify-out', 'graph.json')
PNG = os.path.join(ROOT, 'graphify-out', 'graph_full.png')
SVG = os.path.join(ROOT, 'graphify-out', 'graph_full.svg')

with open(GJ, 'r', encoding='utf-8') as f:
    data = json.load(f)

G = nx.Graph()

id_to_label = {n['id']: n.get('label', n['id']) for n in data['nodes']}
for nid, label in id_to_label.items():
    G.add_node(nid, label=label)

for link in data.get('links', []):
    src = link.get('_src') or link.get('source') or link.get('source_id')
    tgt = link.get('_tgt') or link.get('target') or link.get('target_id')
    if src and tgt and src in id_to_label and tgt in id_to_label:
        G.add_edge(src, tgt)

# Draw a pretty graph
plt.figure(figsize=(12, 12))
pos = nx.spring_layout(G, seed=42, k=0.5)
labels = {n: id_to_label.get(n, n) for n in G.nodes()}

# color by community if present
communities = {}
for n in data['nodes']:
    communities[n['id']] = n.get('community', 0)
colors = [communities.get(n, 0) for n in G.nodes()]

nx.draw_networkx_nodes(G, pos, node_size=300, node_color=colors, cmap=plt.cm.tab20)
nx.draw_networkx_edges(G, pos, alpha=0.4)
nx.draw_networkx_labels(G, pos, labels, font_size=8)
plt.axis('off')
plt.tight_layout()
plt.savefig(PNG, dpi=200)
plt.savefig(SVG)
print('Saved', PNG, SVG)

# Create a simplified mermaid for top-level files
file_nodes = [n for n in data['nodes'] if n.get('file_type') == 'code' and n.get('source_file')]
# pick nodes whose label endswith .py or README.md or .md
top_files = {}
for n in file_nodes:
    label = n['label']
    if label.endswith('.py') or label.lower().endswith('.md'):
        top_files[n['id']] = label

mermaid_lines = ['graph TD']
for link in data.get('links', []):
    src = link.get('_src')
    tgt = link.get('_tgt')
    if src in top_files and tgt in top_files:
        a = top_files[src].replace('.', '_')
        b = top_files[tgt].replace('.', '_')
        mermaid_lines.append(f'    {a}["{top_files[src]}"] --> {b}["{top_files[tgt]}"]')

MERMAID = os.path.join(ROOT, 'Obsidian Vault', 'Graph Summary.md')
with open(MERMAID, 'w', encoding='utf-8') as f:
    f.write('---\n')
    f.write('id: graph-summary\n')
    f.write('tags:\n  - graph\n  - summary\n')
    f.write('---\n\n')
    f.write('# Project Graph Summary\n\n')
    f.write('![Full Graph](../graphify-out/graph_full.png)\n\n')
    f.write('```mermaid\n')
    f.write('\n'.join(mermaid_lines) + '\n')
    f.write('```\n')

print('Wrote mermaid summary to', MERMAID)
