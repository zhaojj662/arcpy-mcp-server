# arcpy-mcp-server -- AI + GIS Smart Spatial Analysis

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![ArcGIS Pro](https://img.shields.io/badge/ArcGIS%20Pro-3.x-green)](https://www.esri.com/)

> Let LLMs (GPT-4o, Claude, DeepSeek) directly operate ArcGIS Pro -- drive 1300+ spatial analysis tools with natural language.

## What is this?

**arcpy-mcp-server** exposes all ArcGIS Pro toolboxes as MCP (Model Context Protocol) tools, enabling:

```
You: "Buffer analysis 500m around the university"
AI: Auto-calls arcpy -> ArcGIS Pro -> generates result
```

No tool names to memorize. No Python to write. No menus to click.

## Features

- **1300+ tools** across 15 modules: management(392), sa(355), ddd(144), stats(44), ga(39), analysis(38) + 9 more
- **MCP standard**: works with AutoClaw, Claude Code, Codex, any MCP client
- **Zero dependencies**: uses ArcGIS Pro's built-in Python 3.9
- **Security whitelist**: configurable path and tool restrictions
- **One-click install**: 30 seconds from clone to running

## Supported Modules

| Module | Tools | Highlights |
|--------|-------|------------|
| management | 392 | Data management, projection, fields, topology |
| sa (Spatial Analyst) | 355 | Slope, aspect, reclassify, viewshed, hydrology |
| ddd (3D Analyst) | 144 | DEM, contours, viewshed2, skyline, point cloud |
| nax (Network Analyst) | 61 | Route, service area, OD matrix |
| conversion | 57 | JSON/KML/CAD/Excel/raster conversion |
| na | 55 | Legacy network analysis |
| stats (Spatial Statistics) | 44 | Moran's I, Gi*, KDE, Ripley's K, GWR |
| cartography | 44 | Contour labels, aggregation, simplification |
| ga (Geostatistical) | 39 | Kriging, IDW, EBK, cross-validation |
| analysis | 38 | Buffer, Clip, Intersect, Erase, Union, Thiessen |
| edit | 18 | Align, extend, trim, split, merge |
| server | 18 | Publish services, cache, tiles |
| stpm (SpaceTime) | 16 | Space-time cube, emerging hotspots |
| geocoding | 13 | Address matching, reverse geocoding |
| sharing | 6 | Web layers, web maps, scene sharing |

## Quick Start

### Prerequisites

- Windows 10/11
- ArcGIS Pro 3.x (with valid license)
- Python 3.9+

### Install

```powershell
git clone https://github.com/zhaojj662/arcpy-mcp-server.git
cd arcpy-mcp-server
install.bat
```

### Start Server

Double-click `start_server.bat` or run:

```powershell
start_server.bat
```

Server runs on `http://127.0.0.1:8765`.

Verify:

```powershell
Invoke-RestMethod http://127.0.0.1:8765/health
# {"status":"ok","server":"arcpy-mcp-server","version":"2.0","tools":1300}
```

### Configure AI Client

**AutoClaw MCP Settings:**

| Field | Value |
|-------|-------|
| Name | arcpy |
| Mode | Local process (stdio) |
| Command | python |
| Args | path/to/mcp_bridge.py |

**Claude Code** (claude_desktop_config.json):

```json
{
  "mcpServers": {
    "arcpy": {
      "command": "python",
      "args": ["C:/Users/%USERNAME%/arcpy-mcp-server/mcp_bridge.py"]
    }
  }
}
```

### Try It

```
"Buffer roads.shp by 500 meters"
"Calculate slope and aspect from this DEM"
"Hotspot analysis on crime points"
"Kriging interpolation on PM2.5 monitoring data"
"Batch viewshed for 100 observer points"
```

## Architecture

```
AI Client <-- stdio --> mcp_bridge.py <-- HTTP --> server.py (arcpy) --> ArcGIS Pro 3.x
```

## Security

Edit `server.py` to restrict access:

```python
ALLOWED_PATHS = ["C:/GIS-AI-Course/"]  # Only allow these directories
INCLUDE_MODULES = ["analysis", "sa"]   # Only expose these modules
```

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| /health | GET | Server status, tool count |
| /tools | GET | List available tools (first 200) |
| /modules | GET | List all modules with tool counts |
| /call | POST | Execute a tool |

## FAQ

**Q: Is ArcGIS Pro required?**
A: Yes. arcpy runs only inside the ArcGIS Pro Python environment.

**Q: Supported ArcGIS Pro versions?**
A: 3.x series (tested on 3.0).

**Q: Can I limit which tools AI can access?**
A: Yes. Edit `INCLUDE_MODULES` in `server.py`.

## License

MIT -- see [LICENSE](LICENSE)
