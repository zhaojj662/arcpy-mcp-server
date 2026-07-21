#!/usr/bin/env python3
# arcpy_mcp_bridge.py — MCP stdio→HTTP bridge for AutoClaw v2
# 适配 arcpy_mcp_server_full.py (1300+ tools)

import json, sys, urllib.request, urllib.error

ARCPY_URL = "http://127.0.0.1:8765"

def http_get(path):
    try:
        with urllib.request.urlopen(f"{ARCPY_URL}{path}", timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def http_post(path, body):
    try:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(f"{ARCPY_URL}{path}", data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=300) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def read_msg():
    line = sys.stdin.readline()
    if not line: return None
    return json.loads(line)

def write_msg(msg):
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()

def main():
    health = http_get("/health")
    if health.get("status") != "ok":
        write_msg({"jsonrpc":"2.0","id":0,"error":{"code":-32000,"message":f"arcpy HTTP not reachable: {health}"}})
        return
    sys.stderr.write(f"[bridge] arcpy-mcp-server v{health.get('version')} | {health.get('tools')} tools\n")
    sys.stderr.flush()
    
    while True:
        msg = read_msg()
        if msg is None: break
        
        method = msg.get("method", "")
        mid = msg.get("id")
        
        if method == "initialize":
            write_msg({"jsonrpc":"2.0","id":mid,"result":{
                "protocolVersion":"2024-11-05",
                "serverInfo":{"name":"arcpy-mcp-server","version":health.get("version","2.0")},
                "capabilities":{"tools":{}}
            }})
        
        elif method == "tools/list":
            result = http_get("/tools")
            tools = result.get("tools", [])
            if result.get("has_more"):
                sys.stderr.write(f"[bridge] Warning: {result['total']} tools, only first 200 returned\n")
                sys.stderr.flush()
            write_msg({"jsonrpc":"2.0","id":mid,"result":{"tools":tools}})
        
        elif method == "tools/call":
            params = msg.get("params", {})
            name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = http_post("/call", {"name": name, "arguments": arguments})
            
            if "error" in result and "status" not in result:
                write_msg({"jsonrpc":"2.0","id":mid,"error":{"code":-32603,"message":result["error"]}})
            elif result.get("status") == "error":
                write_msg({"jsonrpc":"2.0","id":mid,"result":{"content":[{
                    "type":"text", "text": json.dumps(result, ensure_ascii=False)
                }],"isError": True}})
            else:
                write_msg({"jsonrpc":"2.0","id":mid,"result":{"content":[{
                    "type":"text", "text": json.dumps(result, ensure_ascii=False)
                }]}})
        
        elif mid is None:
            if method == "notifications/initialized":
                sys.stderr.write("[bridge] Client initialized\n")
                sys.stderr.flush()
        else:
            write_msg({"jsonrpc":"2.0","id":mid,"error":{"code":-32601,"message":f"Unknown: {method}"}})

if __name__ == "__main__":
    main()
