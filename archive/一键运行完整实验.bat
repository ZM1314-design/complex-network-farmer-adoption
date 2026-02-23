@echo off
chcp 65001 >nul

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Change to the script directory
cd /d "%SCRIPT_DIR%"

echo ============================================================
echo Starting Complete Experiment Pipeline
echo ============================================================
echo Current directory: %CD%
echo.

echo [1/4] Checking environment...
python test_environment.py
if errorlevel 1 (
    echo [ERROR] Environment check failed!
    echo Please install Python and dependencies first.
    pause
    exit /b 1
)

echo.
echo [2/4] Running full experiment...
echo This may take 30-60 minutes...
python run_experiment.py
if errorlevel 1 (
    echo [ERROR] Experiment failed!
    pause
    exit /b 1
)

echo.
echo [3/4] Generating supplementary figures...
python generate_supplementary_figures.py
if errorlevel 1 (
    echo [ERROR] Figure generation failed!
    pause
    exit /b 1
)

echo.
echo [4/4] Opening results...
start explorer figures
start explorer results

echo.
echo ============================================================
echo All tasks completed successfully!
echo ============================================================
echo.
echo Results:
echo   - 13 figures in ./figures/
echo   - Experiment data in ./results/
echo   - Trained model in ./models/
echo.
echo You can now:
echo   1. View figures in the 'figures' folder
echo   2. Check results in the 'results' folder
echo   3. Use figures in your presentation
echo.
pause

