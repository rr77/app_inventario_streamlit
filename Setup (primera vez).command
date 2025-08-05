#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 no está instalado. Descárgalo en https://www.python.org/downloads/"
  exit 1
fi

python3 -m venv "$SCRIPT_DIR/.venv"
source "$SCRIPT_DIR/.venv/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

cat <<'EOF' > "$SCRIPT_DIR/Abrir la app.command"
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
streamlit run "$SCRIPT_DIR/app.py"
exec "$SHELL"
EOF

chmod +x "$SCRIPT_DIR/Abrir la app.command"

echo "Instalación completada. Usa 'Abrir la app.command' para iniciar la app a partir de ahora."
