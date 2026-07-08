@echo off
echo Building DupeClear Pro...

pyinstaller ^
  --onefile ^
  --windowed ^
  --icon=assets/icon.ico ^
  --name="DupeClearPro" ^
  --add-data="assets;assets" ^
  --hidden-import=customtkinter ^
  --hidden-import=PIL._tkinter_finder ^
  --hidden-import=xxhash ^
  --hidden-import=imagehash ^
  --hidden-import=darkdetect ^
  --hidden-import=schedule ^
  --collect-all=customtkinter ^
  main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build complete: dist\DupeClearPro.exe
) else (
    echo.
    echo Build FAILED. Check output above.
)
pause
