@echo off
chcp 65001 >nul
echo ============================================================
echo 详细环境检查
echo ============================================================
echo.

echo [步骤1] 检查Python...
echo.
python --version
if %errorlevel% neq 0 (
    echo ✗ Python命令失败
    echo.
    echo 可能的原因：
    echo 1. Python未安装
    echo 2. Python未添加到PATH环境变量
    echo.
    echo 解决方案：
    echo - 重新安装Python，安装时勾选"Add Python to PATH"
    echo - 或使用完整路径运行Python
    echo.
) else (
    echo ✓ Python命令可用
)

echo.
echo [步骤2] 检查Python可执行文件位置...
echo.
where python
if %errorlevel% neq 0 (
    echo ✗ 找不到python.exe
) else (
    echo ✓ 找到Python可执行文件
)

echo.
echo [步骤3] 检查pip...
echo.
pip --version
if %errorlevel% neq 0 (
    echo ✗ pip命令失败
    echo 尝试使用 python -m pip...
    python -m pip --version
) else (
    echo ✓ pip命令可用
)

echo.
echo [步骤4] 运行Python环境检测脚本...
echo.
python test_environment.py
if %errorlevel% neq 0 (
    echo.
    echo ✗ Python脚本执行失败
    echo.
    echo 请检查：
    echo 1. test_environment.py 文件是否存在
    echo 2. Python是否能正常运行.py文件
    echo.
)

echo.
echo ============================================================
echo 检查完成
echo ============================================================
echo.
echo 按任意键退出...
pause >nul

