# Bygg & Terreng Plugin — Rhino 8

A Python-based Rhino plugin for AI-assisted 3D terrain and building generation.
Developed as part of a bachelor thesis in Data Engineering at NTNU Ålesund.

---

## Overview

The plugin generates realistic 3D terrain from real Norwegian elevation data, drapes satellite imagery over it, and places AI-generated building geometry directly onto the terrain. Everything runs inside Rhino 8 through a persistent floating panel.

---

## Requirements

- Rhino 8
- Internet connection (for terrain and satellite data)
- FastAPI backend running locally on `http://localhost:8000` (for AI building parameters)

---

## Technology

| Component | Technology |
|---|---|
| 3D environment | Rhino 8 / IronPython |
| Elevation data | Kartverket WCS — NHM DTM |
| Satellite imagery | ESRI World Imagery |
| AI parameters | FastAPI + local LLM backend |

---

## How to Run

1. Open Rhino 8
2. Type `RunPythonScript` in the command bar
3. Select `plugin_panel.py` from the `src/` folder and inside `main/` folder
4. The plugin panel will open and remain active for the session

---

## Workflow

1. **Terrain** — Enter GPS coordinates and size, fetch elevation mesh from Kartverket
2. **Satellite** — Drop aerial imagery over the terrain (switch to *Rendered* view)
3. **Building** — Select a box in Rhino, generate walls, windows and roof via AI
4. **Placement** — Snap the building onto the terrain with automatic ground flattening