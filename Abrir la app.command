#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
streamlit run "$SCRIPT_DIR/app.py"
exec "$SHELL"
