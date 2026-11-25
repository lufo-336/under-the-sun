# Mappa web interattiva dell'architettura (D2 + pagina statica)

Mappa cliccabile e animata di **UnderTheSun**: architettura, stato di ogni pezzo (fatto, in revisione, Sprint 1, Sprint 2) e **storico** di quello che è stato fatto, con date, persone, PR e commit. I diagrammi sono scritti in [D2](https://d2lang.com/); la pagina è statica, senza server e senza dipendenze esterne.

## 1. Aprirla

- **Online (GitHub Pages):** <https://lufo-336.github.io/under-the-sun/>. Si aggiorna da sola a ogni modifica di `docs/mappa/out/` su `main`.
- **In locale:** dopo `git clone` o `git pull` fai doppio clic su `docs/mappa/out/index.html`.

### Pagine

| Pagina | Contenuto |
|---|---|
| Vista generale | architettura, calendario dal kickoff al SAL finale, le 6 scelte di fondo |
| Database | le 14 tabelle, avvio in Compose, SQL reale, cosa è stato fatto |
| Backend | percorso di una richiesta in Express, i 21 endpoint del contratto e il loro stato, codice |
| Flusso LLM | sequenza di una segnalazione e cosa è già deciso o ancora da fare |
| Frontend | struttura React e stato delle PR |
| Pipeline dati | generatore Python, controlli, campione SAL 1 |
| CI & DevOps | giro di una modifica, job della CI, Pages |
| Sprint 1 | le 11 Issue (#11–#20 e #25), chi le fa, tabella di stato |
| Storico GitHub | tutte le PR dal 6 novembre, con file toccati e commit |

### Come usarla
- **Clic** su un riquadro con link: zoom verso la pagina di dettaglio, oppure apre PR/Issue su GitHub.
- **Flusso**: attiva o disattiva l'animazione lungo le frecce.
- **− / + / Adatta / Espandi** (o `Ctrl` + rotella e trascinamento): zoom e spostamento del singolo diagramma.
- **Esc**: chiude l'ingrandimento o torna alla vista generale.

## 2. Modificare e ricompilare

- Diagrammi: `d2/*.d2` (tema condiviso in `d2/tema.d2`, icone locali in `d2/icons/`).
- Testi, tabelle, codice, calendario, storico e blocchi «Già fatto»: `out/contenuti.js`.
- Stile e animazioni: `out/style.css` e `out/app.js`.

Serve D2 v0.9.0 (`brew install d2`, oppure `curl -fsSL https://d2lang.com/install.sh | sh -s --`, oppure `winget install Terrastruct.D2`). Dopo ogni modifica ai `.d2`:

```bash
cd docs/mappa
./compila.sh
```

Lo script (serve `bash`: su Windows va bene Git Bash) genera gli SVG in `out/svg/` e il file `out/svg-bundle.js`, che la pagina carica. Funziona anche offline.

### Regole
- Dopo ogni modifica ai `.d2` ricompila prima del commit, così sorgenti e SVG restano allineati.
- Nello storico scrivi le persone come `Nome (@handle)` e solo fatti verificabili su GitHub (titolo, date, stato, approvazioni, commit).
