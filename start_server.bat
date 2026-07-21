@echo off
REM 启动 arcpy-mcp-server (后台运行)
REM 使用 ArcGIS Pro 自带的 Python 环境

title arcpy-mcp-server (HTTP on :8765)

set ARCGIS_PYTHON=C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe

if not exist "%ARCGIS_PYTHON%" (
    echo [ERROR] 未找到 ArcGIS Pro Python 环境
    echo 请确认 ArcGIS Pro 3.x 已安装在默认路径
    pause
    exit /b 1
)

echo Starting arcpy-mcp-server on http://127.0.0.1:8765 ...
echo ArcGIS Pro 3.x Python: %ARCGIS_PYTHON%
echo.
echo 按 Ctrl+C 停止服务
echo ============================================

"%ARCGIS_PYTHON%" "%~dp0server.py" 8765
