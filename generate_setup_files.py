import os, stat, textwrap

ROOT = os.path.dirname(os.path.abspath(__file__))

requirements = textwrap.dedent("""\
streamlit
pandas
openpyxl
xlsxwriter
fpdf2
""")

setup_script = textwrap.dedent("""\
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
""")

launch_script = textwrap.dedent("""\
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.venv/bin/activate"
streamlit run "$SCRIPT_DIR/app.py"
exec "$SHELL"
""")

with open(os.path.join(ROOT, "requirements.txt"), "w") as f:
    f.write(requirements)

with open(os.path.join(ROOT, "Setup (primera vez).command"), "w") as f:
    f.write(setup_script)

with open(os.path.join(ROOT, "Abrir la app.command"), "w") as f:
    f.write(launch_script)

for file in ["Setup (primera vez).command", "Abrir la app.command"]:
    path = os.path.join(ROOT, file)
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

print("Archivos de configuración creados.")
