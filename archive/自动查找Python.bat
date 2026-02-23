@echo off
chcp 65001 >nul
echo ============================================================
echo 自动查找Python
echo ============================================================
echo.

echo 正在搜索Python安装位置...
echo.

set PYTHON_FOUND=0

REM 检查常见安装位置
set "PATHS=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python313 C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312 C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311 C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310 C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39 C:\Python313 C:\Python312 C:\Python311 C:\Python310 C:\Python39 C:\Program Files\Python313 C:\Program Files\Python312 C:\Program Files\Python311 C:\Program Files\Python310"

for %%p in (%PATHS%) do (
    if exist "%%p\python.exe" (
        echo ✓ 找到Python: %%p\python.exe
        set "PYTHON_PATH=%%p\python.exe"
        set PYTHON_FOUND=1
        
        echo.
        echo Python版本信息：
        "%%p\python.exe" --version
        
        echo.
        echo Python完整路径：
        echo %%p\python.exe
        
        echo.
        echo pip路径：
        echo %%p\Scripts\pip.exe
        
        goto :found
    )
)

:found
if %PYTHON_FOUND%==0 (
    echo ✗ 未找到Python安装
    echo.
    echo 请检查Python是否已安装
    echo 或手动查找python.exe文件位置
) else (
    echo.
    echo ============================================================
    echo 找到Python！现在可以：
    echo ============================================================
    echo.
    echo 方案1：手动添加到PATH
    echo   1. 复制上面的Python路径
    echo   2. 添加到系统环境变量PATH中
    echo   3. 重启命令行窗口
    echo.
    echo 方案2：使用完整路径运行（临时）
    echo   在下面输入命令测试：
    echo.
)

echo.
echo 按任意键退出...
pause >nul

