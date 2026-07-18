@echo off
REM Build MathTrainer for Windows
REM Requires: pip install pyinstaller

pyinstaller --noconfirm --onefile --noconsole ^
    --icon math_icon.ico ^
    --name MathTrainer ^
    --clean ^
    multiply_trainer.py

echo.
echo Build complete: dist\MathTrainer.exe
pause
