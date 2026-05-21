@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo =====================================
echo 🧹 工业现场管控平台 - 依赖清理脚本
echo =====================================
echo.

REM 获取当前脚本目录
set "SCRIPT_DIR=%~dp0"

echo [1/8] 🗑️ 清理Python缓存文件...
echo 正在删除 __pycache__ 目录...
for /d /r "%SCRIPT_DIR%" %%d in (__pycache__) do (
    if exist "%%d" (
        echo   删除: %%d
        rmdir /s /q "%%d" 2>nul
    )
)

echo 正在删除 .pyc 文件...
for /r "%SCRIPT_DIR%" %%f in (*.pyc) do (
    if exist "%%f" (
        echo   删除: %%f
        del /q "%%f" 2>nul
    )
)

echo 正在删除 .pyo 文件...
for /r "%SCRIPT_DIR%" %%f in (*.pyo) do (
    if exist "%%f" (
        echo   删除: %%f
        del /q "%%f" 2>nul
    )
)

echo ✅ Python缓存清理完成

echo.
echo [2/8] 📦 清理前端依赖...
if exist "%SCRIPT_DIR%frontend\node_modules" (
    echo 正在删除 node_modules 目录...
    rmdir /s /q "%SCRIPT_DIR%frontend\node_modules" 2>nul
    echo ✅ node_modules 删除完成
) else (
    echo ⚠️ node_modules 目录不存在
)

if exist "%SCRIPT_DIR%frontend\package-lock.json" (
    echo 正在删除 package-lock.json...
    del /q "%SCRIPT_DIR%frontend\package-lock.json" 2>nul
    echo ✅ package-lock.json 删除完成
) else (
    echo ⚠️ package-lock.json 文件不存在
)

if exist "%SCRIPT_DIR%frontend\dist" (
    echo 正在删除 dist 构建目录...
    rmdir /s /q "%SCRIPT_DIR%frontend\dist" 2>nul
    echo ✅ dist 目录删除完成
) else (
    echo ⚠️ dist 目录不存在
)

echo.
echo [3/8] 🗂️ 清理日志文件...
if exist "%SCRIPT_DIR%logs" (
    echo 正在清理日志文件...
    for %%f in ("%SCRIPT_DIR%logs\*.log") do (
        echo   删除: %%f
        del /q "%%f" 2>nul
    )
    echo ✅ 日志文件清理完成
) else (
    echo ⚠️ logs 目录不存在
)

echo.
echo [4/8] 💾 清理数据库文件...
if exist "%SCRIPT_DIR%database\industrial.db" (
    echo 正在删除数据库文件...
    del /q "%SCRIPT_DIR%database\industrial.db" 2>nul
    echo ✅ 数据库文件删除完成
) else (
    echo ⚠️ 数据库文件不存在
)

if exist "%SCRIPT_DIR%database\*.db-journal" (
    echo 正在删除数据库日志文件...
    del /q "%SCRIPT_DIR%database\*.db-journal" 2>nul
    echo ✅ 数据库日志文件删除完成
)

echo.
echo [5/8] 🤖 清理机器学习模型文件...
if exist "%SCRIPT_DIR%ml_models\*.pkl" (
    echo 正在删除模型文件...
    for %%f in ("%SCRIPT_DIR%ml_models\*.pkl") do (
        echo   删除: %%f
        del /q "%%f" 2>nul
    )
    echo ✅ 模型文件删除完成
) else (
    echo ⚠️ 没有找到模型文件
)

if exist "%SCRIPT_DIR%ml_models\*.h5" (
    echo 正在删除 TensorFlow 模型文件...
    del /q "%SCRIPT_DIR%ml_models\*.h5" 2>nul
)

if exist "%SCRIPT_DIR%ml_models\*.joblib" (
    echo 正在删除 joblib 模型文件...
    del /q "%SCRIPT_DIR%ml_models\*.joblib" 2>nul
)

echo.
echo [6/8] 📡 清理MQTT数据...
if exist "%SCRIPT_DIR%mosquitto_data" (
    echo 正在清理 Mosquitto 数据...
    rmdir /s /q "%SCRIPT_DIR%mosquitto_data" 2>nul
    echo ✅ Mosquitto 数据清理完成
) else (
    echo ⚠️ mosquitto_data 目录不存在
)

echo.
echo [7/8] 🔧 清理临时文件...
echo 正在删除临时文件...

REM 删除各种临时文件
for %%ext in (*.tmp *.temp *.bak *.swp *.swo) do (
    for /r "%SCRIPT_DIR%" %%f in (%%ext) do (
        if exist "%%f" (
            echo   删除: %%f
            del /q "%%f" 2>nul
        )
    )
)

REM 删除编辑器临时文件
for /r "%SCRIPT_DIR%" %%f in (.DS_Store Thumbs.db desktop.ini) do (
    if exist "%%f" (
        echo   删除: %%f
        del /q "%%f" 2>nul
    )
)

echo ✅ 临时文件清理完成

echo.
echo [8/8] 🔍 清理空目录...
echo 正在检查并删除空目录...

REM 删除可能的空目录
for /d %%d in ("%SCRIPT_DIR%frontend\.vite" "%SCRIPT_DIR%frontend\.temp" "%SCRIPT_DIR%.pytest_cache" "%SCRIPT_DIR%.coverage") do (
    if exist "%%d" (
        echo   删除空目录: %%d
        rmdir /s /q "%%d" 2>nul
    )
)

echo ✅ 空目录清理完成

echo.
echo =====================================
echo 🎉 依赖清理完成！
echo =====================================
echo.
echo 📊 清理摘要:
echo    ✅ Python缓存文件: 已清理
echo    ✅ 前端依赖文件: 已清理
echo    ✅ 日志文件: 已清理
echo    ✅ 数据库文件: 已清理
echo    ✅ 机器学习模型: 已清理
echo    ✅ MQTT数据: 已清理
echo    ✅ 临时文件: 已清理
echo    ✅ 空目录: 已清理
echo.
echo 💡 清理后的操作建议:
echo    1. 重新运行: install_dependencies.bat
echo    2. 重新初始化数据库: python database/init_db.py
echo    3. 重新训练机器学习模型(如需要)
echo.
echo ⚠️ 注意: 以下文件未被删除
echo    • 源代码文件(.py, .js, .vue等)
echo    • 配置文件(.json, .conf等)
echo    • 安装包文件(所需安装/目录下)
echo    • README和文档文件
echo.
pause
