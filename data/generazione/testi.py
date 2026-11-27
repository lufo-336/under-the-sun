"""Testi: segnalazione, segnalazione_etichette e verbale dal sorgente fisso (guida §3.7).

Solo per il dataset completo. Un testo scritto da un LLM non si rigenera dal codice,
quindi i testi stanno in data/testi/ (su GitHub) e qui si leggono e basta:
- data/testi/segnalazioni_sorgente.csv: le segnalazioni con le etichette vere;
- data/testi/verbali/verbale_<data>.md: un verbale per assemblea.
I file sorgente non si modificano mai.

Nel campione i testi li ha scritti Francesco a mano in data/esempi/: il generatore
non li tocca.
"""

import re
from datetime import date

import numpy as np
import pandas as pd

import config

CARTELLA_TESTI = config.CARTELLA_DATA / "testi"
SORGENTE_SEGNALAZIONI = CARTELLA_TESTI / "segnalazioni_sorgente.csv"
CARTELLA_VERBALI = CARTELLA_TESTI / "verbali"
COLONNE_SORGENTE = [  # §3.7
    "ts", "socio_id", "canale", "impianto_id_indicato", "testo",
    "categoria_vera", "urgenza_vera", "impianto_id_vero", "stato", "anomalia_vera_id",
]
NOME_VERBALE = re.compile(r"verbale_(\d{4}-\d{2}-\d{2})\.md")

QUOTA_SVILUPPO = 0.30  # circa il 30% per scrivere il prompt, il resto per la misura finale (§3.7)


def rng_divisione() -> np.random.Generator:
    """Generatore per la divisione sviluppo/test: default_rng([42, 3]) (§3.7)."""
    return np.random.default_rng([config.SEED, 3])


def leggi_sorgente() -> pd.DataFrame:
    """segnalazioni_sorgente.csv come testo (le celle vuote restano vuote)."""
    s = pd.read_csv(SORGENTE_SEGNALAZIONI, dtype=str, keep_default_na=False, encoding="utf-8")
    if list(s.columns) != COLONNE_SORGENTE:
        raise ValueError(f"{SORGENTE_SEGNALAZIONI.name}: colonne {list(s.columns)}, attese {COLONNE_SORGENTE}")
    return s


def ordina(sorgente: pd.DataFrame) -> pd.DataFrame:
    """Righe in ordine di ts e id da 1 (§3.7). A parità di ts resta l'ordine del file."""
    s = sorgente.sort_values("ts", kind="stable").reset_index(drop=True)
    return s.assign(id=np.arange(1, len(s) + 1))


def dividi(categorie: pd.Series) -> pd.Series:
    """"sviluppo" o "test" per ogni riga, stratificato per categoria (§3.7).

    Per ogni categoria, in ordine alfabetico, si estraggono a caso le righe di sviluppo:
    il 30% delle righe della categoria, arrotondato all'intero più vicino (,5 per
    eccesso). Le categorie in ordine fisso e un solo generatore danno sempre la stessa
    divisione.
    """
    rng = rng_divisione()
    divisione = pd.Series("test", index=categorie.index)
    for categoria in sorted(categorie.unique()):
        righe = categorie.index[categorie == categoria].to_numpy()
        quante = int(np.floor(QUOTA_SVILUPPO * len(righe) + 0.5))
        divisione[rng.choice(righe, size=quante, replace=False)] = "sviluppo"
    return divisione


def segnalazioni(sorgente: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """segnalazione, segnalazione_etichette e segnalazione_etichette_sviluppo.

    - segnalazione: impianto_id = impianto indicato dal socio o dal monitoraggio; le
      colonne LLM e quelle in uso (categoria, urgenza) restano vuote: le riempie il
      batch di classificazione al caricamento (§3.7);
    - segnalazione_etichette: le etichette vere e il set (sviluppo o test);
    - segnalazione_etichette_sviluppo: solo le righe di sviluppo, le uniche da guardare
      mentre si scrive il prompt.
    """
    s = ordina(sorgente)
    vuota = ""
    segnalazione = pd.DataFrame({
        "id": s["id"], "socio_id": s["socio_id"], "impianto_id": s["impianto_id_indicato"], "impianto_id_llm": vuota,
        "ts": s["ts"], "canale": s["canale"], "testo": s["testo"],
        "categoria_llm": vuota, "urgenza_llm": vuota, "categoria": vuota, "urgenza": vuota, "stato": s["stato"],
    })
    etichette = pd.DataFrame({
        "segnalazione_id": s["id"], "categoria_vera": s["categoria_vera"], "urgenza_vera": s["urgenza_vera"],
        "impianto_id_vero": s["impianto_id_vero"], "set": dividi(s["categoria_vera"]),
    })
    sviluppo = etichette[etichette["set"] == "sviluppo"].reset_index(drop=True)
    return {
        "segnalazione": segnalazione[config.COLONNE["segnalazione"]],
        "segnalazione_etichette": etichette[config.COLONNE["segnalazione_etichette"]],
        "segnalazione_etichette_sviluppo": sviluppo[config.COLONNE["segnalazione_etichette_sviluppo"]],
    }


def leggi_verbale(percorso) -> str:
    """Il testo del verbale così com'è nel file, con gli a capo normalizzati a "\\n".

    Su Windows Git può consegnare i .md con gli a capo CRLF: senza questa
    normalizzazione verbale.csv cambierebbe da un computer all'altro. Si tolgono
    anche gli a capo finali, come nel verbale del campione.
    """
    testo = percorso.read_bytes().decode("utf-8")
    if testo.startswith("﻿"):
        raise ValueError(f"{percorso.name}: il file ha il BOM, va salvato in UTF-8 senza BOM")
    testo = testo.replace("\r\n", "\n").rstrip("\n")
    if "\r" in testo:
        raise ValueError(f"{percorso.name}: contiene a capo CR isolati")
    return testo


def verbali() -> pd.DataFrame:
    """Un verbale per file, in ordine di data: id da 1, data dal nome del file, sintesi vuota (§3.7)."""
    righe = []
    for percorso in sorted(CARTELLA_VERBALI.glob("*.md")):
        nome = NOME_VERBALE.fullmatch(percorso.name)
        if not nome:
            raise ValueError(f"{percorso.name}: il nome deve essere verbale_AAAA-MM-GG.md")
        data = date.fromisoformat(nome.group(1)).isoformat()  # si ferma se la data non esiste
        righe.append({"data_assemblea": data, "testo": leggi_verbale(percorso), "sintesi": ""})
    df = pd.DataFrame(righe).sort_values("data_assemblea").reset_index(drop=True)
    df["id"] = np.arange(1, len(df) + 1)
    return df[config.COLONNE["verbale"]]


def genera() -> dict[str, pd.DataFrame]:
    """Le tabelle di testo del dataset completo, rigenerate ogni volta dal sorgente."""
    return {**segnalazioni(leggi_sorgente()), "verbale": verbali()}
