#!/bin/bash
# Build all MathTrainer versions for Linux
# Run from project root: ./build/build_linux.sh

cd "$(dirname "$0")/.."

for lang in EN DE FR ES; do
    src=$(echo "src/multiply_trainer_${lang}.py" | tr '[:upper:]' '[:lower:]')
    # DE, FR, ES files are lowercase in name
    case $lang in
        EN) src="src/multiply_trainer_EN.py" ;;
        DE) src="src/multiply_trainer_de.py" ;;
        FR) src="src/multiply_trainer_fr.py" ;;
        ES) src="src/multiply_trainer_es.py" ;;
    esac
    echo "Building MathTrainer_$lang..."
    pyinstaller --noconfirm --onefile --noconsole \
        --name "MathTrainer_$lang" \
        --clean \
        "$src"
done

echo ""
echo "Build complete! Executables in dist/:"
ls -1 dist/MathTrainer_*
