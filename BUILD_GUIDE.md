# Math Trainer - Windows Build Guide

## Quick Start

1. Install Python from https://www.python.org/downloads/
   - Check **"Add Python to PATH"** during install

2. Open PowerShell and run:
   ```
   pip install pyinstaller
   ```

3. Navigate to this folder:
   ```
   cd D:\MathTrainer
   ```

4. Build all versions:
   ```
   scripts\build_windows.bat
   ```

5. Executables will be at `dist\`

## Running Without Building

```bash
cd src
python multiply_trainer_EN.py   # English
python multiply_trainer_de.py   # German
python multiply_trainer_fr.py   # French
python multiply_trainer_es.py   # Spanish
```

## Build Commands (Manual)

```bat
pyinstaller --onefile --noconsole --icon=assets\math_icon.ico --name=MathTrainer_EN src\multiply_trainer_EN.py
pyinstaller --onefile --noconsole --icon=assets\math_icon.ico --name=MathTrainer_DE src\multiply_trainer_de.py
pyinstaller --onefile --noconsole --icon=assets\math_icon.ico --name=MathTrainer_FR src\multiply_trainer_fr.py
pyinstaller --onefile --noconsole --icon=assets\math_icon.ico --name=MathTrainer_ES src\multiply_trainer_es.py
```

## Project Structure

```
MathTrainer/
├── src/                        # Source files (edit these)
├── assets\math_icon.ico        # Application icon
├── scripts\build_windows.bat   # Build script
├── dist\                       # Built executables
├── .github\workflows\          # macOS CI (auto-builds on release)
├── README.md
└── BUILD_GUIDE.md              # This file
```

## Notes

- Each .exe is self-contained (~10-15MB), no Python needed on target machine
- Game data is saved to `%USERPROFILE%\.config\MathTrainer\data.json`
- macOS builds are automated via GitHub Actions
- To trigger a macOS build: create a release on GitHub, or run the workflow manually
