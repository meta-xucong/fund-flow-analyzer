@echo off
chcp 65001 >nul
title 盘前资金流向分析系统
cd /d "%~dp0"

echo ==========================================
echo   盘前资金流向分析系统 v1.0
echo   Fund Flow Analyzer
echo ==========================================
echo.

REM 检查Python
if exist "python\python.exe" (
    set PYTHON=python\python.exe
    goto :RUN
)

where python >nul 2>nul
if %errorlevel% == 0 (
    set PYTHON=python
    goto :RUN
)

echo [*] 未检测到Python环境，准备下载嵌入式Python...
echo [*] 下载可能需要几分钟，请耐心等待...
echo.

REM 创建python目录
if not exist python mkdir python

REM 下载Python 3.11.9 嵌入式版本
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile 'python.zip'" 2>nul

if not exist python.zip (
    echo [!] 下载失败，请手动安装Python 3.11+ 后重试
    echo [*] 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [*] 解压Python...
powershell -Command "Expand-Archive -Path 'python.zip' -DestinationPath 'python' -Force"
del python.zip

REM 修改python311._pth文件以启用site-packages
echo Lib> python\python311._pth
echo .>> python\python311._pth
echo import site>> python\python311._pth

REM 下载get-pip.py
echo [*] 下载pip...
powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'python\get-pip.py'" 2>nul
python\python.exe python\get-pip.py --quiet
del python\get-pip.py

set PYTHON=python\python.exe
echo [OK] Python环境准备完成
echo.

:RUN
echo [*] 检查依赖...
%PYTHON% -c "import flask, pandas, akshare, requests, psutil" 2>nul
if %errorlevel% == 0 goto :START

echo [*] 安装依赖（首次运行需要）...
%PYTHON% -m pip install -q flask pandas akshare requests psutil --no-warn-script-location
if %errorlevel% neq 0 (
    echo [!] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)
echo [OK] 依赖安装完成
echo.

:START
echo [*] 启动服务...
echo [*] 启动后请用浏览器访问: http://localhost:5000
echo [*] 在窗口中按 Ctrl+C 可停止服务
echo.
echo ==========================================
%PYTHON% launch.py

echo.
echo [*] 服务已停止
echo.
pause
