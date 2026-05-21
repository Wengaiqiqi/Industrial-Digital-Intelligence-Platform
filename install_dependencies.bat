@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "ENV_DIR=%SCRIPT_DIR%.conda-py311"
set "PYTHON_CMD="
set "CONDA_EXE="

echo =====================================
echo Industrial Control Platform - Install
echo =====================================
echo.

echo [1/6] Checking Python environment...

if exist "D:\Anaconda3\Scripts\conda.exe" set "CONDA_EXE=D:\Anaconda3\Scripts\conda.exe"
if not defined CONDA_EXE (
    where conda >nul 2>&1
    if !errorlevel! equ 0 set "CONDA_EXE=conda"
)

if defined CONDA_EXE (
    set "CONDA_NO_PLUGINS=true"
    echo Conda detected. Using local Python 3.11 environment:
    echo    %ENV_DIR%
    if not exist "%ENV_DIR%\python.exe" (
        echo Creating local Conda environment...
        call "%CONDA_EXE%" create --solver classic -p "%ENV_DIR%" python=3.11 -y
        if !errorlevel! neq 0 (
            echo Failed to create Conda environment.
            pause
            exit /b 1
        )
    )
    set "PYTHON_CMD=%CONDA_EXE% run -p %ENV_DIR% python"
    call "%CONDA_EXE%" run -p "%ENV_DIR%" python --version
) else (
    echo Conda was not found. Trying system Python...
    python --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo Python was not found. Please install Python 3.10 or 3.11.
        pause
        exit /b 1
    )

    for /f "usebackq tokens=*" %%V in (`python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"`) do set "PY_VER=%%V"
    if not "!PY_VER!"=="3.10" if not "!PY_VER!"=="3.11" (
        echo Current Python version is !PY_VER!.
        echo This project should use Python 3.10 or 3.11.
        echo Python 3.13 makes old pandas/numpy/tensorflow packages build from source and fail.
        echo Install Conda, or switch to Python 3.10/3.11, then retry.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
    python --version
)

echo.
echo [2/6] Installing Python dependencies...
echo Upgrading pip...
%PYTHON_CMD% -m pip install --upgrade pip
if !errorlevel! neq 0 (
    echo Pip upgrade failed. Continuing with dependency install...
)

echo Installing packages from requirements.txt...
%PYTHON_CMD% -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo Python dependency installation failed.
    echo You can retry with a mirror:
    echo    %PYTHON_CMD% -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
    pause
    exit /b 1
)
echo Python dependencies installed.

echo.
echo [3/6] Checking Node.js environment...
where node >nul 2>&1
if !errorlevel! neq 0 (
    echo Node.js was not found. Please install Node.js 16+.
    pause
    exit /b 1
)
node --version
call npm --version

echo.
echo [4/6] Installing frontend dependencies...
if not exist "frontend\package.json" (
    echo frontend\package.json was not found.
    pause
    exit /b 1
)
pushd frontend
call npm install
if !errorlevel! neq 0 (
    popd
    echo Frontend dependency installation failed.
    echo You can retry with:
    echo    npm config set registry https://registry.npmmirror.com
    echo    npm install
    pause
    exit /b 1
)
popd
echo Frontend dependencies installed.

echo.
echo [5/6] Checking MQTT broker...
where mosquitto >nul 2>&1
if !errorlevel! equ 0 (
    echo Mosquitto is installed.
) else (
    echo Mosquitto was not found. The embedded MQTT broker can be used instead.
)

echo.
echo [6/6] Checking project files...
set "missing_files="
for %%F in (
    "backend\app.py"
    "simulator\device_simulator.py"
    "ml_models\ml_service.py"
    "mqtt_broker_embedded.py"
    "start_services.py"
) do (
    if not exist "%%F" set "missing_files=!missing_files! %%F"
)

if defined missing_files (
    echo Missing required files:!missing_files!
    pause
    exit /b 1
)

if not exist "logs" mkdir logs
if not exist "database" mkdir database

echo.
echo =====================================
echo Install finished
echo =====================================
echo.
echo Start the platform with:
echo    %PYTHON_CMD% start_services.py
echo.
pause
exit /b 0
