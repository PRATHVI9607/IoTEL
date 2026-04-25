---
id: Laptop GCS (Ground Control Station)
tags:
  - laptop
  - software
  - web
---

# 💻 Laptop GCS (Ground Control Station)

The Ground Control Station runs on a standard machine (Windows, Mac, or Linux). 

## Responsibilities
- **Web Dashboard**: Displays telemetry (Alt, Heading, Battery, GPS status).
- **Voice Recognition**: Listens for **[[Voice Commands]]** from the user.
- **Telemetry Display**: Parses incoming MAVLink or TCP data from the **[[RPI Drone Bridge]]**.

## Running the Setup
1. Look at `laptop/laptop_gcs.py`.
2. Connect to the RPI's IP Address over Wi-Fi.

```bash
python laptop_gcs.py --rpi 192.168.1.100
```

Once running, navigate to `http://localhost:5000` to see the dashboard.
