# Math Trainer

A competitive mental arithmetic training app built with Python and tkinter.

## Features

- **Five modes:** Addition (+), Subtraction (−), Multiplication (×), Division (÷), Random (🎲)
- **Five difficulty levels:** 1-digit, 2-digit, 3-digit, 4-digit, and random (mixed per problem)
- **Configurable settings:** Time limit per problem (2–30s) and question count (0 = infinite)
- **Light/dark theme** with live switching, powered by OpenCode's color palette
- **Competitive stats:** Daily high, all-time high, vs last game, fastest/slowest game, fastest solve
- **Per-problem timing** for precision performance tracking
- **Available in:** English, German, French, Spanish
- **Cross-platform:** Windows, Linux, macOS

## Downloads

Grab the latest release from [Releases](../../releases):

| Platform | English | German | French | Spanish |
|----------|---------|--------|--------|---------|
| Windows | `MathTrainer_EN.exe` | `MathTrainer_DE.exe` | `MathTrainer_FR.exe` | `MathTrainer_ES.exe` |
| Linux | `MathTrainer_EN` | `MathTrainer_DE` | `MathTrainer_FR` | `MathTrainer_ES` |
| macOS | `MathTrainer_EN_macos` | `MathTrainer_DE_macos` | `MathTrainer_FR_macos` | `MathTrainer_ES_macos` |

## Project Structure

```
MathTrainer/
├── src/                        # Source files
│   ├── multiply_trainer_EN.py  # English
│   ├── multiply_trainer_de.py  # German
│   ├── multiply_trainer_fr.py  # French
│   └── multiply_trainer_es.py  # Spanish
├── assets/
│   └── math_icon.ico           # Application icon
├── scripts/                    # Build scripts
│   ├── build_linux.sh
│   └── build_windows.bat
├── dist/                       # Built binaries (Linux)
├── .github/workflows/
│   └── release.yml             # macOS CI builds
├── README.md
└── .gitignore
```

## Running from Source

Requires Python 3.8+ (tkinter included by default).

```bash
cd src
python multiply_trainer_EN.py   # English
python multiply_trainer_de.py   # German
python multiply_trainer_fr.py   # French
python multiply_trainer_es.py   # Spanish
```

## Building

### All platforms

```bash
# Linux
./scripts/build_linux.sh

# Windows
scripts\build_windows.bat

# macOS — automated via GitHub Actions on release
```

### Manual build (any language)

```bash
pyinstaller --onefile --noconsole --icon=assets/math_icon.ico --name=MathTrainer_EN src/multiply_trainer_EN.py
```

## Data Storage

Settings and game history are saved to `~/.config/MathTrainer/data.json`.

## Changelog

### v1.1
- Added 3-digit difficulty level
- Added random digit mode (🎲) — each problem picks 1–4 digits randomly
- Repositioned pause button to settings row with red/grey state colors
- Fixed answer entry field to accommodate all result sizes
- Added German, French, and Spanish language versions
- Added macOS builds via GitHub Actions
- Reorganized project structure

### v1.0
- Initial release with 1-digit, 2-digit, and 4-digit modes
- Five operations, light/dark themes, competitive stats dashboard

## License

MIT
