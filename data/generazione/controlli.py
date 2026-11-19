"""Controlli di qualità (guida §6), adattati al campione SAL 1.

Uso, dalla cartella data/:
    python generazione/controlli.py --config piccola
    python generazione/controlli.py --config piccola --senza-rigenerare   (salta i due rilanci)

Ogni controllo stampa [ok] o [FALLITO]. Se anche uno solo fallisce, il programma
esce con codice 1: il dataset non si consegna (§6).

Riferimenti:
- data/data-dictionary.md: file, colonne e numero di righe del campione;
- GUIDA-DATASET.md: §2 formato, §1.3 e §3.7 valori ammessi, §3.2 e §6 regole;
- verbale.csv: i numeri e i fatti citati nel testo, confrontati con i CSV.

Adattamenti al campione (un mese invece di due anni):
- produzione: la resa del modello (kWh/kWp per kWh/m²) entro ±10% di PVGIS a giugno,
  invece del totale annuo entro ±10%;
- consumi: il totale sull'anno dei volumi provvisori (1/9/2025-31/8/2026) uguale a
  volume × scala per ogni socio, invece del confronto annuo con ARERA;
- grafici: una settimana di giugno per impianto (niente settimana invernale).
"""

import argparse
import csv
import hashlib
import io
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import anagrafiche  # noqa: E402
import config  # noqa: E402
import consumi  # noqa: E402
import produzione  # noqa: E402
import pvgis  # noqa: E402

DIZIONARIO = config.CARTELLA_DATA / "data-dictionary.md"
NOTEBOOK = config.CARTELLA_DATA / "notebook"
FUSO = "Europe/Rome"

# --- Regole del §2 ----------------------------------------------------------

ISTANTI = {"ts", "inizio", "fine"}
DATE = {"data_adesione", "data_attivazione", "mese", "data_assemblea"}
DECIMALI = {  # numero massimo di decimali (§2)
    **dict.fromkeys(["kwh", "kwh_previsti", "kwh_condivisi", "co2_evitata_kg"], 3),
    **dict.fromkeys(["importo_eur", "incentivo_eur"], 2),
    **dict.fromkeys(["irraggiamento_wm2", "irraggiamento_pannelli_wm2", "temperatura_c", "nuvolosita_pct", "neve_cm"], 1),
}
SERIE_ORARIE = {"meteo_orario", "produzione_oraria", "consumo_orario", "previsione_produzione",
                "previsione_consumo", "anomalia", "anomalie_vere"}  # istanti a ora piena
VALORI_VIETATI = {"nan", "none", "null", "-", "n/a"}
VUOTI_AMMESSI = {  # (file, colonna) in cui una cella vuota ha un significato
    ("segnalazione", "socio_id"), ("segnalazione", "impianto_id"), ("segnalazione", "impianto_id_llm"),
    ("anomalia", "fine"), ("anomalia", "tipo"), ("verbale", "sintesi"), ("socio_profilo", "ateco"),
}

# --- Valori ammessi (§1.3, §3.3, §3.5, §3.7, data dictionary) -----------------

TIPI_SOCIO = {"famiglia", "impresa", "ente"}
PROFILI = {"famiglia": "famiglia",
           **{profilo: "impresa" for profilo, *_ in anagrafiche.IMPRESE},
           **{profilo: "ente" for profilo, *_ in anagrafiche.ENTI}}
COMUNI = set(anagrafiche.ABITANTI)
CANALI = {"email", "portale", "interno"}
CATEGORIE = {"guasto_impianto", "bolletta_pagamenti", "incentivi_ripartizione", "adesione_recesso", "informazioni", "reclamo"}
URGENZE = {"alta", "media", "bassa"}
STATI_SEGNALAZIONE = {"aperta", "in_corso", "chiusa"}
TIPI_ANOMALIA = {"guasto", "stringa", "sporcizia", "neve"}
STATI_ANOMALIA = {"aperta", "chiusa"}
CHIAVI_PARAMETRO = {chiave for chiave, *_ in anagrafiche.PARAMETRI}

ESITI: list[tuple[str, bool]] = []


def controlla(nome: str, ok, dettaglio: str = "") -> None:
    ESITI.append((nome, bool(ok)))
    print(f"  [{'ok' if ok else 'FALLITO'}] {nome}" + (f": {dettaglio}" if dettaglio else ""))


def sezione(titolo: str) -> None:
    print(f"\n=== {titolo} ===")


def num(df: pd.DataFrame, colonna: str) -> pd.Series:
    return pd.to_numeric(df[colonna])


def italiano(n: float, decimali: int = 0) -> str:
    """66332 -> "66.332"; 34.6 -> "34,6"."""
    testo = f"{n:,.{decimali}f}"
    return testo.replace(",", "_").replace(".", ",").replace("_", ".")


# --- Data dictionary --------------------------------------------------------


def leggi_dizionario(percorso: Path) -> dict[str, dict]:
    """{file: {"colonne": [...], "righe": n}} letti da data-dictionary.md.

    - schede "### nome.csv (N righe ...)" con la prima tabella "| Colonna | ...";
    - tabella delle tabelle calcolate: "| `nome.csv` | N | `col`, `col` | ...";
    - "righe" è None per i file che non sono nel campione.
    """
    righe = percorso.read_text(encoding="utf-8").splitlines()
    voci = {}
    for i, riga in enumerate(righe):
        scheda = re.match(r"^### (\w+)\.csv[^(]*\(([^)]*)\)", riga)
        if scheda:
            quante = re.match(r"([\d.]+) rig(?:a|he)\b", scheda.group(2))  # "1 riga", "14.400 righe"
            voce = {"righe": int(quante.group(1).replace(".", "")) if quante else None, "colonne": None}
            for j in range(i + 1, len(righe)):
                if righe[j].startswith("#"):
                    break
                if righe[j].startswith("| Colonna"):
                    colonne = []
                    for k in range(j + 2, len(righe)):
                        if not righe[k].startswith("|"):
                            break
                        colonne += [c.strip(" `") for c in righe[k].split("|")[1].split(",")]
                    voce["colonne"] = colonne
                    break
            voci[scheda.group(1)] = voce
        calcolata = re.match(r"^\| `(\w+)\.csv` \| ([\d.]+) \| (.+?) \|", riga)
        if calcolata:
            voci[calcolata.group(1)] = {
                "righe": int(calcolata.group(2).replace(".", "")),
                "colonne": [c.strip(" `") for c in calcolata.group(3).split(",")],
            }
    return voci


# --- Sezioni dei controlli ----------------------------------------------------


def hash_esempi(cartella: Path) -> dict[str, str]:
    return {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(cartella.glob("*.csv"))}


def riproducibilita(nome_config: str, cartella: Path) -> None:
    sezione("Riproducibilità: due rilanci di genera.py")
    prima = hash_esempi(cartella)
    rilanci = []
    for _ in range(2):
        subprocess.run([sys.executable, str(Path(__file__).with_name("genera.py")), "--config", nome_config],
                       cwd=config.CARTELLA_DATA, check=True, capture_output=True)
        rilanci.append(hash_esempi(cartella))
    controlla("i due rilanci producono file identici", rilanci[0] == rilanci[1], f"{len(rilanci[1])} file confrontati")
    cambiati = sorted(n for n in rilanci[0] if prima.get(n) != rilanci[0][n])
    controlla("i file di esempi/ erano già uguali a quelli rigenerati", not cambiati, ", ".join(cambiati))


def dizionario_e_righe(T: dict[str, pd.DataFrame]) -> None:
    sezione("File, intestazioni e righe (data-dictionary.md)")
    voci = leggi_dizionario(DIZIONARIO)
    attesi = {n for n, v in voci.items() if v["righe"] is not None}
    presenti = set(T)
    controlla("i file di esempi/ sono quelli del data dictionary", presenti == attesi,
              f"{len(presenti)} file" if presenti == attesi else f"mancano {sorted(attesi - presenti)}, in più {sorted(presenti - attesi)}")
    for nome in sorted(presenti & attesi):
        v, df = voci[nome], T[nome]
        problemi = []
        if list(df.columns) != v["colonne"]:
            problemi.append(f"colonne {list(df.columns)}, nel dizionario {v['colonne']}")
        if len(df) != v["righe"]:
            problemi.append(f"{len(df)} righe, nel dizionario {v['righe']}")
        controlla(f"{nome}.csv: intestazioni e righe", not problemi, "; ".join(problemi) or f"{len(df)} righe")
    diversi = sorted(n for n in attesi if config.COLONNE.get(n) != voci[n]["colonne"])
    controlla("config.py usa le stesse colonne del data dictionary", not diversi, ", ".join(diversi))


def formato(cartella: Path) -> None:
    sezione("Formato dei file (§2)")
    for percorso in sorted(cartella.glob("*.csv")):
        nome, dati, problemi = percorso.stem, percorso.read_bytes(), []
        if dati.startswith(b"\xef\xbb\xbf"):
            problemi.append("BOM")
        if b"\r" in dati:
            problemi.append("fine riga CR")
        if not dati.endswith(b"\n"):
            problemi.append("manca l'a capo finale")
        try:
            righe = list(csv.reader(io.StringIO(dati.decode("utf-8"), newline="")))
        except UnicodeDecodeError:
            controlla(f"{nome}.csv", False, "non è UTF-8")
            continue
        intestazione, corpo = righe[0], righe[1:]
        if not all(re.fullmatch(r"[a-z][a-z0-9_]*", c) for c in intestazione):
            problemi.append("intestazioni non in snake_case")
        if any(len(r) != len(intestazione) for r in corpo):
            problemi.append("righe con un numero di campi diverso dall'intestazione")
        for i, colonna in enumerate(intestazione):
            valori = [r[i] for r in corpo if len(r) == len(intestazione)]
            pieni = [v for v in valori if v != ""]
            if len(pieni) < len(valori) and (nome, colonna) not in VUOTI_AMMESSI:
                problemi.append(f"{colonna}: celle vuote")
            if any(v.strip().lower() in VALORI_VIETATI for v in valori):
                problemi.append(f"{colonna}: NaN, None o '-'")
            if colonna in ISTANTI:
                forma = r"\d{4}-\d{2}-\d{2}T\d{2}:00:00Z" if nome in SERIE_ORARIE else r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
                if not all(re.fullmatch(forma, v) for v in pieni):
                    problemi.append(f"{colonna}: istanti non nel formato {'a ora piena ' if nome in SERIE_ORARIE else ''}UTC con la Z")
            if colonna in DATE:
                try:
                    giorni = [date.fromisoformat(v) for v in pieni]
                    if not all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", v) for v in pieni):
                        raise ValueError
                    if colonna == "mese" and any(g.day != 1 for g in giorni):
                        problemi.append("mese: non è il primo giorno del mese")
                except ValueError:
                    problemi.append(f"{colonna}: date non nel formato AAAA-MM-GG")
            if colonna in DECIMALI:
                if not all(re.fullmatch(r"-?\d+(\.\d+)?", v) for v in pieni):
                    problemi.append(f"{colonna}: numeri non nel formato 123.456")
                elif any(len(v.split(".")[1]) > DECIMALI[colonna] for v in pieni if "." in v):
                    problemi.append(f"{colonna}: più di {DECIMALI[colonna]} decimali")
        controlla(f"{nome}.csv", not problemi, "; ".join(problemi) or f"{len(corpo)} righe, UTF-8 senza BOM, fine riga LF")


def serie_complete(T: dict[str, pd.DataFrame], conf: dict) -> None:
    sezione("Serie orarie complete (§6)")
    attese = list(pd.date_range(conf["primo_ts"], conf["ultimo_ts"], freq="h").strftime("%Y-%m-%dT%H:%M:%SZ"))
    impianti, soci = sorted(T["impianto"]["id"]), sorted(T["socio"]["id"])
    for nome, chiave, ids in [("meteo_orario", "impianto_id", impianti), ("produzione_oraria", "impianto_id", impianti),
                              ("previsione_produzione", "impianto_id", impianti), ("consumo_orario", "socio_id", soci),
                              ("previsione_consumo", "socio_id", soci)]:
        df = T[nome]
        ok = sorted(df[chiave].unique()) == ids and all(sorted(g["ts"]) == attese for _, g in df.groupby(chiave))
        controlla(f"{nome}: {len(attese)} ore per ognuno dei {len(ids)} {chiave}, senza buchi né duplicati", ok)


def integrita(T: dict[str, pd.DataFrame]) -> None:
    sezione("ID: ogni socio_id e impianto_id esiste (§6)")
    for nome in ["impianto", "socio", "bolletta", "segnalazione", "verbale", "anomalia", "anomalie_vere"]:
        controlla(f"{nome}.id unici", T[nome]["id"].is_unique)
    soci, impianti = set(T["socio"]["id"]), set(T["impianto"]["id"])
    for nome, colonna, insieme, tabella in [
        ("socio_profilo", "socio_id", soci, "socio"), ("consumo_orario", "socio_id", soci, "socio"),
        ("previsione_consumo", "socio_id", soci, "socio"), ("bolletta", "socio_id", soci, "socio"),
        ("ripartizione_mensile", "socio_id", soci, "socio"), ("segnalazione", "socio_id", soci, "socio"),
        ("meteo_orario", "impianto_id", impianti, "impianto"), ("produzione_oraria", "impianto_id", impianti, "impianto"),
        ("previsione_produzione", "impianto_id", impianti, "impianto"), ("anomalia", "impianto_id", impianti, "impianto"),
        ("anomalie_vere", "impianto_id", impianti, "impianto"), ("segnalazione", "impianto_id", impianti, "impianto"),
        ("segnalazione", "impianto_id_llm", impianti, "impianto"),
    ]:
        mancanti = {v for v in T[nome][colonna] if v != ""} - insieme
        controlla(f"{nome}.{colonna} esiste in {tabella}", not mancanti, f"non trovati: {sorted(mancanti)}" if mancanti else "")
    controlla("socio_profilo ha una riga per ogni socio", sorted(T["socio_profilo"]["socio_id"]) == sorted(soci))


def valori_ammessi(T: dict[str, pd.DataFrame]) -> None:
    sezione("Valori ammessi")

    def ammessi(nome, colonna, insieme, vuoto=False):
        valori = set(T[nome][colonna]) - ({""} if vuoto else set())
        controlla(f"{nome}.{colonna}", valori <= insieme, f"non ammessi: {sorted(valori - insieme)}" if valori - insieme else ", ".join(sorted(valori)))

    ammessi("socio", "tipo", TIPI_SOCIO)
    ammessi("socio", "comune", COMUNI)
    ammessi("impianto", "comune", COMUNI)
    ammessi("socio_profilo", "profilo", set(PROFILI))
    sp = T["socio_profilo"].merge(T["socio"], left_on="socio_id", right_on="id")
    controlla("socio_profilo: profilo coerente con il tipo del socio", (sp["profilo"].map(PROFILI) == sp["tipo"]).all())
    controlla("socio_profilo: ATECO vuoto solo per le famiglie", ((sp["ateco"] == "") == (sp["tipo"] == "famiglia")).all())
    ammessi("parametro", "chiave", CHIAVI_PARAMETRO)
    controlla("parametro: ci sono tutte le 8 chiavi del §3.5", set(T["parametro"]["chiave"]) == CHIAVI_PARAMETRO)
    s = T["segnalazione"]
    ammessi("segnalazione", "canale", CANALI)
    for colonna in ["categoria", "categoria_llm"]:
        ammessi("segnalazione", colonna, CATEGORIE)
    for colonna in ["urgenza", "urgenza_llm"]:
        ammessi("segnalazione", colonna, URGENZE)
    ammessi("segnalazione", "stato", STATI_SEGNALAZIONE)
    controlla("segnalazione: socio_id vuoto solo per il canale interno", ((s["socio_id"] == "") == (s["canale"] == "interno")).all())
    ammessi("anomalia", "tipo", TIPI_ANOMALIA, vuoto=True)
    ammessi("anomalia", "stato", STATI_ANOMALIA)
    controlla("anomalia.score tra 0 e 1", num(T["anomalia"], "score").between(0, 1).all())
    ammessi("anomalie_vere", "tipo", TIPI_ANOMALIA)
    controlla("anomalie_vere.perdita_pct tra 0 e 100", num(T["anomalie_vere"], "perdita_pct").between(0, 100).all())
    m = T["meteo_orario"]
    controlla("meteo: irraggiamenti e neve non negativi, nuvolosità tra 0 e 100",
              (num(m, "irraggiamento_wm2") >= 0).all() and (num(m, "irraggiamento_pannelli_wm2") >= 0).all()
              and (num(m, "neve_cm") >= 0).all() and num(m, "nuvolosita_pct").between(0, 100).all())


def produzione_e_anomalie(T: dict[str, pd.DataFrame], conf: dict) -> None:
    sezione("Produzione (§3.2, §3.3, §6)")
    imp = T["impianto"].assign(id=lambda d: d["id"].astype(int), kwp=lambda d: num(d, "kwp"))
    d = (T["produzione_oraria"].merge(T["meteo_orario"], on=["impianto_id", "ts"])
         .assign(impianto_id=lambda x: x["impianto_id"].astype(int)).merge(imp[["id", "kwp"]], left_on="impianto_id", right_on="id"))
    kwh, gti, kwp = num(d, "kwh"), num(d, "irraggiamento_pannelli_wm2"), d["kwp"]
    controlla("produzione mai negativa", (kwh >= 0).all())
    controlla("produzione 0 quando irraggiamento_pannelli_wm2 è 0", (kwh[gti == 0] == 0).all(), f"{int((gti == 0).sum())} ore senza sole")
    controlla("produzione mai sopra kwp", (kwh <= kwp).all(), f"massimo {(kwh / kwp).max():.2f} kWh per kWp")

    # Produzione attesa rifatta qui con la formula del §3.2
    t_modulo = num(d, "temperatura_c") + 0.03 * gti
    k = pvgis.k_impianti(conf, anagrafiche.tabella_impianti())
    attesa = (kwp * gti / 1000 * 0.86 * (1 - 0.004 * (t_modulo - 25)) * d["impianto_id"].map(k)).clip(0, kwp)
    for a in T["anomalie_vere"].itertuples():
        dentro = (d["impianto_id"] == int(a.impianto_id)) & (d["ts"] >= a.inizio) & (d["ts"] < a.fine)
        persi = (attesa[dentro] - kwh[dentro]).sum()
        controlla(f"anomalia {a.id} ({a.tipo}, impianto {a.impianto_id}) visibile: produzione sotto l'atteso",
                  dentro.any() and (kwh[dentro] < attesa[dentro]).all(), f"{persi:.1f} kWh persi in {int(dentro.sum())} ore")
    fuori = pd.Series(True, index=d.index)
    for a in T["anomalie_vere"].itertuples():
        fuori &= ~((d["impianto_id"] == int(a.impianto_id)) & (d["ts"] >= a.inizio) & (d["ts"] < a.fine))
    controlla("fuori dalle anomalie la produzione è uguale alla formula", (kwh[fuori] - attesa[fuori].round(3)).abs().max() < 0.0015)

    # Adattamento al campione: resa di giugno contro PVGIS, a parità di irraggiamento
    righe = []
    for impianto in anagrafiche.tabella_impianti().itertuples():
        if impianto.id not in conf["impianti"]:
            continue
        giugno = next(x for x in pvgis.pvcalc(impianto)["outputs"]["monthly"]["fixed"] if x["month"] == 6)
        sel = d["impianto_id"] == impianto.id
        resa = (attesa[sel].sum() / impianto.kwp) / (gti[sel].sum() / 1000)
        resa_pvgis = (giugno["E_m"] / impianto.kwp) / giugno["H(i)_m"]
        righe.append((impianto.id, (resa / resa_pvgis - 1) * 100))
    controlla("resa del modello entro ±10% di PVGIS (giugno, kWh/kWp per kWh/m²)", all(abs(s) <= 10 for _, s in righe),
              ", ".join(f"impianto {i}: {s:+.1f}%" for i, s in righe))


def consumi_e_derivate(T: dict[str, pd.DataFrame]) -> None:
    sezione("Consumi e tabelle derivate (§3.4, §3.6, §6)")
    c = T["consumo_orario"]
    controlla("consumi mai negativi", (num(c, "kwh") >= 0).all())
    anno = {"volumi_consumo": "provvisori", "primo_ts": consumi.ANNO_VOLUMI[0], "ultimo_ts": consumi.ANNO_VOLUMI[1]}
    soci = T["socio"].merge(T["socio_profilo"], left_on="id", right_on="socio_id")
    scarti, famiglie = [], []
    for s in soci.itertuples():
        totale = consumi.consumo_socio(int(s.id), s.tipo, s.profilo, float(s.scala), anno)["kwh"].sum()
        obiettivo = consumi.VOLUMI_PROVVISORI_KWH_ANNO[s.tipo] * float(s.scala)
        scarti.append(abs(totale / obiettivo - 1))
        if s.tipo == "famiglia":
            famiglie.append(totale)
    controlla("anno 1/9/2025-31/8/2026: totale = volume provvisorio × scala per ogni socio", max(scarti) < 1e-9,
              f"famiglie in media {np.mean(famiglie):,.0f} kWh/anno (volume provvisorio 2.700 × scala media)")

    cons = c.assign(kwh=num(c, "kwh"))
    b = T["bolletta"].set_index("socio_id")
    somma = cons.groupby("socio_id")["kwh"].sum().round(3)
    controlla("bolletta.kwh = somma di consumo_orario del mese", (num(b, "kwh") - somma.reindex(b.index)).abs().max() < 0.0005)
    pp = T["previsione_produzione"].merge(T["produzione_oraria"], on=["impianto_id", "ts"])
    in_anomalia = pd.Series(False, index=pp.index)
    for a in T["anomalie_vere"].itertuples():
        in_anomalia |= (pp["impianto_id"] == a.impianto_id) & (pp["ts"] >= a.inizio) & (pp["ts"] < a.fine)
    diverse = num(pp, "kwh_previsti") != num(pp, "kwh")
    controlla("previsione_produzione = produzione, tranne nelle ore delle anomalie", not (diverse & ~in_anomalia).any() and diverse.any(),
              f"{int(diverse.sum())} ore diverse, tutte dentro le anomalie")
    prod = num(T["produzione_oraria"], "kwh").groupby(T["produzione_oraria"]["ts"]).sum()
    prel = cons.groupby("ts")["kwh"].sum()
    condivisa = np.minimum(prod.reindex(prel.index), prel).sum()
    r = T["ripartizione_mensile"]
    controlla("ripartizione: la somma delle quote è l'energia condivisa del §3.6", abs(num(r, "kwh_condivisi").sum() - condivisa) < 0.02,
              f"{num(r, 'kwh_condivisi').sum():,.1f} kWh")


def verbale(T: dict[str, pd.DataFrame], cartella: Path, conf: dict) -> None:
    sezione("verbale.csv: lettura")
    percorso = cartella / "verbale.csv"
    with open(percorso, encoding="utf-8", newline="") as f:
        righe_csv = list(csv.reader(f))
    v = pd.read_csv(percorso, dtype=str, keep_default_na=False)
    controlla("si legge con il modulo csv: intestazione più 1 riga da 4 campi", len(righe_csv) == 2 and [len(r) for r in righe_csv] == [4, 4])
    controlla("si legge con pandas: 1 riga, 4 colonne", v.shape == (1, 4))
    testo = v.loc[0, "testo"]
    controlla("il testo mantiene gli a capo, uguale con csv e con pandas", "\n" in testo and righe_csv[1][2] == testo,
              f"{testo.count(chr(10)) + 1} righe di testo, {len(testo):,} caratteri")
    controlla("id 7, assemblea del 9 luglio 2026, sintesi vuota (§7)",
              (v.loc[0, "id"], v.loc[0, "data_assemblea"], v.loc[0, "sintesi"]) == ("7", "2026-07-09", ""))

    sezione("verbale.csv: numeri e fatti citati, confrontati con i CSV")

    def cita(descrizione, frase, calcolato_ok, dettaglio):
        trovata = frase in testo
        controlla(f"{descrizione}", trovata and calcolato_ok, f"«{frase}»" + ("" if trovata else " NON TROVATA nel testo") + f"; dai CSV: {dettaglio}")

    p = T["produzione_oraria"].assign(kwh=lambda d: num(d, "kwh"))
    per_impianto = p.groupby("impianto_id")["kwh"].sum()
    totale = round(p["kwh"].sum())
    cita("produzione di giugno, totale", "66.332 kWh", totale == 66332, f"{italiano(totale)} kWh")
    for imp, frase, atteso in [("1", "9.986 kWh", 9986), ("2", "25.934 kWh", 25934), ("3", "30.413 kWh", 30413)]:
        cita(f"produzione di giugno, impianto {imp}", frase, round(per_impianto[imp]) == atteso, f"{italiano(per_impianto[imp])} kWh")

    a = T["anomalie_vere"].iloc[0]
    pp = T["previsione_produzione"].merge(T["produzione_oraria"], on=["impianto_id", "ts"])
    dentro = (pp["impianto_id"] == a["impianto_id"]) & (pp["ts"] >= a["inizio"]) & (pp["ts"] < a["fine"])
    persi = (num(pp, "kwh_previsti") - num(pp, "kwh"))[dentro].sum()
    cita("kWh persi nel guasto", "442 kWh", round(persi) == 442, f"{persi:.1f} kWh")
    inizio = pd.Timestamp(a["inizio"]).tz_convert(FUSO).strftime("%H:%M")
    fine = pd.Timestamp(a["fine"]).tz_convert(FUSO).strftime("%H:%M")
    cita("inizio del guasto in ora italiana", "alle 13:00", inizio == "13:00", f"{a['inizio']} = {inizio} ora italiana")
    cita("fine del guasto in ora italiana", "alle 17:00", fine == "17:00", f"{a['fine']} = {fine} ora italiana")

    m = T["meteo_orario"].assign(t=lambda d: pd.to_datetime(d["ts"], utc=True))
    m["giorno"] = m["t"].dt.tz_convert(FUSO).dt.day
    tmax = num(m, "temperatura_c").max()
    cita("temperatura massima", "34,6 °C", round(tmax, 1) == 34.6, f"{italiano(tmax, 1)} °C")
    p["giorno"] = pd.to_datetime(p["ts"], utc=True).dt.tz_convert(FUSO).dt.day
    giorno_max = int(p.groupby("giorno")["kwh"].sum().idxmax())
    cita("giorno di maggiore produzione (ora italiana)", "l'11 giugno", giorno_max == 11, f"{giorno_max} giugno")
    irr = num(m, "irraggiamento_wm2").groupby(m["giorno"]).sum()
    giorno_min = int(irr.idxmin())
    cita("giorno con meno irraggiamento", "con meno sole il 24 giugno", giorno_min == 24, f"{giorno_min} giugno")

    gti = num(m, "irraggiamento_pannelli_wm2").groupby(m["impianto_id"]).sum() / 1000
    h_pvgis = {}
    for impianto in anagrafiche.tabella_impianti().itertuples():
        if impianto.id in conf["impianti"]:
            h_pvgis[str(impianto.id)] = next(x for x in pvgis.pvcalc(impianto)["outputs"]["monthly"]["fixed"] if x["month"] == 6)["H(i)_m"]
    sopra = (gti.sum() / sum(h_pvgis.values()) - 1) * 100
    cita("irraggiamento sui pannelli sopra la media PVGIS di giugno", "circa il 10%", abs(sopra - 10) < 1.5,
         f"{sopra:+.1f}% (" + ", ".join(f"impianto {i}: {(gti[i] / h - 1) * 100:+.1f}%" for i, h in h_pvgis.items()) + ")")

    s = T["segnalazione"]
    canali = s["canale"].value_counts().to_dict()
    cita("segnalazioni: totale", "15 segnalazioni", len(s) == 15, f"{len(s)}")
    for frase, canale, n in [("7 dal portale", "portale", 7), ("6 via email", "email", 6), ("2 comunicazioni interne", "interno", 2)]:
        cita(f"segnalazioni: canale {canale}", frase, canali.get(canale, 0) == n, f"{canali.get(canale, 0)}")
    categorie = s["categoria"].value_counts().to_dict()
    for frase, categoria, n in [("informazioni generali (4)", "informazioni", 4), ("bollette e pagamenti (3)", "bolletta_pagamenti", 3),
                                ("guasti (3)", "guasto_impianto", 3), ("incentivi e ripartizione (2)", "incentivi_ripartizione", 2),
                                ("adesioni e recessi (2)", "adesione_recesso", 2), ("un reclamo", "reclamo", 1)]:
        cita(f"segnalazioni: categoria {categoria}", frase, categorie.get(categoria, 0) == n, f"{categorie.get(categoria, 0)} (colonna categoria)")
    stati = s["stato"].value_counts().to_dict()
    for frase, stato, n in [("8 segnalazioni risultavano chiuse", "chiusa", 8), ("4 in lavorazione", "in_corso", 4), ("3 aperte", "aperta", 3)]:
        cita(f"segnalazioni: stato {stato}", frase, stati.get(stato, 0) == n, f"{stati.get(stato, 0)}")

    tutti, _ = anagrafiche.genera_soci()
    entro_assemblea = (tutti["data_adesione"] <= "2026-07-09").sum()
    di_giugno = tutti["data_adesione"].between("2026-06-01", "2026-06-30").sum()
    cita("soci nella lista completa", "240 soci", len(tutti) == 240 and entro_assemblea == 240,
         f"{len(tutti)} soci, tutti aderenti entro il 9 luglio; {di_giugno} adesioni a giugno")
    fine_lezioni = consumi.CALENDARI_SCOLASTICI["2025/26"]["lezioni"][1]
    cita("fine delle lezioni", "il 10 giugno", fine_lezioni == date(2026, 6, 10), f"{fine_lezioni} (calendario 2025/26)")
    tariffa = float(T["parametro"].set_index("chiave").loc["tariffa_premio_eur_kwh", "valore"]) * 1000
    cita("tariffa premio", "130 euro per MWh", round(tariffa) == 130, f"{tariffa:.0f} €/MWh")


def grafici(T: dict[str, pd.DataFrame]) -> list[Path]:
    """Grafici di controllo in data/notebook/ (§6): una settimana di giugno per
    impianto e il profilo medio giornaliero per tipo di socio, in ora italiana."""
    NOTEBOOK.mkdir(exist_ok=True)
    salvati = []

    pp = T["previsione_produzione"].merge(T["produzione_oraria"], on=["impianto_id", "ts"])
    pp["t"] = pd.to_datetime(pp["ts"], utc=True).dt.tz_convert(FUSO)
    settimana = pp[(pp["t"] >= pd.Timestamp("2026-06-01", tz=FUSO)) & (pp["t"] < pd.Timestamp("2026-06-08", tz=FUSO))]
    fig, assi = plt.subplots(3, 1, figsize=(11, 8), sharex=True)
    nomi = T["impianto"].set_index("id")["nome"]
    for ax, (imp, g) in zip(assi, settimana.groupby("impianto_id")):
        ax.plot(g["t"], num(g, "kwh_previsti"), lw=1, ls="--", label="previsione (senza anomalie)")
        ax.plot(g["t"], num(g, "kwh"), lw=1.2, label="produzione")
        ax.set_title(f"Impianto {imp}: {nomi[imp]}", fontsize=10)
        ax.set_ylabel("kWh")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper right")
    assi[-1].set_xlabel("ora italiana, 1-7 giugno 2026")
    fig.tight_layout()
    percorso = NOTEBOOK / "campione_produzione_settimana_giugno.png"
    fig.savefig(percorso, dpi=100, metadata={"Software": None})
    plt.close(fig)
    salvati.append(percorso)

    c = T["consumo_orario"].merge(T["socio_profilo"], on="socio_id").merge(T["socio"][["id", "tipo"]], left_on="socio_id", right_on="id")
    c["ora"] = pd.to_datetime(c["ts"], utc=True).dt.tz_convert(FUSO).dt.hour
    c["kwh"] = num(c, "kwh")
    fig, assi = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, tipo in zip(assi, ["famiglia", "impresa", "ente"]):
        for profilo, g in c[c["tipo"] == tipo].groupby("profilo"):
            ax.plot(range(24), g.groupby("ora")["kwh"].mean().reindex(range(24)), marker="o", ms=3, label=profilo)
        ax.set_title(f"{tipo} (media di giugno)", fontsize=10)
        ax.set_xlabel("ora italiana")
        ax.set_xticks(range(0, 24, 2))
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    assi[0].set_ylabel("kWh nell'ora")
    fig.tight_layout()
    percorso = NOTEBOOK / "campione_profilo_medio_soci.png"
    fig.savefig(percorso, dpi=100, metadata={"Software": None})
    plt.close(fig)
    salvati.append(percorso)
    return salvati


def elenco_file(cartella: Path, T: dict[str, pd.DataFrame]) -> None:
    sezione("File di esempi/")
    for nome in sorted(T):
        dimensione = (cartella / f"{nome}.csv").stat().st_size
        print(f"  {nome + '.csv':28} {italiano(len(T[nome])):>7} righe {italiano(dimensione / 1024, 1):>9} KB")


def main() -> None:
    parser = argparse.ArgumentParser(description="Controlli di qualità del dataset UnderTheSun (§6)")
    parser.add_argument("--config", choices=list(config.CONFIGURAZIONI), required=True)
    parser.add_argument("--senza-rigenerare", action="store_true", help="salta i due rilanci di genera.py")
    args = parser.parse_args()
    if args.config != "piccola":
        raise SystemExit("I controlli per la versione completa sono da adattare: PVGIS annuo ±10%, ARERA, settimana invernale (§6).")
    conf = config.CONFIGURAZIONI[args.config]
    cartella = conf["cartella"]
    print(f"Controlli del campione in {cartella}")

    if not args.senza_rigenerare:
        riproducibilita(args.config, cartella)
    T = {f.stem: pd.read_csv(f, dtype=str, keep_default_na=False) for f in sorted(cartella.glob("*.csv"))}

    for passo in [lambda: dizionario_e_righe(T), lambda: formato(cartella), lambda: serie_complete(T, conf),
                  lambda: integrita(T), lambda: valori_ammessi(T), lambda: produzione_e_anomalie(T, conf),
                  lambda: consumi_e_derivate(T), lambda: verbale(T, cartella, conf)]:
        try:
            passo()
        except Exception as errore:  # un errore in una sezione non deve nascondere le altre
            controlla("sezione interrotta da un errore", False, f"{type(errore).__name__}: {errore}")

    sezione("Grafici di controllo")
    for percorso in grafici(T):
        print(f"  {percorso.relative_to(config.CARTELLA_DATA)}")
    elenco_file(cartella, T)

    falliti = [nome for nome, ok in ESITI if not ok]
    print(f"\nESITO: {len(ESITI) - len(falliti)} controlli ok su {len(ESITI)}" + (f", FALLITI: {len(falliti)}" if falliti else ""))
    for nome in falliti:
        print(f"  - {nome}")
    sys.exit(1 if falliti else 0)


if __name__ == "__main__":
    main()
