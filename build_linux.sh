#!/bin/bash
# Build MathTrainer for Linux
# Requires: pip install pyinstaller

pyinstaller --noconfirm --onefile --noconsole \
    --name MathTrainer \
    --clean \
    multiply_trainer.py

echo ""
echo "Build complete: dist/MathTrainer"
