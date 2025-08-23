@echo off
echo Building DeDupe executable...
echo.

REM Clean previous builds
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

REM Build the executable
python -m PyInstaller --clean DeDupe.spec

echo.
echo Build completed!
echo.
echo The executable is located in the 'dist' folder.
echo You can run 'DeDupe.exe' from there.
echo.
pause
