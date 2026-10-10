@echo off
echo ========================================
echo   AI Pet Build Script
echo ========================================
echo.

echo [1/3] Installing PyInstaller...
pip install pyinstaller -i https://pypi.tuna.tsinghua.edu.cn/simple

echo.
echo [2/3] Building...
pyinstaller --noconfirm --onedir --windowed --name "AI_Pet" ^
    --paths "." ^
    --hidden-import "pets" ^
    --hidden-import "config" ^
    --hidden-import "settings" ^
    --hidden-import "pet_selector" ^
    --hidden-import "features" ^
    --hidden-import "games" ^
    --hidden-import "pet" ^
    --hidden-import "ui" ^
    main.py

echo.
echo [3/3] Done!
echo Output: dist\AI_Pet\AI_Pet.exe
echo.
pause
