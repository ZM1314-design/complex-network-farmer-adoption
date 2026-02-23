@echo off
chcp 65001 >nul
echo ============================================================
echo 环境检查工具
echo ============================================================
echo.

echo 正在运行环境检查脚本...
echo.

python test_environment.py

if %errorlevel% neq 0 (
    echo.
    echo 环境检查遇到问题，请查看上面的输出信息
    pause
    exit /b 1
)

echo.

echo [2/3] 检查pip是否可用...
pip --version
if %errorlevel% neq 0 (
    echo ✗ pip不可用
    echo.
    pause
    exit /b 1
) else (
    echo ✓ pip可用
)
echo.

echo [3/3] 检查关键依赖包...
echo 检查numpy...
python -c "import numpy" 2>nul
if %errorlevel% neq 0 (
    echo ✗ numpy未安装
    echo.
    echo 需要安装依赖包！
    echo 请运行：install_dependencies.bat
    echo.
    pause
    exit /b 1
) else (
    echo ✓ numpy已安装
)

echo 检查torch...
python -c "import torch" 2>nul
if %errorlevel% neq 0 (
    echo ✗ torch未安装
    echo.
    echo 需要安装依赖包！
    echo 请运行：install_dependencies.bat
    echo.
    pause
    exit /b 1
) else (
    echo ✓ torch已安装
)

echo 检查networkx...
python -c "import networkx" 2>nul
if %errorlevel% neq 0 (
    echo ✗ networkx未安装
    echo.
    echo 需要安装依赖包！
    echo 请运行：install_dependencies.bat
    echo.
    pause
    exit /b 1
) else (
    echo ✓ networkx已安装
)

echo.
echo ============================================================
echo ✓ 环境检查通过！所有依赖都已安装！
echo ============================================================
echo.
echo 可以继续运行：
echo   - run_quick_test.bat（快速测试）
echo   - run_full_experiment.bat（完整实验）
echo.
echo 按任意键退出...
pause >nul

