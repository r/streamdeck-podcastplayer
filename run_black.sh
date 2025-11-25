#!/bin/bash
# Run black code formatter on the codebase

echo "Running black code formatter..."
uv run python -m black podplayer/ tests/ *.py "$@"
echo "Done!"

