@echo off
echo ???  Installing Maker Tool v7.7.0...
echo -----------------------------------

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ? Error: Python is not installed or not in PATH.
    pause
    exit /b
)

:: Install the tool in editable mode
echo ?? Running pip install...
pip install -e .

if %errorlevel% eq 0 (
    echo.
    echo ? SUCCESS! Maker Tool is installed.
    echo ?? Restart your CMD and type 'maker --help' to begin.
) else (
    echo ? Installation failed. Check the errors above.
)

pause