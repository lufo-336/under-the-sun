# Team dati UnderTheSun: istruzioni per Claude Code

Questa cartella contiene la pipeline dati di UnderTheSun, una CER simulata nel Pinerolese.
La guida completa è @GUIDA-DATASET.md: seguila sempre. Se una richiesta la contraddice, fermati e chiedi prima di procedere.
Chi lavora qui sta imparando: spiega le scelte in modo semplice e breve.

## Regole fisse

- **Python 3.11 o superiore:** ambiente virtuale in `data/.venv` (da aggiungere a `.gitignore` se manca), dipendenze in `data/requirements.txt`.
- **Seed 42** per ogni scelta casuale. Con lo stesso seed escono file identici.
- **Orari:**
  - nei CSV sempre UTC, nel formato `2026-06-01T10:00:00Z`; `ts` è l'inizio dell'ora;
  - i profili di consumo nascono in ora italiana e si convertono in UTC con pandas;
  - in Open-Meteo radiazione e neve alle hh:00 si riferiscono all'ora precedente: vanno spostate indietro di un'ora.
- **Nomi di file e colonne:** esattamente come in GUIDA-DATASET.md §4. Non aggiungere, togliere o rinominare colonne senza chiedere.
- **Cache delle fonti:** le risposte di Open-Meteo e PVGIS e i file ARERA vanno in `data/output/cache/` e si rileggono da lì. Mai scaricare due volte la stessa cosa.
- **Cosa va su Git:** il dataset completo resta in `data/output/` (escluso da Git). Su Git vanno solo script, `data/esempi/` e documentazione. Mai file oltre 50 MB, chiavi API o file `.env`.
- **Prima di dire che hai finito:** lancia i controlli e riporta l'esito.

## Comandi

- Campione SAL 1: `python generazione/genera.py --config piccola` (scrive in `data/esempi/`)
- Dataset completo: `python generazione/genera.py --config completa` (scrive in `data/output/`)
- Controlli: `python generazione/controlli.py --config piccola` (oppure `completa`)

## Git: lo gestisce Francesco, non tu

- **Chi fa le operazioni Git:** branch, commit, push e pull li fa Francesco con GitHub Desktop, dopo aver controllato i file.
- **Comandi vietati:** non eseguire mai comandi git che modificano il repo o mandano dati su GitHub, come `git add`, `commit`, `push`, `pull`, `merge`, `reset`, `checkout`, `switch` e `stash`.
- **Comandi ammessi:** solo quelli in lettura, cioè `git status`, `git diff` e `git log`.
- **Quando un pezzo di lavoro è pronto,** scrivi un riepilogo con:
  - i file creati o modificati e cosa fanno;
  - l'esito dei controlli;
  - un messaggio di commit proposto, in italiano.
- **Regole del team** (`docs/git.md`, nella radice del repo): branch con prefisso `dati/`, commit piccoli, mai lavorare su `main`.

## Come lavorare

- **Prima il piano:** per ogni lavoro nuovo proponi un piano breve e aspetta l'ok.
- **Un modulo alla volta,** in quest'ordine: anagrafiche → meteo → pvgis → produzione → consumi → derivate → controlli. Dopo ogni modulo mostra un controllo rapido: numero di righe, prime righe, un grafico se serve.
- **Dubbi sulle fonti:** se un file ARERA o una risposta API ha una forma diversa da quella attesa, mostrala e chiedi come procedere invece di indovinare.
