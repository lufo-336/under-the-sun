#!/usr/bin/env bash
# Rigenera la mappa in out/index/ (da lanciare dopo ogni modifica ad architettura.d2).
set -euo pipefail
cd "$(dirname "$0")"

SFONDO="#0B1220"   # uguale a N7 in architettura.d2
# Dimensione di partenza nel browser. Le pagine sono larghe al massimo ~1860 px:
# con 0.85 entrano in uno schermo 1600x900; con uno schermo largo 1920 si può
# lanciare SCALA=1 ./compila.sh. Una scala fissa (e non "adatta alla finestra")
# lascia funzionare Ctrl + / Ctrl - del browser.
SCALA="${SCALA:-0.85}"

d2 --scale "$SCALA" architettura.d2 out/index.svg

# D2 colora solo il disegno: fuori dal disegno Firefox mostrerebbe il bianco.
# Uno sfondo sull'<svg> radice colora tutta la finestra.
sed -i "1s|<svg xmlns=|<svg style=\"background:${SFONDO}\" xmlns=|" out/index/*.svg

# D2 svuota out/index/ a ogni giro: index.html va ricreato qui.
# Serve per il doppio clic: su Fedora un .svg si apre nel visualizzatore immagini, un .html nel browser.
cat > out/index/index.html <<HTML
<!doctype html>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=index.svg">
<title>UnderTheSun · architettura</title>
<style>html { background: ${SFONDO}; }</style>
<a href="index.svg" style="color:#93C5FD">Apri la mappa</a>
HTML
