"""
arcpy_mcp_server_full.py — 自动注册 ArcGIS Pro 全部工具
扫描所有 arcpy 模块，自动生成 Tool Schema，通过 HTTP 暴露
兼容 Python 3.9 (ArcGIS Pro 3.0)
"""

import json, sys, os, http.server, time, traceback, re
import datetime as _real_dt  # before arcpy shadow

import io
_old = sys.stdout
sys.stdout = io.StringIO()
import arcpy
sys.stdout = _old

sys.modules['datetime'] = _real_dt

VER = "2.0"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

# ============================================================
# 1. AUTO-SCAN: Discover all arcpy tools and build registry
# ============================================================

TOOL_REGISTRY = {}  # name -> {"module": module_name, "func": tool_name, "schema": {...}}
TOOLS_BY_MODULE = {}  # module_name -> [tool_names]

TYPE_MAP = {
    "Feature Layer": "string", "Raster Layer": "string",
    "String": "string", "Long": "integer", "Double": "number",
    "Boolean": "boolean", "Workspace": "string",
    "Table": "string", "Folder": "string", "File": "string",
    "Field": "string", "SQL Expression": "string",
    "Coordinate System": "string", "Linear Unit": "string",
}

# Core modules to register (exclude internal/overwhelming modules)
INCLUDE_MODULES = [
    'analysis', 'management', 'conversion', 'sa', 'ga', 'ddd',
    'stats', 'cartography', 'geocoding', 'stpm', 'na', 'nax',
    'edit', 'server', 'sharing',
]

for mod_name in dir(arcpy):
    if mod_name.startswith('_'):
        continue
    if mod_name not in INCLUDE_MODULES:
        continue
    m = getattr(arcpy, mod_name)
    tools = [t for t in dir(m) if not t.startswith('_') and t[0].isupper()]
    
    for func_name in tools:
        tool_id = f"{mod_name}_{func_name}"
        try:
            func = getattr(m, func_name)
            # Basic schema: just accept **kwargs
            TOOL_REGISTRY[tool_id] = {
                "module": mod_name,
                "func": func_name,
                "schema": {
                    "type": "object",
                    "properties": {
                        "__kwargs": {"type": "string", "description": f"JSON string of kwargs for arcpy.{mod_name}.{func_name}"}
                    },
                    "required": []
                }
            }
            TOOLS_BY_MODULE.setdefault(mod_name, []).append(func_name)
        except:
            pass

TOTAL_TOOLS = len(TOOL_REGISTRY)
TOTAL_MODULES = len(TOOLS_BY_MODULE)

print(f"[arcpy-mcp] Registered {TOTAL_TOOLS} tools across {TOTAL_MODULES} modules", flush=True)

# ============================================================
# 2. HTTP Server
# ============================================================

ALLOWED_PATHS = ["C:/GIS-AI-Course/", "C:\\GIS-AI-Course\\"]

def check_path(p):
    if not p or not isinstance(p, str):
        return True
    p = p.replace("\\", "/").lower()
    return any(p.startswith(a.replace("\\", "/").lower()) for a in ALLOWED_PATHS)

class MCP(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.json({"status": "ok", "server": "arcpy-mcp-server", "version": VER, "tools": TOTAL_TOOLS, "modules": TOTAL_MODULES})
        elif self.path == "/tools":
            tools_list = []
            for tid, tdef in sorted(TOOL_REGISTRY.items()):
                tools_list.append({
                    "name": tid,
                    "description": f"arcpy.{tdef['module']}.{tdef['func']}",
                    "inputSchema": tdef["schema"]
                })
            # Paginate: return first 200 tools to avoid overwhelming clients
            self.json({"tools": tools_list[:200], "total": len(tools_list), "has_more": len(tools_list) > 200})
        elif self.path == "/modules":
            mods = {}
            for mod, funcs in sorted(TOOLS_BY_MODULE.items()):
                mods[mod] = {"count": len(funcs), "tools": funcs[:20]}
            self.json({"modules": mods})
        elif self.path.startswith("/module/"):
            mod_name = self.path.split("/")[-1]
            funcs = TOOLS_BY_MODULE.get(mod_name, [])
            self.json({"module": mod_name, "tools": funcs})
        elif self.path.startswith("/tool/"):
            tool_id = self.path.split("/")[-1]
            tdef = TOOL_REGISTRY.get(tool_id, {})
            self.json({"tool": tool_id, "module": tdef.get("module"), "func": tdef.get("func")})
        else:
            self.json({"error": "not found"}, 404)
    
    def do_POST(self):
        if self.path != "/call":
            self.json({"error": "not found"}, 404)
            return
        
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            tool_id = body.get("name", "")
            args = body.get("arguments", {})
            
            # Path security check
            for k, v in args.items():
                if isinstance(v, str) and ("/" in v or "\\" in v) and (".shp" in v.lower() or ".tif" in v.lower() or ".gdb" in v.lower()):
                    if not check_path(v):
                        self.json({"status": "error", "message": f"Path not allowed: {v}"}, 403)
                        return
            
            tdef = TOOL_REGISTRY.get(tool_id)
            if not tdef:
                self.json({"status": "error", "message": f"Tool not found: {tool_id}. Call /tools to list available tools."}, 404)
                return
            
            arcpy.env.overwriteOutput = True
            t0 = time.time()
            
            mod = getattr(arcpy, tdef["module"])
            func = getattr(mod, tdef["func"])
            
            # Parse kwargs: handle both flat args and JSON string kwargs
            if "__kwargs" in args and len(args) == 1:
                kwargs = json.loads(args["__kwargs"])
            else:
                kwargs = {k: v for k, v in args.items() if not k.startswith("__")}
            
            # Execute!
            result = func(**kwargs)
            
            elapsed = round(time.time() - t0, 2)
            info = {"execution_time_seconds": elapsed}
            
            # Try to extract output info from kwargs
            out = kwargs.get("out_feature_class") or kwargs.get("out_dataset") or kwargs.get("out_raster") or args.get("out_feature_class", "")
            if out and isinstance(out, str) and os.path.exists(out):
                try:
                    info["output"] = out
                    info["feature_count"] = int(arcpy.GetCount_management(out)[0])
                    info["geometry_type"] = str(arcpy.Describe(out).shapeType)
                except:
                    try:
                        from arcpy import Raster
                        r = Raster(out)
                        info["output"] = out
                        info["raster_width"] = r.width
                        info["raster_height"] = r.height
                    except:
                        pass
            elif result:
                info["result"] = str(result)[:200]
            
            self.json({"status": "success", "tool": tool_id, "info": info})
        
        except arcpy.ExecuteError:
            msg = arcpy.GetMessages(2)[:500]
            hint = "Check inputs"
            if "000732" in msg:
                hint = "Dataset not found"
            elif "000725" in msg:
                hint = "Output exists, use overwriteOutput=True"
            elif "000735" in msg:
                hint = "Invalid parameter format"
            elif "000622" in msg:
                hint = "Invalid data type for parameter"
            self.json({"status": "error", "tool": tool_id, "message": msg.strip(), "suggestion": hint})
        except Exception as e:
            self.json({"status": "error", "tool": tool_id, "message": str(e)[:500]})
    
    def json(self, data, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    
    def log_message(self, *args):
        pass

if __name__ == "__main__":
    s = http.server.HTTPServer(("127.0.0.1", PORT), MCP)
    print(f"arcpy-mcp-server v{VER} | http://127.0.0.1:{PORT}", flush=True)
    print(f"Registered: {TOTAL_TOOLS} tools across {TOTAL_MODULES} modules", flush=True)
    print(f"Modules: {', '.join(sorted(TOOLS_BY_MODULE.keys()))}", flush=True)
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        s.shutdown()
        print("\nShutting down...", flush=True)
