# Math Trainer

A competitive mental arithmetic training app built with Python and tkinter.

## Features

- **Five modes:** Addition (+), Subtraction (−), Multiplication (×), Division (÷), Random (🎲)
- **Configurable difficulty:** Time limit per problem (2–30s) and question count (0 = infinite)
- **Light/dark theme** with live switching, powered by OpenCode's color palette
- **Competitive stats:** Daily high, all-time high, vs last game, fastest/slowest game, fastest solve
- **Per-problem timing** for precision performance tracking

## Downloads

Grab the latest release from [Releases](../../releases):

| Platform | File | Description |
|----------|------|-------------|
| Windows | `MathTrainer.exe` | Standalone executable, no install needed |
| Linux | `MathTrainer` | Standalone ELF binary (built on Arch/CachyOS) |

## Running from Source

Requires Python 3.8+ (tkinter included by default).

```bash
python multiply_trainer.py
```

## Building

### Windows
```bat
pyinstaller --onefile --noconsole --icon=math_icon.ico --name=MathTrainer multiply_trainer.py
```

### Linux
```bash
pyinstaller --onefile --icon=math_icon.ico --name=MathTrainer multiply_trainer.py
```

## Data Storage

Settings and game history are saved to `~/.config/MathTrainer/data.json`.

## License

MIT
