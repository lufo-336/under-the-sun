#!/usr/bin/env bash
# Compila tutti i diagrammi .d2 (motore ELK, linee a 90°) e li impacchetta in out/svg-bundle.js
# così la pagina web funziona sia su GitHub Pages sia in locale con doppio clic su out/index.html.
set -euo pipefail
cd "$(dirname "$0")"

mkdir -p out/svg

DIAGRAMMI=(
  generale
  database
  database_avvio
  backend
  flusso_llm
  frontend
  dati
  devops
  sprint1
)

for nome in "${DIAGRAMMI[@]}"; do
  d2 "d2/${nome}.d2" "out/svg/${nome}.svg"
done
chmod 644 out/svg/*.svg

python3 - <<'PY'
import json
from pathlib import Path

svg_dir = Path("out/svg")
bundle = {}
for svg_path in sorted(svg_dir.glob("*.svg")):
    bundle[svg_path.stem] = svg_path.read_text(encoding="utf-8")

out_js = Path("out/svg-bundle.js")
out_js.write_text(
    "// Generato automaticamente da compila.sh — non modificare a mano.\n"
    "window.UTS_SVGS = " + json.dumps(bundle, ensure_ascii=False) + ";\n",
    encoding="utf-8",
)
print(f"OK: {out_js} ({len(bundle)} diagrammi, {out_js.stat().st_size / 1024:.0f} KB)")
PY
