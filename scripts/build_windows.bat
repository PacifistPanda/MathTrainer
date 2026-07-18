@echo off
REM Build all MathTrainer versions for Windows
REM Run from project root: build\build_windows.bat

cd /d "%~dp0\.."

pyinstaller --noconfirm --onefile --noconsole --icon assets\math_icon.ico --name MathTrainer_EN --clean src\multiply_trainer_EN.py
pyinstaller --noconfirm --onefile --noconsole --icon assets\math_icon.ico --name MathTrainer_DE --clean src\multiply_trainer_de.py
pyinstaller --noconfirm --onefile --noconsole --icon assets\math_icon.ico --name MathTrainer_FR --clean src\multiply_trainer_fr.py
pyinstaller --noconfirm --onefile --noconsole --icon assets\math_icon.ico --name MathTrainer_ES --clean src\multiply_trainer_es.py

echo.
echo Build complete! Executables in dist\:
echo   MathTrainer_EN.exe   (English)
echo   MathTrainer_DE.exe   (German)
echo   MathTrainer_FR.exe   (French)
echo   MathTrainer_ES.exe   (Spanish)
pause
