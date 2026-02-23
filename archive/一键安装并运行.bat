@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ============================================================
echo    复杂网络农户采纳行为模型 - 一键安装并运行
echo ============================================================
echo.
echo 当前目录: %CD%
echo.

REM ============================================================
REM 步骤1: 检查Python环境
REM ============================================================
echo [步骤 1/5] 检查Python环境...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python！
    echo.
    echo 请先安装Python 3.8或更高版本：
    echo https://www.python.org/downloads/
    echo.
    echo 安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

python --version
echo [OK] Python环境检查通过
echo.

REM ============================================================
REM 步骤2: 检查pip
REM ============================================================
echo [步骤 2/5] 检查pip...
echo.

python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo [错误] pip未安装或不可用
    echo.
    pause
    exit /b 1
)

echo [OK] pip检查通过
echo.

REM ============================================================
REM 步骤3: 安装依赖
REM ============================================================
echo [步骤 3/5] 安装依赖包...
echo.
echo 这可能需要5-10分钟，请耐心等待...
echo 如果下载慢，可以使用国内镜像（见运行指南）
echo.

python -m pip install -r requirements.txt --quiet --upgrade
if errorlevel 1 (
    echo.
    echo [警告] 部分依赖安装可能失败，尝试使用国内镜像...
    python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --upgrade
    if errorlevel 1 (
        echo.
        echo [错误] 依赖安装失败！
        echo 请检查网络连接，或手动运行：
        echo   pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

echo.
echo [OK] 依赖安装完成
echo.

REM ============================================================
REM 步骤4: 验证环境
REM ============================================================
echo [步骤 4/5] 验证环境...
echo.

if exist test_environment.py (
    python test_environment.py
    if errorlevel 1 (
        echo.
        echo [警告] 环境验证失败，但将继续运行...
        echo.
    ) else (
        echo [OK] 环境验证通过
        echo.
    )
) else (
    echo [跳过] 未找到test_environment.py，跳过验证
    echo.
)

REM ============================================================
REM 步骤5: 运行完整实验
REM ============================================================
echo [步骤 5/5] 运行完整实验...
echo.
echo ============================================================
echo 重要提示：
echo   - 这将运行200轮训练
echo   - 预计需要30-60分钟
echo   - 请保持电脑运行，不要关闭命令行窗口
echo ============================================================
echo.
echo 按任意键开始运行，或按Ctrl+C取消...
pause >nul
echo.

REM 检查是否存在run_complete_experiment.py
if exist run_complete_experiment.py (
    echo 运行完整实验脚本...
    python run_complete_experiment.py
) else if exist run_experiment.py (
    echo 运行实验脚本...
    python run_experiment.py
) else (
    echo [错误] 未找到运行脚本！
    echo 请确保以下文件存在：
    echo   - run_complete_experiment.py
    echo   或
    echo   - run_experiment.py
    echo.
    pause
    exit /b 1
)

if errorlevel 1 (
    echo.
    echo [错误] 实验运行失败！
    echo 请查看上方的错误信息
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo 实验运行完成！
echo ============================================================
echo.

REM ============================================================
REM 检查结果文件
REM ============================================================
echo 检查生成的结果...
echo.

set "HAS_FIGURES=0"
if exist "figures\phase_transition.png" set "HAS_FIGURES=1"
if exist "figures\diffusion_time.png" set "HAS_FIGURES=1"
if exist "figures\training_curves.png" set "HAS_FIGURES=1"

if !HAS_FIGURES!==1 (
    echo [OK] 图表已生成在 figures\ 文件夹
) else (
    echo [警告] 未找到图表文件，可能生成失败
)

set "HAS_RESULTS=0"
if exist "results\baseline_history.csv" set "HAS_RESULTS=1"
if exist "results\rl_training_history.csv" set "HAS_RESULTS=1"

if !HAS_RESULTS!==1 (
    echo [OK] 数据已生成在 results\ 文件夹
) else (
    echo [警告] 未找到结果数据文件
)

echo.
echo ============================================================
echo 运行完成！
echo ============================================================
echo.
echo 结果位置：
echo   - 图表: figures\ 文件夹
echo   - 数据: results\ 文件夹
echo   - 模型: models\ 文件夹
echo.
echo 是否打开结果文件夹？(Y/N)
set /p OPEN_FOLDER=

if /i "!OPEN_FOLDER!"=="Y" (
    if exist figures start explorer figures
    if exist results start explorer results
)

echo.
echo 按任意键退出...
pause >nul

