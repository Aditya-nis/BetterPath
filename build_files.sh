#!/bin/bash
set -e

echo "Setting up output directory..."
mkdir -p staticfiles

echo "Installing Python dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv to install dependencies..."
    uv pip install --system -r requirements.txt || uv pip install -r requirements.txt
else
    echo "Using pip with --break-system-packages..."
    python3 -m pip install -r requirements.txt --break-system-packages || python3 -m pip install -r requirements.txt
fi

echo "Collecting static assets..."
python3 manage.py collectstatic --noinput --clear

echo "Vercel build completed successfully!"
