@echo off
REM ============================================================
REM  arcpy-mcp-server 一键安装脚本 (Windows)
REM  用法: 双击 install.bat 或 在终端中运行 install.bat
REM ============================================================

title arcpy-mcp-server Installer

echo.
echo  ============================================
echo    arcpy-mcp-server - 安装程序
echo    LLM + MCP + ArcGIS Pro 智能空间分析
echo  ============================================
echo.

:: Check Python
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] 未找到 Python，请先安装 Python 3.9+
    echo         下载: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version

:: Check ArcGIS Pro
echo [2/4] 检查 ArcGIS Pro...
if not exist "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" (
    echo [WARN] 未检测到 ArcGIS Pro 3.x
    echo         arcpy-mcp-server 需要 ArcGIS Pro 3.x
    echo         请确认 ArcGIS Pro 已安装后再继续
    echo.
    set /p CONTINUE="是否继续安装（仅安装客户端部分）? [y/N] "
    if /i not "%CONTINUE%"=="y" exit /b 1
) else (
    echo [OK] 检测到 ArcGIS Pro
)

:: Install dependencies
echo [3/4] 安装 Python 依赖...
pip install --upgrade pip -q
pip install openai -q -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn

:: Copy files to install location
echo [4/4] 部署文件...
set INSTALL_DIR=%USERPROFILE%\arcpy-mcp-server
mkdir "%INSTALL_DIR%" 2>nul
xcopy /Y /Q "%~dp0src\*" "%INSTALL_DIR%\"
xcopy /Y /Q "%~dp0bridge\*" "%INSTALL_DIR%\"
xcopy /Y /Q "%~dp0config_example.json" "%INSTALL_DIR%\" 2>nul

echo.
echo  ============================================
echo    安装完成！
echo  ============================================
echo.
echo   文件位置: %INSTALL_DIR%
echo.
echo   启动服务:
echo     1. 右键以管理员运行 "启动arcpy服务.bat"
echo     2. ArcGIS Pro 自带 Python 会自动启动 HTTP 服务
echo.
echo   配置 AutoClaw / Claude Code:
echo     见 %INSTALL_DIR%\README.md
echo.
pause
