@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "ENV_DIR=%SCRIPT_DIR%.conda-py311"
set "PYTHON_CMD="

cd /d "%SCRIPT_DIR%"

echo =====================================
echo Industrial Control Platform - Start
echo =====================================
echo.

if exist "%ENV_DIR%\python.exe" (
    set "PYTHON_CMD=%ENV_DIR%\python.exe"
) else (
    echo Local Python environment was not found:
    echo    %ENV_DIR%
    echo.
    echo Please run install_dependencies.bat first.
    pause
    exit /b 1
)

if not exist "start_services.py" (
    echo start_services.py was not found in:
    echo    %SCRIPT_DIR%
    pause
    exit /b 1
)

echo Using Python environment:
echo    %ENV_DIR%
echo.

%PYTHON_CMD% -c "import flask, pandas, numpy, loguru, pymodbus, paho.mqtt.client" >nul 2>&1
if !errorlevel! neq 0 (
    echo Python dependencies are incomplete.
    echo Please run install_dependencies.bat again.
    pause
    exit /b 1
)

echo Starting services...
echo.
%PYTHON_CMD% start_services.py

set "EXIT_CODE=!errorlevel!"
echo.
echo Service manager exited with code !EXIT_CODE!.
pause
exit /b !EXIT_CODE!
