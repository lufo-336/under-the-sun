# Mappa interattiva dell'architettura (D2)

Mappa cliccabile dell'architettura di **UnderTheSun**, scritta in [D2](https://d2lang.com/) (`architettura.d2`) ed esportata in SVG navigabili (`out/index/`). Mostra lo stato fino allo **Sprint 1**: cosa è fatto, cosa è in revisione, cosa manca.

## 1. Aprire la mappa (senza installare nulla)

1. Apri la cartella `out/index/`.
2. Doppio clic su **`index.html`**: si apre nel browser e porta subito alla mappa (`index.svg`).

> Evita il doppio clic diretto su `index.svg`: su Fedora (e a volte su Windows) apre il visualizzatore di immagini, dove i riquadri non sono cliccabili. In alternativa trascina `index.svg` in una scheda del browser.

### Pagine

| File | Contenuto |
|---|---|
| `index.svg` | vista generale: calendario, legenda, architettura, le 6 scelte di fondo |
| `database.svg` | le 14 tabelle (colorate per chi le scrive), avvio in Compose, SQL reale |
| `backend.svg` | percorso di una richiesta in Express, endpoint fatti e da fare, codice |
| `flusso_llm.svg` | sequenza di una segnalazione con il caso "LLM non risponde" |
| `frontend.svg` | struttura React, mock di oggi e API dello Sprint 1, codice |
| `dati.svg` | pipeline Python, le due configurazioni, formula della ripartizione |
| `devops.svg` | giro di una modifica, i 3 job della CI, ordine di merge |
| `sprint1.svg` | le 10 Issue dello Sprint 1, chi le fa e cosa aspetta cosa |
| `storico.svg` | storico del repository GitHub: PR unite, aperte, chiuse e review principali |

### Come navigarla
- **Clic** su un riquadro con l'icona del link: apre la pagina di dettaglio o la PR/Issue su GitHub.
- **Mouse sopra** i riquadri con la "i": nota veloce.
- **← Vista generale** (o il tasto Indietro) per tornare.
- Le pagine sono fatte per entrare in larghezza in uno schermo 1600×900 e si scorrono in verticale; **Ctrl +** e **Ctrl −** funzionano come su un sito normale.

Il tema è scuro in qualunque browser: lo sfondo è scritto dentro gli SVG, non dipende dalle impostazioni del browser.

## 2. Modificare e ricompilare

### Installare D2
- **Linux / macOS:** `curl -fsSL https://d2lang.com/install.sh | sh -s --`
- **Windows:** `winget install Terrastruct.D2`

Verifica: `d2 --version` (la mappa è fatta con la v0.9.0).

### Ricompilare dopo una modifica

```bash
./compila.sh
```

Lo script (serve `bash`: su Windows va bene Git Bash):
1. lancia `d2 --scale 0.85 architettura.d2 out/index.svg`: una scala fissa (non "adatta alla finestra"), così lo zoom del browser funziona. Con uno schermo largo 1920 si può usare `SCALA=1 ./compila.sh`;
2. mette lo sfondo scuro anche sull'`<svg>` principale, altrimenti Firefox mostra il bianco fuori dal disegno;
3. ricrea `out/index/index.html`, perché D2 svuota `out/index/` a ogni compilazione.

Per la compilazione serve la rete: le icone (React, PostgreSQL, Python, Docker) vengono scaricate e incluse negli SVG.

### Anteprima live mentre scrivi

```bash
d2 --watch architettura.d2 out/index.svg
```

L'anteprima del browser non ha lo sfondo scuro fuori dal disegno: alla fine lancia comunque `./compila.sh`.

### Regole
- Dopo ogni modifica a `architettura.d2` ricompila con `./compila.sh` prima del commit, così sorgente e SVG restano allineati.
- Le convenzioni (classi di stato, colori) e le trappole di D2 già incontrate sono in testa ad `architettura.d2`.
