# Graph Report - C:\Workspace\IoTEL  (2026-04-23)

## Corpus Check
- 2 files · ~7,372 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 33 nodes · 52 edges · 9 communities detected
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 2 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]

## God Nodes (most connected - your core abstractions)
1. `DroneMonitor` - 14 edges
2. `GCSState` - 7 edges
3. `main()` - 4 edges
4. `main()` - 3 edges
5. `gps_distance_meters()` - 3 edges
6. `api_connect()` - 2 edges
7. `api_disconnect()` - 2 edges
8. `api_status()` - 2 edges
9. `api_command()` - 2 edges
10. `Config` - 1 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `DroneMonitor`  [EXTRACTED]
  C:\Workspace\IoTEL\rpi\rpi_drone_bridge.py → C:\Workspace\IoTEL\rpi\rpi_drone_bridge.py  _Bridges community 0 → community 8_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.36
Nodes (1): DroneMonitor

### Community 1 - "Community 1"
Cohesion: 0.4
Nodes (3): Config, gps_distance_meters(), Calculate distance between two GPS coordinates using Haversine formula

### Community 2 - "Community 2"
Cohesion: 0.5
Nodes (1): api_connect()

### Community 3 - "Community 3"
Cohesion: 0.67
Nodes (1): GCSState

### Community 4 - "Community 4"
Cohesion: 0.67
Nodes (1): main()

### Community 5 - "Community 5"
Cohesion: 1.0
Nodes (1): api_disconnect()

### Community 6 - "Community 6"
Cohesion: 1.0
Nodes (1): api_status()

### Community 7 - "Community 7"
Cohesion: 1.0
Nodes (1): api_command()

### Community 8 - "Community 8"
Cohesion: 1.0
Nodes (1): main()

## Knowledge Gaps
- **2 isolated node(s):** `Config`, `Calculate distance between two GPS coordinates using Haversine formula`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 5`** (2 nodes): `api_disconnect()`, `.disconnect()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 6`** (2 nodes): `api_status()`, `.get_state()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 7`** (2 nodes): `api_command()`, `.send_command()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 8`** (2 nodes): `.stop()`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 4` to `Community 0`, `Community 2`?**
  _High betweenness centrality (0.322) - this node is a cross-community bridge._
- **Why does `DroneMonitor` connect `Community 0` to `Community 8`, `Community 1`, `Community 4`?**
  _High betweenness centrality (0.277) - this node is a cross-community bridge._
- **Why does `GCSState` connect `Community 3` to `Community 2`, `Community 4`, `Community 5`, `Community 6`, `Community 7`?**
  _High betweenness centrality (0.263) - this node is a cross-community bridge._
- **What connects `Config`, `Calculate distance between two GPS coordinates using Haversine formula` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._