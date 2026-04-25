---
id: graph-top-nodes
tags:
  - graph
  - top-nodes
---

# Top Connected Nodes

```mermaid
graph LR
    Nrpi_drone_bridge_dronemonitor["DroneMonitor"]
    Nrpi_drone_bridge_dronemonitor_run[".run()"]
    Nc_workspace_iotel_laptop_laptop_gcs_py["laptop_gcs.py"]
    Nlaptop_gcs_gcsstate["GCSState"]
    Nlaptop_gcs_gcsstate_connect_to_rpi[".connect_to_rpi()"]
    Nc_workspace_iotel_rpi_rpi_drone_bridge_p["rpi_drone_bridge.py"]
    Nrpi_drone_bridge_main["main()"]
    Nlaptop_gcs_main["main()"]
    Nrpi_drone_bridge_dronemonitor_connect[".connect()"]
    Nrpi_drone_bridge_gps_distance_meters["gps_distance_meters()"]
    Nrpi_drone_bridge_dronemonitor_detect_ano[".detect_anomalies()"]
    Nrpi_drone_bridge_dronemonitor_stop[".stop()"]
    Nc_workspace_iotel_laptop_laptop_gcs_py --> Nlaptop_gcs_gcsstate
    Nc_workspace_iotel_laptop_laptop_gcs_py --> Nlaptop_gcs_main
    Nlaptop_gcs_gcsstate --> Nlaptop_gcs_gcsstate_connect_to_rpi
    Nlaptop_gcs_main --> Nlaptop_gcs_gcsstate_connect_to_rpi
    Nlaptop_gcs_gcsstate_connect_to_rpi --> Nrpi_drone_bridge_dronemonitor_connect
    Nlaptop_gcs_main --> Nrpi_drone_bridge_dronemonitor_run
    Nc_workspace_iotel_rpi_rpi_drone_bridge_p --> Nrpi_drone_bridge_gps_distance_meters
    Nc_workspace_iotel_rpi_rpi_drone_bridge_p --> Nrpi_drone_bridge_dronemonitor
    Nc_workspace_iotel_rpi_rpi_drone_bridge_p --> Nrpi_drone_bridge_main
    Nrpi_drone_bridge_dronemonitor_detect_ano --> Nrpi_drone_bridge_gps_distance_meters
    Nrpi_drone_bridge_dronemonitor --> Nrpi_drone_bridge_dronemonitor_connect
    Nrpi_drone_bridge_dronemonitor --> Nrpi_drone_bridge_dronemonitor_detect_ano
    Nrpi_drone_bridge_dronemonitor --> Nrpi_drone_bridge_dronemonitor_run
    Nrpi_drone_bridge_dronemonitor --> Nrpi_drone_bridge_dronemonitor_stop
    Nrpi_drone_bridge_main --> Nrpi_drone_bridge_dronemonitor
    Nrpi_drone_bridge_dronemonitor_run --> Nrpi_drone_bridge_dronemonitor_connect
    Nrpi_drone_bridge_dronemonitor_run --> Nrpi_drone_bridge_dronemonitor_detect_ano
    Nrpi_drone_bridge_dronemonitor_run --> Nrpi_drone_bridge_dronemonitor_stop
    Nrpi_drone_bridge_main --> Nrpi_drone_bridge_dronemonitor_run
    Nrpi_drone_bridge_main --> Nrpi_drone_bridge_dronemonitor_stop
```