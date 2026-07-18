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

## Downloads

Grab the latest release from [Releases](../../releases):

| Platform | File | Description |
|----------|------|-------------|
| Windows | `MathTrainer_EN.exe` | Standalone executable (English) |
| Windows | `MathTrainer_DE.exe` | Standalone executable (German) |
| Windows | `MathTrainer_FR.exe` | Standalone executable (French) |
| Windows | `MathTrainer_ES.exe` | Standalone executable (Spanish) |
| Linux | `MathTrainer_EN` | Standalone ELF binary (English, built on Arch/CachyOS) |
| Linux | `MathTrainer_DE` | Standalone ELF binary (German) |
| Linux | `MathTrainer_FR` | Standalone ELF binary (French) |
| Linux | `MathTrainer_ES` | Standalone ELF binary (Spanish) |

## Running from Source

Requires Python 3.8+ (tkinter included by default).

### Available Languages

| Command | Language |
|---------|----------|
| `python multiply_trainer_EN.py` | English |
| `python multiply_trainer_DE.py` | German |
| `python multiply_trainer_FR.py` | French |
| `python multiply_trainer_ES.py` | Spanish |

## Building

### Windows
```bat
.\build_windows.bat
```

### Linux
```bash
./build_linux.sh
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
- Renamed source files with language suffixes (_EN, _DE, _FR, _ES)

### v1.0
- Initial release with 1-digit, 2-digit, and 4-digit modes
- Five operations, light/dark themes, competitive stats dashboard

## License

MIT
