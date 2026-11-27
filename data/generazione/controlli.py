"""Controlli di qualità (guida §6), per il campione SAL 1 e per il dataset completo.

Uso, dalla cartella data/:
    python generazione/controlli.py --config piccola
    python generazione/controlli.py --config piccola --senza-rigenerare   (salta i due rilanci)
    python generazione/controlli.py --config completa

Dataset completo (impianti, soci, meteo, produzione, anomalie, consumi, bollette,
tabelle calcolate, ripartizione, riepilogo dei trimestri e file del seed):
vedi main_completa più sotto.

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
import derivate  # noqa: E402  (solo per la tabella dei trimestri)
import meteo  # noqa: E402
import produzione  # noqa: E402
import pvgis  # noqa: E402

DIZIONARIO = config.CARTELLA_DATA / "data-dictionary.md"
NOTEBOOK = config.CARTELLA_DATA / "notebook"
FUSO = "Europe/Rome"

# --- Regole del §2 ----------------------------------------------------------

ISTANTI = {"ts", "inizio", "fine"}
DATE = {"data_adesione", "data_attivazione", "mese", "data_assemblea", "giorno_max_produzione", "giorno_min_produzione"}
DECIMALI = {  # numero massimo di decimali (§2)
    **dict.fromkeys(["kwh", "kwh_previsti", "kwh_condivisi", "co2_evitata_kg"], 3),
    **dict.fromkeys(["importo_eur", "incentivo_eur"], 2),
    # riepilogo_trimestri (solo nel completo)
    **dict.fromkeys([*[f"produzione_impianto_{i}_kwh" for i in range(1, 9)], "produzione_kwh", "consumi_kwh",
                     "co2_evitata_condivisa_kg", "kwh_giorno_max", "kwh_giorno_min"], 3),
    **dict.fromkeys(["incentivo_famiglie_eur", "incentivo_imprese_eur", "incentivo_enti_eur"], 2),
    **dict.fromkeys(["irraggiamento_wm2", "irraggiamento_pannelli_wm2", "temperatura_c", "nuvolosita_pct", "neve_cm"], 1),
}
SERIE_ORARIE = {"meteo_orario", "produzione_oraria", "consumo_orario", "previsione_produzione",
                "previsione_consumo", "anomalia", "anomalie_vere"}  # istanti a ora piena
VALORI_VIETATI = {"nan", "none", "null", "-", "n/a"}
VUOTI_AMMESSI = {  # (file, colonna) in cui una cella vuota ha un significato
    ("segnalazione", "socio_id"), ("segnalazione", "impianto_id"), ("segnalazione", "impianto_id_llm"),
    ("anomalia", "fine"), ("anomalia", "tipo"), ("verbale", "sintesi"), ("socio_profilo", "ateco"),
    ("riepilogo_trimestri", "anomalie_dettaglio"),  # vuota in un trimestre senza anomalie
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


def riproducibilita(nome_config: str, cartella: Path, altri_argomenti: tuple[str, ...] = ()) -> None:
    sezione("Riproducibilità: due rilanci di genera.py")
    prima = hash_esempi(cartella)
    rilanci = []
    for _ in range(2):
        subprocess.run([sys.executable, str(Path(__file__).with_name("genera.py")), "--config", nome_config, *altri_argomenti],
                       cwd=config.CARTELLA_DATA, check=True, capture_output=True)
        rilanci.append(hash_esempi(cartella))
    controlla("i due rilanci producono file identici", rilanci[0] == rilanci[1], f"{len(rilanci[1])} file confrontati")
    cambiati = sorted(n for n in rilanci[0] if prima.get(n) != rilanci[0][n])
    controlla(f"i file di {cartella.name}/ erano già uguali a quelli rigenerati", not cambiati, ", ".join(cambiati))


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
            testo = dati.decode("utf-8")
        except UnicodeDecodeError:
            controlla(f"{nome}.csv", False, "non è UTF-8")
            continue
        # Le righe si contano con il modulo csv, una alla volta; le colonne si
        # controllano con pandas, tutte insieme: così basta poca memoria anche
        # per consumo_orario.csv (4,2 milioni di righe).
        lettore = csv.reader(io.StringIO(testo, newline=""))
        intestazione = next(lettore)
        n_righe = campi_diversi = 0
        for r in lettore:
            n_righe += 1
            campi_diversi += len(r) != len(intestazione)
        if not all(re.fullmatch(r"[a-z][a-z0-9_]*", c) for c in intestazione):
            problemi.append("intestazioni non in snake_case")
        if campi_diversi:
            problemi.append("righe con un numero di campi diverso dall'intestazione")
            controlla(f"{nome}.csv", False, "; ".join(problemi))
            continue
        tabella = pd.read_csv(io.StringIO(testo), dtype=str, keep_default_na=False)
        for colonna in intestazione:
            valori = tabella[colonna]
            pieni = valori[valori != ""]
            if len(pieni) < len(valori) and (nome, colonna) not in VUOTI_AMMESSI:
                problemi.append(f"{colonna}: celle vuote")
            if valori.str.strip().str.lower().isin(VALORI_VIETATI).any():
                problemi.append(f"{colonna}: NaN, None o '-'")
            if colonna in ISTANTI:
                forma = r"\d{4}-\d{2}-\d{2}T\d{2}:00:00Z" if nome in SERIE_ORARIE else r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z"
                if not pieni.str.fullmatch(forma).all():
                    problemi.append(f"{colonna}: istanti non nel formato {'a ora piena ' if nome in SERIE_ORARIE else ''}UTC con la Z")
            if colonna in DATE:
                if not (pieni.str.fullmatch(r"\d{4}-\d{2}-\d{2}").all()
                        and pd.to_datetime(pieni, format="%Y-%m-%d", errors="coerce").notna().all()):
                    problemi.append(f"{colonna}: date non nel formato AAAA-MM-GG")
                elif colonna == "mese" and (pieni.str[8:10] != "01").any():
                    problemi.append("mese: non è il primo giorno del mese")
            if colonna in DECIMALI:
                if not pieni.str.fullmatch(r"-?\d+(\.\d+)?").all():
                    problemi.append(f"{colonna}: numeri non nel formato 123.456")
                elif (pieni.str.extract(r"\.(\d+)$", expand=False).str.len() > DECIMALI[colonna]).any():
                    problemi.append(f"{colonna}: più di {DECIMALI[colonna]} decimali")
        controlla(f"{nome}.csv", not problemi, "; ".join(problemi) or f"{n_righe} righe, UTF-8 senza BOM, fine riga LF")


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


def grafico_pvgis_anno(impianti: pd.DataFrame) -> Path:
    """Giorno medio del 2023 per impianto: PVGIS seriescalc contro il modello tarato
    sul meteo Open-Meteo dello stesso anno. I picchi devono coincidere (§3.2)."""
    NOTEBOOK.mkdir(exist_ok=True)
    fig, assi = plt.subplots(2, 4, figsize=(15, 6.5), sharex=True)
    for ax, impianto in zip(assi.flat, impianti.itertuples()):
        c = pvgis.confronto_anno(impianto)
        k = pvgis._k(c)
        ora = c.index.hour
        ax.plot(range(24), c["kwh_pvgis"].groupby(ora).mean(), lw=1.5, label="PVGIS seriescalc")
        ax.plot(range(24), c["kwh_modello"].mul(k).clip(upper=impianto.kwp).groupby(ora).mean(), lw=1.2, ls="--",
                label=f"modello (k = {k})")
        ax.set_title(f"{impianto.id}. {impianto.nome}", fontsize=9)
        ax.set_xticks(range(0, 24, 3))
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, loc="upper left")
    for ax in assi[1]:
        ax.set_xlabel("ora UTC (inizio dell'ora)")
    for ax in assi[:, 0]:
        ax.set_ylabel("kWh medi nell'ora")
    fig.suptitle(f"Giorno medio del {pvgis.ANNO}: PVGIS e modello sul meteo Open-Meteo", fontsize=11)
    fig.tight_layout()
    percorso = NOTEBOOK / f"completa_pvgis_{pvgis.ANNO}_giorno_medio.png"
    fig.savefig(percorso, dpi=100, metadata={"Software": None})
    plt.close(fig)
    return percorso


def elenco_file(cartella: Path, T: dict[str, pd.DataFrame]) -> None:
    sezione(f"File di {cartella.name}/")
    for nome in sorted(T):
        dimensione = (cartella / f"{nome}.csv").stat().st_size
        print(f"  {nome + '.csv':28} {italiano(len(T[nome])):>7} righe {italiano(dimensione / 1024, 1):>9} KB")


# =============================================================================
# Dataset completo: parte 1 (impianti, soci, meteo, produzione e anomalie),
# parte 2 (consumi e bollette) e parte 3a (tabelle calcolate, ripartizione,
# riepilogo dei trimestri e file del seed)
# =============================================================================

RIGHE_COMPLETA = {  # §5 (v1.10)
    "impianto": 8, "socio": 240, "socio_profilo": 240, "parametro": 8,
    "meteo_orario": 140_160, "produzione_oraria": 140_160,
    "consumo_orario": 4_204_800, "bolletta": 5_760, "anomalie_vere": 41,
    "ripartizione_mensile": 4_579, "previsione_produzione": 140_160, "previsione_consumo": 4_204_800,
    "anomalia": 1, "riepilogo_trimestri": 8,
}
TESTI_DA_SCRIVERE = ["segnalazione", "verbale"]  # per ora solo le intestazioni: i testi arrivano nella parte 3b
FILE_COMPLETA = sorted([*RIGHE_COMPLETA, *TESTI_DA_SCRIVERE])
FUORI_DIZIONARIO = {"riepilogo_trimestri"}  # file di lavoro che il data dictionary v1 non descrive: colonne da config.py
CARTELLA_REPO = config.CARTELLA_DATA.parent
CARICA_SQL = CARTELLA_REPO / "db" / "seed" / "carica.sql"
MIGRAZIONI = CARTELLA_REPO / "db" / "migrations"
TOLLERANZA_MESE = 0.4  # kWh: un mese ha al massimo 744 ore, ognuna arrotondata di al massimo 0,0005 kWh
TOLLERANZA_FAMIGLIE = 0.05  # ±5%: la media di 200 scale lognormali (σ = 0,35) oscilla di circa il 2,5%
TOLLERANZA_FASCE = 0.03  # 3 punti: spostamenti di ±1 ora e rumore muovono un po' di consumo tra le fasce
ANOMALIE_CONTATE = {"guasto": 10, "stringa": 4, "sporcizia": 5}  # §3.3; i guasti comprendono quello fisso
ANNI = {"nov 2024-ott 2025": ("2024-11-01", "2025-11-01"), "nov 2025-ott 2026": ("2025-11-01", "2026-11-01")}
SETTIMANE = {"estiva": "2025-07-14", "invernale": "2026-02-02"}  # lunedì, ora italiana
IMPIANTI_VALLE, IMPIANTI_PIANURA = [5, 6, 8], [1, 2, 3, 7]  # §1.1
ENTI_CON_IMPIANTO = [("scuola", "Pinerolo"), ("uffici_comunali", "San Secondo di Pinerolo"),
                     ("impianto_sportivo", "Bricherasio"), ("biblioteca", "Torre Pellice"), ("rsa", "Villar Perosa")]
TOLLERANZA = 0.0015  # kWh: valori a 3 decimali
TOLLERANZA_CAMPIONE = 0.001  # kWh: completa e campione arrotondati entrambi a 3 decimali
COLORI_ANOMALIE = {"guasto": "tab:red", "stringa": "tab:orange", "sporcizia": "tab:brown", "neve": "tab:blue"}


def utc(testo: str) -> pd.Timestamp:
    return pd.Timestamp(testo, tz="UTC")


def file_e_righe_completa(T: dict[str, pd.DataFrame]) -> None:
    sezione("File, intestazioni (data dictionary) e righe (§5)")
    presenti = sorted(T)
    controlla("in output/ ci sono i file del dataset completo", presenti == FILE_COMPLETA,
              ", ".join(presenti) if presenti == FILE_COMPLETA
              else f"mancano {sorted(set(FILE_COMPLETA) - set(presenti))}, in più {sorted(set(presenti) - set(FILE_COMPLETA))}")
    voci = leggi_dizionario(DIZIONARIO)
    for nome in presenti:
        df, problemi = T[nome], []
        if nome in FUORI_DIZIONARIO:
            attese, fonte = config.COLONNE.get(nome), "in config.py (non è nel data dictionary)"
        else:
            attese, fonte = (voci.get(nome) or {}).get("colonne"), "nel data dictionary"
        if list(df.columns) != attese:
            problemi.append(f"colonne {list(df.columns)}, {fonte} {attese}")
        if nome in RIGHE_COMPLETA and len(df) != RIGHE_COMPLETA[nome]:
            problemi.append(f"{len(df)} righe, attese {RIGHE_COMPLETA[nome]}")
        if nome in TESTI_DA_SCRIVERE and len(df):
            problemi.append(f"{len(df)} righe: per ora deve avere solo le intestazioni (testi nella parte 3b)")
        dettaglio = "solo intestazioni, i testi arrivano nella parte 3b" if nome in TESTI_DA_SCRIVERE else f"{italiano(len(df))} righe"
        controlla(f"{nome}.csv: intestazioni e righe", not problemi, "; ".join(problemi) or dettaglio)


def serie_complete_completa(T: dict[str, pd.DataFrame], conf: dict) -> None:
    sezione("Serie orarie complete (§6)")
    attese = list(pd.date_range(conf["primo_ts"], conf["ultimo_ts"], freq="h").strftime("%Y-%m-%dT%H:%M:%SZ"))
    impianti = sorted(T["impianto"]["id"])
    for nome in ["meteo_orario", "produzione_oraria", "previsione_produzione"]:
        df = T[nome]
        ok = sorted(df["impianto_id"].unique()) == impianti and all(sorted(g["ts"]) == attese for _, g in df.groupby("impianto_id"))
        controlla(f"{nome}: {italiano(len(attese))} ore per ognuno degli {len(impianti)} impianti, senza buchi né duplicati", ok)
    soci = sorted(T["socio"]["id"])
    for nome in ["consumo_orario", "previsione_consumo"]:
        c = T[nome]
        ok = sorted(c["socio_id"].unique()) == soci and all(sorted(g["ts"]) == attese for _, g in c.groupby("socio_id"))
        controlla(f"{nome}: {italiano(len(attese))} ore per ognuno dei {len(soci)} soci, senza buchi né duplicati "
                  "(anche nei 4 giorni del cambio d'ora)", ok)


def integrita_completa(T: dict[str, pd.DataFrame]) -> None:
    sezione("ID: unici e coerenti tra i file (§2, §6)")
    for nome in ["impianto", "socio", "anomalie_vere", "bolletta", "anomalia"]:
        ids = T[nome]["id"].astype(int).tolist()
        controlla(f"{nome}.id: 1, 2, 3, ... senza buchi né doppioni", sorted(ids) == list(range(1, len(ids) + 1)))
    soci, impianti = set(T["socio"]["id"]), set(T["impianto"]["id"])
    for nome, colonna, insieme, tabella in [
        ("socio_profilo", "socio_id", soci, "socio"), ("meteo_orario", "impianto_id", impianti, "impianto"),
        ("produzione_oraria", "impianto_id", impianti, "impianto"), ("anomalie_vere", "impianto_id", impianti, "impianto"),
        ("consumo_orario", "socio_id", soci, "socio"), ("bolletta", "socio_id", soci, "socio"),
        ("previsione_produzione", "impianto_id", impianti, "impianto"), ("previsione_consumo", "socio_id", soci, "socio"),
        ("anomalia", "impianto_id", impianti, "impianto"), ("ripartizione_mensile", "socio_id", soci, "socio"),
    ]:
        mancanti = set(T[nome][colonna]) - insieme
        controlla(f"{nome}.{colonna} esiste in {tabella}", not mancanti, f"non trovati: {sorted(mancanti)}" if mancanti else "")
    controlla("socio_profilo ha una riga per ogni socio", sorted(T["socio_profilo"]["socio_id"]) == sorted(soci))


def anagrafiche_completa(T: dict[str, pd.DataFrame], conf: dict) -> None:
    sezione("Anagrafiche (§1.2, §1.3, §3.5)")
    imp = T["impianto"]
    controlla("impianto: gli 8 impianti della tabella del §1.2", imp.equals(anagrafiche.tabella_impianti().astype(str)))
    kwp = num(imp, "kwp")
    controlla("impianto: 950 kWp in totale, tutti ≤ 200 kWp", kwp.sum() == 950 and (kwp <= 200).all(), f"{kwp.sum():.0f} kWp")
    controlla("impianto: tutti attivi prima dell'inizio del periodo", (imp["data_attivazione"] < conf["primo_ts"][:10]).all())
    controlla("parametro: le 8 righe del §3.5", T["parametro"].equals(anagrafiche.tabella_parametri().astype(str)))

    s = T["socio"].merge(T["socio_profilo"], left_on="id", right_on="socio_id")
    tipi = s["tipo"].value_counts().to_dict()
    controlla("socio: 200 famiglie, 30 imprese e 10 enti", tipi == {"famiglia": 200, "impresa": 30, "ente": 10},
              ", ".join(f"{t} {n}" for t, n in tipi.items()))
    profili_attesi = {"famiglia": 200}
    ateco = {"famiglia": ""}
    for profilo, codice, quante, _ in anagrafiche.IMPRESE:
        profili_attesi[profilo], ateco[profilo] = quante, codice
    for profilo, codice, *_ in anagrafiche.ENTI:
        profili_attesi[profilo], ateco[profilo] = profili_attesi.get(profilo, 0) + 1, codice
    controlla("socio_profilo: profili e codici ATECO come nella tabella del §1.3",
              s["profilo"].value_counts().to_dict() == profili_attesi and (s["ateco"] == s["profilo"].map(ateco)).all())
    controlla("socio.comune e impianto.comune: uno degli 8 comuni", set(s["comune"]) <= COMUNI and set(imp["comune"]) <= COMUNI)
    fondatori = s["data_adesione"].between("2024-06-01", "2024-10-31").sum()
    altri = s["data_adesione"].between("2024-11-01", "2026-06-30").sum()
    controlla("socio: 120 fondatori (giugno-ottobre 2024) e 120 adesioni da novembre 2024 a giugno 2026",
              fondatori == 120 and altri == 120, f"{fondatori} e {altri}")
    controlla("socio: ID in ordine di data di adesione", T["socio"]["data_adesione"].is_monotonic_increasing)
    controlla("socio: nomi tutti diversi", T["socio"]["nome"].is_unique)
    enti = s[s["tipo"] == "ente"]
    controlla("socio: gli enti sono fondatori e quelli che ospitano un impianto stanno nel suo comune",
              (enti["data_adesione"] <= "2024-10-31").all()
              and all(((enti["profilo"] == p) & (enti["comune"] == c)).any() for p, c in ENTI_CON_IMPIANTO))
    scala = num(s, "scala")
    medie = scala.groupby(s["tipo"]).mean()
    controlla("socio_profilo.scala: positiva, con media vicina a 1 per ogni tipo (0,8-1,2)",
              (scala > 0).all() and medie.between(0.8, 1.2).all(), ", ".join(f"{t} {m:.3f}" for t, m in medie.items()))


def meteo_completa(T: dict[str, pd.DataFrame]) -> None:
    sezione("Meteo (§1.1, §3.1)")
    m = T["meteo_orario"]
    controlla("meteo: irraggiamenti e neve non negativi, nuvolosità tra 0 e 100",
              (num(m, "irraggiamento_wm2") >= 0).all() and (num(m, "irraggiamento_pannelli_wm2") >= 0).all()
              and (num(m, "neve_cm") >= 0).all() and num(m, "nuvolosita_pct").between(0, 100).all())
    celle = meteo.celle(anagrafiche.tabella_impianti()).set_index("impianto_id")["cella"]
    pianura = set(celle[IMPIANTI_PIANURA])
    controlla("§1.1: gli impianti di valle (5, 6, 8) sono in celle meteo diverse da quelle di pianura (1, 2, 3, 7)",
              not set(celle[IMPIANTI_VALLE]) & pianura, ", ".join(f"impianto {i}: cella {c}" for i, c in celle.items()))
    neve = num(m, "neve_cm").groupby(m["impianto_id"].astype(int)).sum()
    print("  neve caduta in 2 anni (cm): " + ", ".join(f"impianto {i}: {italiano(v, 1)}" for i, v in neve.items()))


def produzione_completa(T: dict[str, pd.DataFrame], conf: dict) -> pd.DataFrame:
    """Controlli della produzione; restituisce la tabella ora per ora con la
    produzione attesa (formula del §3.2 rifatta qui), che serve alle anomalie."""
    sezione("Produzione (§3.2, §6)")
    imp = anagrafiche.tabella_impianti()
    k = pvgis.k_impianti(conf, imp)
    d = (T["produzione_oraria"].merge(T["meteo_orario"], on=["impianto_id", "ts"])
         .assign(impianto_id=lambda x: x["impianto_id"].astype(int)).merge(imp[["id", "kwp"]], left_on="impianto_id", right_on="id"))
    kwh, gti, kwp = num(d, "kwh"), num(d, "irraggiamento_pannelli_wm2"), d["kwp"]
    controlla("produzione mai negativa", (kwh >= 0).all())
    controlla("produzione 0 quando irraggiamento_pannelli_wm2 è 0", (kwh[gti == 0] == 0).all(), f"{italiano(int((gti == 0).sum()))} ore senza sole")
    controlla("produzione mai sopra kwp", (kwh <= kwp).all(), f"massimo {(kwh / kwp).max():.2f} kWh per kWp")

    t_modulo = num(d, "temperatura_c") + 0.03 * gti
    d["attesa"] = (kwp * gti / 1000 * 0.86 * (1 - 0.004 * (t_modulo - 25)) * d["impianto_id"].map(k)).clip(0, kwp)
    d["kwh_num"] = kwh
    d["t"] = pd.to_datetime(d["ts"], utc=True)

    controlla("k_impianto vicino a 1 (tra 0,85 e 1,05)", all(0.85 <= v <= 1.05 for v in k.values()),
              ", ".join(f"{i}: {v}" for i, v in k.items()))
    val = pvgis.validazione(imp)
    controlla(f"PVGIS {pvgis.ANNO}: orari non sfasati (correlazione massima senza spostamenti)",
              ((val["r"] >= val["r_-1h"]) & (val["r"] >= val["r_+1h"])).all())
    print(f"  Validazione {pvgis.ANNO}, modello tarato contro PVGIS seriescalc (§3.2, passo 4):")
    print("  " + val.to_string(index=False).replace("\n", "\n  "))

    righe, scarti = [], []
    for impianto in imp.itertuples():
        e_y = pvgis.pvcalc(impianto)["outputs"]["totals"]["fixed"]["E_y"] / impianto.kwp
        sel = d["impianto_id"] == impianto.id
        per_anno = []
        for dal, al in ANNI.values():
            anno = sel & (d["ts"] >= f"{dal}T00:00:00Z") & (d["ts"] < f"{al}T00:00:00Z")
            per_anno.append((d.loc[anno, "kwh_num"].sum() / impianto.kwp / e_y - 1) * 100)
        scarti += per_anno
        righe.append(f"{impianto.id}: " + "/".join(f"{s:+.1f}%" for s in per_anno))
    controlla("produzione annua per kWp entro ±10% di PVGIS PVcalc, in ognuno dei due anni (§6)",
              all(abs(s) <= 10 for s in scarti), ", ".join(righe))
    return d


def anomalie_completa(T: dict[str, pd.DataFrame], d: pd.DataFrame) -> None:
    sezione("Anomalie (§3.3)")
    a = T["anomalie_vere"].assign(
        impianto_id=lambda x: x["impianto_id"].astype(int), perdita=lambda x: num(x, "perdita_pct"),
        i=lambda x: pd.to_datetime(x["inizio"], utc=True), f=lambda x: pd.to_datetime(x["fine"], utc=True))
    a["ore"] = (a["f"] - a["i"]) / produzione.ORA
    conteggi = a["tipo"].value_counts().to_dict()
    controlla("10 guasti (compreso quello fisso), 4 stringhe e 5 sporcizie, più gli episodi di neve",
              all(conteggi.get(t, 0) == n for t, n in ANOMALIE_CONTATE.items()),
              ", ".join(f"{t} {conteggi.get(t, 0)}" for t in ["guasto", "stringa", "sporcizia", "neve"]))
    prima = a.iloc[0]
    controlla("id 1 è il guasto fisso dell'impianto 3 del 1 giugno 2026, come nel campione",
              (prima["impianto_id"], prima["inizio"], prima["fine"], prima["tipo"], prima["perdita"])
              == (3, "2026-06-01T11:00:00Z", "2026-06-01T15:00:00Z", "guasto", 100.0))

    g, s, p, n = (a[a["tipo"] == t] for t in ["guasto", "stringa", "sporcizia", "neve"])
    controlla("guasti: da 2 ore a 5 giorni, produzione a 0", g["ore"].between(2, 120).all() and (g["perdita"] == 100).all(),
              f"durate da {g['ore'].min():.0f} a {g['ore'].max():.0f} ore")
    controlla("stringhe: calo fisso del 20-35% per 1-4 settimane",
              s["perdita"].between(20, 35).all() and s["ore"].between(7 * 24, 28 * 24).all(),
              f"perdite {s['perdita'].min()}-{s['perdita'].max()}%, durate {s['ore'].min() / 24:.1f}-{s['ore'].max() / 24:.1f} giorni")
    ritmo = p["perdita"] / (p["ore"] / 168)
    controlla("sporcizia: arriva al 10-15% a circa l'1% a settimana, inizia a mezzanotte tra aprile e luglio",
              p["perdita"].between(10, 15).all() and ritmo.between(0.78, 1.22).all()
              and p["i"].dt.month.isin([4, 5, 6, 7]).all() and (p["i"].dt.hour == 0).all(),
              f"perdite {p['perdita'].min()}-{p['perdita'].max()}%, da {ritmo.min():.2f} a {ritmo.max():.2f}% a settimana")
    controlla("neve: produzione al 5% (perdita 95%)", (n["perdita"] == 95).all(), f"{len(n)} episodi")

    attesa = d.set_index(["impianto_id", "ts"])["attesa"]
    kwp = d.groupby("impianto_id")["kwp"].first()
    casuali_brevi = a[a["tipo"].isin(["guasto", "stringa"]) & (a["id"] != "1")]
    controlla("guasti e stringhe casuali iniziano in un'ora di sole (produzione attesa ≥ 10% di kwp)",
              all(attesa[(r.impianto_id, r.inizio)] >= 0.1 * kwp[r.impianto_id] for r in casuali_brevi.itertuples()))

    # Neve: la regola del §3.3 rifatta qui sulle ore, poi confrontata con produzione.episodi_neve
    m = T["meteo_orario"].assign(impianto_id=lambda x: x["impianto_id"].astype(int), neve_cm=lambda x: num(x, "neve_cm"),
                                 temperatura_c=lambda x: num(x, "temperatura_c"))
    coperte = iniziano_bene = uguali = True
    for imp_id, mi in m.groupby("impianto_id"):
        mi = mi.sort_values("ts")
        neve_24h = mi["neve_cm"].rolling(24, min_periods=1).sum().shift(1).round(1)
        ore_neve = pd.to_datetime(mi.loc[neve_24h >= 2.0, "ts"], utc=True)
        ep = n[n["impianto_id"] == imp_id]
        coperte &= all(((ep["i"] <= t) & (ep["f"] > t)).any() for t in ore_neve)
        iniziano_bene &= set(ep["i"]) <= set(ore_neve)
        uguali &= list(zip(ep["i"], ep["f"])) == produzione.episodi_neve(mi)
    controlla("neve: ogni ora con almeno 2 cm nelle 24 ore precedenti è dentro un episodio, e ogni episodio inizia in una di queste ore",
              coperte and iniziano_bene, f"{len(n)} episodi su {n['impianto_id'].nunique()} impianti")
    controlla("neve: gli episodi finiscono dopo 2 giorni con temperatura massima sopra 3 °C (produzione.episodi_neve)", uguali)

    sovrapposte, vicine = [], []
    for _, gi in a.sort_values("i").groupby("impianto_id"):
        righe = list(gi.itertuples())
        for prec, succ in zip(righe, righe[1:]):
            if succ.i < prec.f:
                sovrapposte.append((prec.id, succ.id))
            elif not (prec.tipo == succ.tipo == "neve") and succ.i - prec.f < produzione.DISTACCO:
                vicine.append((prec.id, succ.id))
    controlla("anomalie dello stesso impianto che non si sovrappongono", not sovrapposte, f"sovrapposte: {sovrapposte}" if sovrapposte else "")
    controlla("tra un'anomalia casuale e le altre dello stesso impianto passano almeno 24 ore", not vicine, f"troppo vicine: {vicine}" if vicine else "")
    giugno = a[a["impianto_id"].isin([1, 2, 3]) & (a["i"] < utc("2026-07-01")) & (a["f"] > utc("2026-06-01"))]
    controlla("campione stabile: a giugno 2026 sugli impianti 1-3 c'è solo il guasto fisso (§3.3)",
              giugno["id"].tolist() == ["1"], f"anomalie che toccano giugno: {giugno['id'].tolist()}")

    # Ogni anomalia si vede: produzione sotto l'atteso, con l'effetto previsto ora per ora
    esiti = {tipo: [] for tipo in ["guasto", "stringa", "sporcizia", "neve"]}
    dentro_qualcuna = pd.Series(False, index=d.index)
    for r in a.itertuples():
        sel = (d["impianto_id"] == r.impianto_id) & (d["ts"] >= r.inizio) & (d["ts"] < r.fine)
        dentro_qualcuna |= sel
        att, kwh, t = d.loc[sel, "attesa"], d.loc[sel, "kwh_num"], d.loc[sel, "t"]
        if r.tipo == "sporcizia":  # cresce in modo lineare e arriva a perdita_pct nell'ultima ora
            fattore = 1 - r.perdita / 100 * ((t - r.i) / produzione.ORA + 1) / r.ore
        else:
            fattore = pd.Series(1 - r.perdita / 100, index=att.index)
        forma = (kwh - (att * fattore).round(3)).abs().max() <= TOLLERANZA
        sotto = kwh.sum() < att.sum() and (kwh <= att.round(3) + 1e-9).all()
        esiti[r.tipo].append((r.id, forma and sotto, (1 - kwh.sum() / att.sum()) * 100))
    for tipo, lista in esiti.items():
        non_visibili = [i for i, ok, _ in lista if not ok]
        perse = [x for *_, x in lista]
        controlla(f"{tipo}: tutte le {len(lista)} anomalie si vedono (produzione sotto l'atteso, con l'effetto previsto)",
                  lista and not non_visibili,
                  f"energia persa nella finestra da {min(perse):.0f}% a {max(perse):.0f}%" + (f"; non visibili: {non_visibili}" if non_visibili else ""))
    fuori = ~dentro_qualcuna
    controlla("fuori dalle anomalie la produzione è uguale alla formula",
              (d.loc[fuori, "kwh_num"] - d.loc[fuori, "attesa"].round(3)).abs().max() < TOLLERANZA)


def ore_italiane(ts: pd.Series) -> pd.DataFrame:
    """Per ogni istante UTC distinto: ora, mese e tipo di giorno in ora italiana, e
    fascia ARERA (§3.4). Si calcola sulle 17.520 ore una volta sola; per le righe
    di consumo_orario si usa poi la posizione dell'istante (get_indexer)."""
    unici = pd.Index(ts.unique())
    t = pd.DatetimeIndex(pd.to_datetime(unici, utc=True)).tz_convert(FUSO)
    ora = np.asarray(t.hour)
    festivo = np.array([g in consumi.FESTIVI or g.weekday() == 6 for g in t.date])
    sabato = (np.asarray(t.day_of_week) == 5) & ~festivo
    feriale = ~festivo & ~sabato
    f1 = feriale & (ora >= 8) & (ora < 19)
    f2 = (feriale & ((ora == 7) | ((ora >= 19) & (ora < 23)))) | (sabato & (ora >= 7) & (ora < 23))
    return pd.DataFrame({
        "ora": ora,
        "mese": np.asarray(t.month),
        "tipo_giorno": np.where(festivo, "festivo", np.where(sabato, "sabato", "feriale")),
        "fascia": np.where(f1, "F1", np.where(f2, "F2", "F3")),
    }, index=unici)


def consumi_completa(T: dict[str, pd.DataFrame]) -> None:
    sezione("Consumi (§3.4, §6)")
    c = T["consumo_orario"]
    kwh = num(c, "kwh").to_numpy()
    s = T["socio"].merge(T["socio_profilo"], left_on="id", right_on="socio_id").set_index("id")
    controlla("consumi mai negativi", (kwh >= 0).all(), f"da {kwh.min():.3f} a {kwh.max():.3f} kWh nell'ora")

    volumi = consumi.volumi_mensili()
    controlla("ARERA Torino 2025: 12 mesi positivi per ognuno dei 12 profili (classi di potenza del 27/11/2026)",
              set(volumi) == set(PROFILI) and all(len(v) == 12 and (v > 0).all() for v in volumi.values()),
              ", ".join(f"{p} {italiano(v.sum())}" for p, v in volumi.items()) + " kWh/anno")

    # §3.4, passo 6: il totale di ogni mese è volume ARERA × scala
    tot = pd.Series(kwh).groupby([c["socio_id"].to_numpy(), c["ts"].str.slice(0, 7).to_numpy()]).sum()
    soci, mesi = tot.index.get_level_values(0), tot.index.get_level_values(1)
    scala = num(s, "scala")
    attesi = np.array([volumi[s.at[i, "profilo"]][int(m[5:7]) - 1] * scala[i] for i, m in zip(soci, mesi)])
    scarto = np.abs(tot.to_numpy() - attesi).max()
    controlla(f"ogni socio, ogni mese UTC: totale = volume ARERA del mese × scala (scarto ≤ {italiano(TOLLERANZA_MESE, 1)} kWh, arrotondamenti)",
              len(tot) == len(s) * 24 and scarto <= TOLLERANZA_MESE, f"{italiano(len(tot))} mesi, scarto massimo {scarto:.3f} kWh")

    # §6: media annua delle famiglie vicina al valore ARERA di Torino
    famiglia = c["socio_id"].isin(set(s.index[s["tipo"] == "famiglia"])).to_numpy()
    n_famiglie = int((s["tipo"] == "famiglia").sum())
    arera_anno = volumi["famiglia"].sum()
    ok, righe = True, []
    for nome, (dal, al) in ANNI.items():
        anno = famiglia & (c["ts"] >= f"{dal}T00:00:00Z").to_numpy() & (c["ts"] < f"{al}T00:00:00Z").to_numpy()
        media = kwh[anno].sum() / n_famiglie
        ok &= abs(media / arera_anno - 1) <= TOLLERANZA_FAMIGLIE
        righe.append(f"{nome}: {italiano(media)} kWh ({(media / arera_anno - 1) * 100:+.1f}%)")
    controlla(f"famiglie: consumo annuo medio entro ±{TOLLERANZA_FAMIGLIE:.0%} del valore ARERA di Torino "
              f"({italiano(arera_anno)} kWh, somma dei 12 mesi), in ognuno dei due anni", ok, "; ".join(righe))

    # Fasce F1/F2/F3 delle famiglie contro ARERA (media dell'anno pesata sui volumi dei mesi)
    info = ore_italiane(c["ts"])
    posizione = info.index.get_indexer(c["ts"])
    fascia = info["fascia"].to_numpy()[posizione]
    quote = pd.Series(kwh[famiglia]).groupby(fascia[famiglia]).sum()
    quote /= quote.sum()
    q = consumi.quote_fasce_arera().loc[range(1, 13)]
    attese = q.mul(volumi["famiglia"], axis=0).sum() / arera_anno
    differenza = (quote - attese).abs().max()
    controlla(f"famiglie: quote F1/F2/F3 entro {TOLLERANZA_FASCE * 100:.0f} punti da quelle ARERA", differenza <= TOLLERANZA_FASCE,
              ", ".join(f"{f} {quote[f] * 100:.1f}% (ARERA {attese[f] * 100:.1f}%)" for f in ["F1", "F2", "F3"]))

    # Scuola: chiusa a luglio e agosto, aperta a ottobre (calendari scolastici, §3.4)
    scuola = c["socio_id"].isin(set(s.index[s["profilo"] == "scuola"])).to_numpy()
    ora = info["ora"].to_numpy()[posizione]
    mese = info["mese"].to_numpy()[posizione]
    lezione = (info["tipo_giorno"].to_numpy()[posizione] == "feriale") & (ora >= 9) & (ora < 15)
    notte = ora < 5

    def rapporto(mesi_scelti: list[int]) -> float:
        sel = scuola & np.isin(mese, mesi_scelti)
        return kwh[sel & lezione].mean() / kwh[sel & notte].mean()

    estate, ottobre = rapporto([7, 8]), rapporto([10])
    controlla("scuola: nessun picco nelle ore di lezione a luglio e agosto, picco a ottobre "
              "(consumo medio feriale 9-15 diviso consumo medio 0-5, ora italiana)",
              0.8 <= estate <= 1.25 and ottobre > 3, f"luglio-agosto {italiano(estate, 2)}, ottobre {italiano(ottobre, 2)}")


def bollette_completa(T: dict[str, pd.DataFrame]) -> None:
    sezione("Bollette (§4)")
    b, c = T["bolletta"], T["consumo_orario"]
    mesi_attesi = list(pd.date_range("2024-11-01", "2026-10-01", freq="MS").strftime("%Y-%m-%d"))
    ok = b["socio_id"].nunique() == len(T["socio"]) and all(list(g["mese"]) == mesi_attesi for _, g in b.groupby("socio_id"))
    controlla("bolletta: 24 mesi in ordine per ognuno dei 240 soci, da novembre 2024 a ottobre 2026", ok and len(b) == 240 * 24,
              f"{italiano(len(b))} righe")

    somma = num(c, "kwh").groupby([c["socio_id"], c["ts"].str.slice(0, 7) + "-01"]).sum().round(3)
    dalle_ore = somma.reindex(pd.MultiIndex.from_arrays([b["socio_id"], b["mese"]])).to_numpy()
    kwh = num(b, "kwh").to_numpy()
    controlla("bolletta.kwh = somma di consumo_orario del mese (in UTC)",
              not np.isnan(dalle_ore).any() and np.abs(kwh - dalle_ore).max() < 0.0005)

    prezzi = dict(zip(T["parametro"]["chiave"], num(T["parametro"], "valore")))
    tipo = b["socio_id"].map(T["socio"].set_index("id")["tipo"])
    prezzo = tipo.map(lambda t: prezzi[f"prezzo_energia_{t}_eur_kwh"]).to_numpy()
    importo = num(b, "importo_eur").to_numpy()
    controlla("bolletta.importo_eur = kwh × prezzo del tipo di socio (§3.5), al centesimo",
              np.abs(importo - np.round(kwh * prezzo, 2)).max() < 0.005)
    annua = pd.Series(importo).groupby(tipo.to_numpy()).sum() / tipo.groupby(b["socio_id"]).first().value_counts() / 2
    print("  bolletta annua media: " + ", ".join(f"{t} {italiano(annua[t])} €" for t in ["famiglia", "impresa", "ente"]))


def grafico_consumi(T: dict[str, pd.DataFrame]) -> Path:
    """Profilo medio giornaliero per tipo di socio (giorni feriali, ora italiana) e
    consumo mensile medio delle famiglie contro ARERA (§6)."""
    NOTEBOOK.mkdir(exist_ok=True)
    colori = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]  # palette categorica, in ordine fisso
    grigio = "#52514e"
    c = T["consumo_orario"]
    kwh = num(c, "kwh").to_numpy()
    s = T["socio"].merge(T["socio_profilo"], left_on="id", right_on="socio_id").set_index("id")
    profilo = c["socio_id"].map(s["profilo"]).to_numpy()
    info = ore_italiane(c["ts"])
    posizione = info.index.get_indexer(c["ts"])
    feriale = info["tipo_giorno"].to_numpy()[posizione] == "feriale"
    d = pd.DataFrame({"profilo": profilo[feriale], "ora": info["ora"].to_numpy()[posizione][feriale], "kwh": kwh[feriale]})
    medie = d.groupby(["profilo", "ora"])["kwh"].mean().unstack()
    quote = medie.div(medie.sum(axis=1), axis=0) * 100  # % del consumo del giorno in ogni ora

    fig, assi = plt.subplots(2, 2, figsize=(14, 9), facecolor="#fcfcfb")
    ax = assi[0, 0]
    forma = consumi.forma_famiglia_arera()
    arera = np.mean([forma[(m, "feriale")] for m in range(1, 13)], axis=0)
    ax.plot(range(24), quote.loc["famiglia"], lw=1.8, color=colori[0], label="famiglie del dataset (200)")
    ax.plot(range(24), arera / arera.sum() * 100, lw=1.5, ls="--", color=grigio, label="ARERA Torino, residenti 1,5-3 kW")
    ax.set_title("Famiglie: profilo medio dei giorni feriali", fontsize=10)

    for ax, tipo, elenco in [(assi[1, 0], "Imprese", anagrafiche.IMPRESE), (assi[1, 1], "Enti", anagrafiche.ENTI)]:
        profili = list(dict.fromkeys(p for p, *_ in elenco))
        for colore, p in zip(colori, profili):
            ax.plot(range(24), quote.loc[p], lw=1.8, color=colore, label=f"{p} ({(s['profilo'] == p).sum()})")
        ax.set_title(f"{tipo}: profilo medio dei giorni feriali", fontsize=10)
    for ax in [assi[0, 0], assi[1, 0], assi[1, 1]]:
        ax.set_xticks(range(0, 24, 2))
        ax.set_xlabel("ora italiana (inizio dell'ora)")
        ax.set_ylabel("% del consumo del giorno")

    ax = assi[0, 1]
    famiglie = c["socio_id"].isin(set(s.index[s["tipo"] == "famiglia"])).to_numpy()
    mensile = pd.Series(kwh[famiglie]).groupby(c["ts"].str.slice(0, 7).to_numpy()[famiglie]).sum() / int((s["tipo"] == "famiglia").sum())
    x = np.arange(len(mensile))
    ax.bar(x, mensile.to_numpy(), width=0.8, color=colori[0], label="famiglie del dataset: media per famiglia")
    volumi = consumi.volumi_mensili()["famiglia"]
    ax.plot(x, [volumi[int(m[5:7]) - 1] for m in mensile.index], color=grigio, lw=1.5, ls="--", marker="o", ms=5,
            label="ARERA Torino 2025, stesso mese")
    ax.set_xticks(x[::2], [m for m in mensile.index][::2], rotation=45, fontsize=8)
    ax.set_ylim(0, mensile.max() * 1.3)  # spazio per la legenda sopra le barre
    ax.set_ylabel("kWh nel mese")
    ax.set_title("Famiglie: consumo mensile, nov 2024 - ott 2026 (mesi in UTC)", fontsize=10)

    for ax in assi.flat:
        ax.set_facecolor("#fcfcfb")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
    fig.tight_layout()
    percorso = NOTEBOOK / "completa_consumi_profili.png"
    fig.savefig(percorso, dpi=90, metadata={"Software": None})
    plt.close(fig)
    return percorso


def confronto_campione(T: dict[str, pd.DataFrame]) -> None:
    piccola = config.CONFIGURAZIONI["piccola"]
    sezione("Giugno 2026, impianti 1-3: confronto con il campione (data/esempi/)")
    E = {nome: pd.read_csv(config.CARTELLA_ESEMPI / f"{nome}.csv", dtype=str, keep_default_na=False)
         for nome in ["impianto", "socio", "socio_profilo", "parametro", "meteo_orario", "produzione_oraria", "anomalie_vere"]}
    for nome, chiave in [("impianto", "id"), ("socio", "id"), ("socio_profilo", "socio_id"), ("parametro", "chiave")]:
        c, f = E[nome], T[nome]
        controlla(f"{nome}: le {len(c)} righe del campione sono uguali a quelle della completa con lo stesso {chiave}",
                  f[f[chiave].isin(c[chiave])].reset_index(drop=True).equals(c))

    def giugno(df: pd.DataFrame) -> pd.DataFrame:
        sel = df["impianto_id"].isin([str(i) for i in piccola["impianti"]]) & df["ts"].between(piccola["primo_ts"], piccola["ultimo_ts"])
        return df[sel].reset_index(drop=True)

    controlla("meteo_orario: identico al campione (stesso testo nei CSV)", giugno(T["meteo_orario"]).equals(E["meteo_orario"]),
              f"{italiano(len(E['meteo_orario']))} righe")

    k = pvgis.k_impianti(config.CONFIGURAZIONI["completa"], anagrafiche.tabella_impianti())
    kwp = anagrafiche.tabella_impianti().set_index("id")["kwp"]
    pc, pe = giugno(T["produzione_oraria"]), E["produzione_oraria"]
    allineate = pc[["impianto_id", "ts"]].equals(pe[["impianto_id", "ts"]])
    imp = pe["impianto_id"].astype(int)
    completa, campione = num(pc, "kwh"), num(pe, "kwh")
    limite = campione == imp.map(kwp)  # nel campione la formula ha toccato kwp: lì × k non vale
    scarto = (completa - campione * imp.map(k)).abs()
    controlla("produzione_oraria = campione × k_impianto, tranne le ore al limite kwp (scarto ≤ 0,001 kWh, arrotondamenti)",
              allineate and scarto[~limite].max() <= TOLLERANZA_CAMPIONE + 1e-9,
              f"scarto massimo {scarto[~limite].max():.4f} kWh su {italiano(int((~limite).sum()))} ore; "
              f"k: " + ", ".join(f"{i} = {k[i]}" for i in piccola["impianti"]))
    if limite.any():
        tra = (completa[limite] >= (campione * imp.map(k))[limite] - TOLLERANZA_CAMPIONE) & (completa[limite] <= imp.map(kwp)[limite])
        controlla("ore al limite kwp: la completa sta tra campione × k e kwp", tra.all(), f"{int(limite.sum())} ore")
    else:
        print("  nessuna ora al limite kwp nel campione")
    guasto_c = giugno(T["produzione_oraria"]).query("impianto_id == '3' and ts >= '2026-06-01T11:00:00Z' and ts < '2026-06-01T15:00:00Z'")
    guasto_e = pe.query("impianto_id == '3' and ts >= '2026-06-01T11:00:00Z' and ts < '2026-06-01T15:00:00Z'")
    controlla("guasto dell'impianto 3 del 1/6: stessa riga di anomalie_vere e le stesse 4 ore a zero",
              T["anomalie_vere"].iloc[[0]].reset_index(drop=True).equals(E["anomalie_vere"])
              and len(guasto_c) == len(guasto_e) == 4 and (num(guasto_c, "kwh") == 0).all() and (num(guasto_e, "kwh") == 0).all())


def grafici_completa(T: dict[str, pd.DataFrame], d: pd.DataFrame) -> list[Path]:
    """Grafici di controllo del dataset completo in data/notebook/ (§6)."""
    NOTEBOOK.mkdir(exist_ok=True)
    salvati = [grafico_pvgis_anno(anagrafiche.tabella_impianti())]
    d = d.assign(t_it=d["t"].dt.tz_convert(FUSO))
    nomi = T["impianto"].assign(id=lambda x: x["id"].astype(int)).set_index("id")["nome"]
    a = T["anomalie_vere"].assign(impianto_id=lambda x: x["impianto_id"].astype(int),
                                  i=lambda x: pd.to_datetime(x["inizio"], utc=True), f=lambda x: pd.to_datetime(x["fine"], utc=True))

    # 1. Una settimana estiva e una invernale per ogni impianto
    fig, assi = plt.subplots(8, 2, figsize=(15, 22), sharey="row")
    for colonna, (nome, lunedi) in enumerate(SETTIMANE.items()):
        dal = pd.Timestamp(lunedi, tz=FUSO)
        settimana = d[(d["t_it"] >= dal) & (d["t_it"] < dal + pd.Timedelta(days=7))]
        for riga, (imp, g) in enumerate(settimana.groupby("impianto_id")):
            ax = assi[riga, colonna]
            ax.plot(g["t_it"], g["attesa"], lw=1, ls="--", color="grey", label="attesa senza anomalie")
            ax.plot(g["t_it"], g["kwh_num"], lw=1.2, label="produzione")
            for r in a[(a["impianto_id"] == imp) & (a["i"] < settimana["t"].max()) & (a["f"] > settimana["t"].min())].itertuples():
                ax.axvspan(max(r.i, settimana["t"].min()), min(r.f, settimana["t"].max()), color=COLORI_ANOMALIE[r.tipo], alpha=0.15,
                           label=f"anomalia {r.id}: {r.tipo}")
            ax.set_title(f"{imp}. {nomi[imp]}: settimana {nome} dal {dal:%d/%m/%Y}", fontsize=9)
            ax.grid(alpha=0.3)
            ax.legend(fontsize=7, loc="upper right")
            ax.tick_params(labelsize=7)
            if colonna == 0:
                ax.set_ylabel("kWh")
    fig.tight_layout()
    percorso = NOTEBOOK / "completa_produzione_settimane.png"
    fig.savefig(percorso, dpi=80, metadata={"Software": None})
    plt.close(fig)
    salvati.append(percorso)

    # 2. Calendario delle anomalie
    fig, ax = plt.subplots(figsize=(15, 4.5))
    for r in a.itertuples():
        ax.barh(r.impianto_id, (r.f - r.i) / pd.Timedelta(days=1), left=r.i.tz_localize(None), height=0.6,
                color=COLORI_ANOMALIE[r.tipo], edgecolor="black", linewidth=0.3)
    for tipo, colore in COLORI_ANOMALIE.items():
        ax.barh(0, 0, color=colore, label=tipo)
    ax.axvspan(pd.Timestamp("2026-06-01"), pd.Timestamp("2026-07-01"), color="green", alpha=0.08, label="giugno 2026 (campione)")
    ax.set_yticks(range(1, 9), [f"{i}. {nomi[i]}" for i in range(1, 9)], fontsize=8)
    ax.set_ylim(0.4, 8.6)
    ax.invert_yaxis()
    ax.set_xlim(pd.Timestamp("2024-11-01"), pd.Timestamp("2026-11-01"))
    ax.grid(alpha=0.3, axis="x")
    ax.legend(fontsize=8, ncol=5, loc="lower center", bbox_to_anchor=(0.5, 1.0))
    ax.set_title("anomalie_vere: calendario per impianto", fontsize=10, pad=28)
    fig.tight_layout()
    percorso = NOTEBOOK / "completa_anomalie_calendario.png"
    fig.savefig(percorso, dpi=90, metadata={"Software": None})
    plt.close(fig)
    salvati.append(percorso)

    # 3. Un esempio per tipo: ore per guasto e neve, giorni per stringa e sporcizia
    esempi = {
        "guasto": a[(a["tipo"] == "guasto") & (a["f"] - a["i"] >= pd.Timedelta(days=1))].iloc[0],
        "neve": a[a["tipo"] == "neve"].iloc[0],
        "stringa": a[a["tipo"] == "stringa"].iloc[0],
        "sporcizia": a[a["tipo"] == "sporcizia"].iloc[0],
    }
    fig, assi = plt.subplots(2, 2, figsize=(15, 8))
    for ax, (tipo, r) in zip(assi.flat, esempi.items()):
        orario = tipo in ("guasto", "neve")
        margine = pd.Timedelta(days=2 if orario else 14)
        g = d[(d["impianto_id"] == r.impianto_id) & (d["t"] >= r.i - margine) & (d["t"] < r.f + margine)]
        if not orario:  # kWh al giorno (ora italiana), senza il primo e l'ultimo giorno, incompleti
            g = g.groupby(g["t_it"].dt.floor("D"))[["attesa", "kwh_num"]].sum().reset_index().iloc[1:-1]
        x = g["t_it"]
        ax.plot(x, g["attesa"], lw=1, ls="--", color="grey", label="attesa senza anomalie")
        ax.plot(x, g["kwh_num"], lw=1.2, label="produzione")
        ax.axvspan(r.i.tz_convert(FUSO), r.f.tz_convert(FUSO), color=COLORI_ANOMALIE[tipo], alpha=0.15, label=f"{tipo} ({r.perdita_pct}%)")
        ax.set_title(f"anomalia {r.id}: {tipo}, impianto {r.impianto_id} ({'kWh orari' if orario else 'kWh al giorno'})", fontsize=9)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, loc="upper right")
        ax.tick_params(labelsize=7)
    fig.tight_layout()
    percorso = NOTEBOOK / "completa_anomalie_esempi.png"
    fig.savefig(percorso, dpi=90, metadata={"Software": None})
    plt.close(fig)
    salvati.append(percorso)
    return salvati


# --- Parte 3a: tabelle calcolate, ripartizione, riepilogo e seed ---------------


def tabelle_calcolate_completa(T: dict[str, pd.DataFrame], d: pd.DataFrame) -> None:
    """Le tabelle provvisorie del §4 (v1.10), con le stesse regole del campione."""
    sezione("Tabelle calcolate provvisorie (§4): previsioni e anomalia")
    pp = (T["previsione_produzione"].assign(impianto_id=lambda x: x["impianto_id"].astype(int))
          .merge(d[["impianto_id", "ts", "kwh", "kwh_num", "attesa"]], on=["impianto_id", "ts"]))
    previsti = num(pp, "kwh_previsti")
    controlla("previsioni mai negative (vincolo dello schema)",
              (previsti >= 0).all() and (num(T["previsione_consumo"], "kwh_previsti") >= 0).all())
    scarto = (previsti - pp["attesa"].round(3)).abs()
    controlla("previsione_produzione = formula del §3.2 senza anomalie (rifatta qui), ora per ora",
              len(pp) == len(T["previsione_produzione"]) and scarto.max() <= TOLLERANZA, f"scarto massimo {scarto.max():.4f} kWh")
    dentro = pd.Series(False, index=pp.index)
    for a in T["anomalie_vere"].itertuples():
        dentro |= (pp["impianto_id"] == int(a.impianto_id)) & (pp["ts"] >= a.inizio) & (pp["ts"] < a.fine)
    uguali = pp["kwh_previsti"] == pp["kwh"]  # stesso testo nei due CSV
    controlla("previsione_produzione = produzione_oraria fuori dalle anomalie, e mai sotto nelle ore delle anomalie",
              uguali[~dentro].all() and (previsti[dentro] >= pp.loc[dentro, "kwh_num"]).all(),
              f"{italiano(int((~uguali).sum()))} ore diverse, tutte dentro le {len(T['anomalie_vere'])} anomalie")

    pc, b = T["previsione_consumo"], T["bolletta"]
    somma = num(pc, "kwh_previsti").groupby([pc["socio_id"], pc["ts"].str.slice(0, 7) + "-01"]).sum()
    dalle_ore = somma.reindex(pd.MultiIndex.from_arrays([b["socio_id"], b["mese"]])).to_numpy()
    scarto = np.abs(dalle_ore - num(b, "kwh").to_numpy())
    controlla("previsione_consumo: ogni mese ha il totale della bolletta (stesso volume ARERA × scala, senza rumore)",
              not np.isnan(dalle_ore).any() and scarto.max() <= 2 * TOLLERANZA_MESE,
              f"scarto massimo {scarto.max():.3f} kWh (due serie arrotondate ora per ora)")
    reale = num(T["consumo_orario"], "kwh").to_numpy()
    prevista = num(pc, "kwh_previsti").to_numpy()
    stessi = (T["consumo_orario"]["socio_id"].to_numpy() == pc["socio_id"].to_numpy()).all() and (
        T["consumo_orario"]["ts"].to_numpy() == pc["ts"].to_numpy()).all()
    if stessi:
        positivi = prevista > 0
        print(f"  il consumo si scosta dalla previsione in media del {np.abs(reale[positivi] / prevista[positivi] - 1).mean() * 100:.1f}% "
              "(rumore orario del §3.4, σ = 15%)")

    campione = pd.read_csv(config.CARTELLA_ESEMPI / "anomalia.csv", dtype=str, keep_default_na=False)
    colonne = ["impianto_id", "inizio", "fine", "tipo"]
    controlla("anomalia: solo il guasto dell'impianto 3 del 1/6/2026 (anomalie_vere id 1), identica al campione",
              T["anomalia"].equals(campione)
              and T["anomalia"][colonne].equals(T["anomalie_vere"].iloc[[0]][colonne].reset_index(drop=True)),
              ", ".join(f"{k} {v}" for k, v in T["anomalia"].iloc[0].items()) if len(T["anomalia"]) else "vuota")


def ripartizione_completa(T: dict[str, pd.DataFrame]) -> None:
    """La ripartizione del §3.6 rifatta qui da zero, con una tabella soci × ore (numpy),
    senza usare derivate.py, e confrontata con ripartizione_mensile.csv."""
    sezione("Ripartizione CER (§3.6): calcolo rifatto qui ora per ora")
    p = dict(zip(T["parametro"]["chiave"], num(T["parametro"], "valore")))
    socio = T["socio"].assign(sid=lambda x: x["id"].astype(int)).sort_values("sid").reset_index(drop=True)
    prod = T["produzione_oraria"]
    ore = np.sort(prod["ts"].unique()).astype("U20")
    n_s, n_h = len(socio), len(ore)

    # Consumi: una riga per socio, una colonna per ora
    c = T["consumo_orario"].assign(sid=lambda x: x["socio_id"].astype(int)).sort_values(["sid", "ts"])
    allineati = (len(c) == n_s * n_h and (c["sid"].to_numpy().reshape(n_s, n_h)[:, 0] == socio["sid"].to_numpy()).all()
                 and (c["ts"].to_numpy().reshape(n_s, n_h) == ore.astype(object)[None, :]).all())
    consumo = num(c, "kwh").to_numpy().reshape(n_s, n_h)
    socio_dal = (socio["data_adesione"] + "T00:00:00Z").to_numpy().astype("U20")
    attivo = ore[None, :] >= socio_dal[:, None]  # un socio conta dalle 00:00 UTC del giorno di adesione
    consumo_attivo = np.where(attivo, consumo, 0.0)

    prelevati = consumo_attivo.sum(axis=0)
    immessi = num(prod, "kwh").groupby(prod["ts"]).sum().reindex(ore.astype(object)).to_numpy()
    condivisi = np.minimum(immessi, prelevati)
    frazione = np.divide(condivisi, prelevati, out=np.zeros(n_h), where=prelevati > 0)
    quote = consumo_attivo * frazione[None, :]

    ok = (allineati and (quote.sum(axis=0) <= np.minimum(immessi, prelevati) + 1e-9).all()
          and (quote >= 0).all() and (quote <= consumo_attivo + 1e-12).all())
    dalla_produzione = int(((immessi > 0) & (immessi < prelevati)).sum())
    dai_consumi = int(((prelevati > 0) & (immessi >= prelevati)).sum())
    controlla("ogni ora: energia condivisa ≤ min(produzione, consumi dei soci attivi), e nessuna quota supera il consumo del socio",
              ok, f"ore con il sole: {italiano(dalla_produzione)} limitate dalla produzione, {italiano(dai_consumi)} dai consumi")

    # Somme per mese (UTC, §2)
    mese_ora = np.array([t[:7] + "-01" for t in ore])
    mesi = sorted(set(mese_ora))
    nel_mese = [mese_ora == m for m in mesi]
    quote_mese = np.stack([quote[:, s].sum(axis=1) for s in nel_mese], axis=1)  # soci × mesi
    consumo_mese = np.stack([consumo_attivo[:, s].sum(axis=1) for s in nel_mese], axis=1)
    condivisi_mese = np.array([condivisi[s].sum() for s in nel_mese])
    limite_mese = np.array([min(immessi[s].sum(), prelevati[s].sum()) for s in nel_mese])

    r = T["ripartizione_mensile"]
    kwh = num(r, "kwh_condivisi").to_numpy()
    righe_mese = r.groupby("mese").size().reindex(mesi, fill_value=0).to_numpy()
    soci_mese = pd.Series(kwh).groupby(r["mese"].to_numpy()).sum().reindex(mesi, fill_value=0.0).to_numpy()
    scarto = np.abs(soci_mese - condivisi_mese)
    controlla("ogni mese: somma dei soci = energia condivisa della comunità (somma delle ore di min(produzione, consumi))",
              (scarto <= righe_mese * 0.0005 + 1e-6).all() and (condivisi_mese <= limite_mese + 1e-6).all(),
              f"scarto massimo {scarto.max():.4f} kWh (arrotondamento a 3 decimali per socio); in 2 anni "
              f"{italiano(condivisi_mese.sum() / 1000, 1)} MWh condivisi, {condivisi_mese.sum() / immessi.sum() * 100:.1f}% della produzione")

    posizione_socio = {s: i for i, s in enumerate(socio["sid"])}
    posizione_mese = {m: j for j, m in enumerate(mesi)}
    i_s = r["socio_id"].astype(int).map(posizione_socio)
    j_m = r["mese"].map(posizione_mese)
    if i_s.isna().any() or j_m.isna().any():
        controlla("ripartizione_mensile: soci e mesi dentro il periodo", False, "righe con socio o mese sconosciuto")
        return
    i_s, j_m = i_s.to_numpy(int), j_m.to_numpy(int)
    scarto = np.abs(kwh - np.round(quote_mese[i_s, j_m], 3))
    controlla("ogni riga di ripartizione_mensile = quote ricalcolate qui, socio per socio e mese per mese",
              scarto.max() <= 0.001 + 1e-9, f"{italiano(len(r))} righe, scarto massimo {scarto.max():.4f} kWh")

    # Nessuna quota prima della data_adesione
    mese_adesione = dict(zip(socio["sid"], socio["data_adesione"].str.slice(0, 7) + "-01"))
    attese = {(s, m) for s, ma in mese_adesione.items() for m in mesi if m >= ma}
    presenti = list(zip(r["socio_id"].astype(int), r["mese"]))
    prima = [(s, m) for s, m in presenti if m < mese_adesione[s]]
    controlla("nessuna quota prima della data_adesione: una riga per socio e mese, dal mese di adesione in poi",
              not prima and len(presenti) == len(set(presenti)) and set(presenti) == attese,
              f"{italiano(len(attese))} righe attese, {italiano(len(presenti))} presenti, {len(prima)} prima dell'adesione")
    a_meta = socio[(socio["data_adesione"] >= config.CONFIGURAZIONI["completa"]["primo_ts"][:10])
                   & (socio["data_adesione"].str.slice(8, 10) != "01")]
    righe_r = dict(zip(presenti, kwh))
    in_piu, ok = 0.0, True
    for s in a_meta.itertuples():
        i, j = posizione_socio[s.sid], posizione_mese[mese_adesione[s.sid]]
        tutto_il_mese = (consumo[i, nel_mese[j]] * frazione[nel_mese[j]]).sum()  # se contasse dal 1° del mese
        valore = righe_r.get((s.sid, mese_adesione[s.sid]), np.nan)
        ok &= bool(valore <= consumo_mese[i, j] + 0.0005 and valore < tutto_il_mese)
        in_piu += tutto_il_mese - valore
    controlla("nel mese di adesione la quota conta solo dal giorno di adesione (soci entrati a metà mese)", ok,
              f"{len(a_meta)} soci; contando tutto il mese avrebbero avuto {italiano(in_piu, 1)} kWh in più")
    controlla("ogni quota mensile ≤ consumi del socio nello stesso mese, contati dalla sua adesione",
              (kwh <= consumo_mese[i_s, j_m] + 0.0005).all())

    inc, co2 = num(r, "incentivo_eur").to_numpy(), num(r, "co2_evitata_kg").to_numpy()
    tariffa = p["tariffa_premio_eur_kwh"] + p["valorizzazione_arera_eur_kwh"]
    controlla("incentivo_eur = kwh_condivisi × (tariffa premio + valorizzazione ARERA) e co2_evitata_kg = kwh_condivisi × fattore, "
              "mai negativi (§3.6)",
              (np.abs(inc - np.round(kwh * tariffa, 2)) < 0.005).all() and (np.abs(co2 - np.round(kwh * p["fattore_co2_kg_kwh"], 3)) < 0.0005).all()
              and (kwh >= 0).all() and (inc >= 0).all() and (co2 >= 0).all(),
              f"incentivo in 2 anni {italiano(inc.sum())} € ({tariffa:.3f} €/kWh)")


def riepilogo_completa(T: dict[str, pd.DataFrame]) -> None:
    """riepilogo_trimestri.csv rifatto qui dai CSV di partenza, trimestre per trimestre."""
    sezione("Riepilogo dei trimestri (file di lavoro per i verbali, §4)")
    R = T["riepilogo_trimestri"]
    controlla("8 trimestri, da nov-dic 2024 a lug-set 2026, ognuno con l'id del verbale che lo commenta (1-8)",
              R["verbale_id"].tolist() == [str(v) for v, *_ in derivate.TRIMESTRI]
              and R["trimestre"].tolist() == [t for _, t, *_ in derivate.TRIMESTRI])
    p = dict(zip(T["parametro"]["chiave"], num(T["parametro"], "valore")))
    socio = T["socio"]
    prod = T["produzione_oraria"].assign(kwh_n=lambda x: num(x, "kwh"))
    c = T["consumo_orario"].merge(socio[["id", "data_adesione"]], left_on="socio_id", right_on="id")
    c = c[c["ts"] >= c["data_adesione"] + "T00:00:00Z"]
    consumi_mese = num(c, "kwh").groupby(c["ts"].str.slice(0, 7) + "-01").sum()
    rip = T["ripartizione_mensile"].merge(socio[["id", "tipo"]], left_on="socio_id", right_on="id")
    pp = T["previsione_produzione"].merge(T["produzione_oraria"], on=["impianto_id", "ts"])
    pp["perso"] = num(pp, "kwh_previsti") - num(pp, "kwh")
    anomalie = T["anomalie_vere"]
    frase = re.compile(r"id (\d+) (\w+) impianto (\d+) \(.*?\) dal (\S+) al (\S+), perdita [\d.]+%, (-?[\d.]+) kWh persi nel trimestre")

    errori = {k: [] for k in ["energia", "ripartizione", "co2", "soci", "anomalie", "giorni"]}
    for (_, riga), (_, trimestre, inizio, fine) in zip(R.iterrows(), derivate.TRIMESTRI):
        v = lambda colonna: float(riga[colonna])  # noqa: E731
        t0, t1 = inizio + "T00:00:00Z", fine + "T00:00:00Z"
        pt = prod[(prod["ts"] >= t0) & (prod["ts"] < t1)]
        per_impianto = pt.groupby("impianto_id")["kwh_n"].sum()
        mesi = [m for m in consumi_mese.index if inizio <= m < fine]
        if (any(abs(v(f"produzione_impianto_{i}_kwh") - per_impianto[str(i)]) > 0.0005 for i in range(1, 9))
                or abs(v("produzione_kwh") - pt["kwh_n"].sum()) > 0.0005 or abs(v("consumi_kwh") - consumi_mese[mesi].sum()) > 0.0005):
            errori["energia"].append(trimestre)

        rt = rip[rip["mese"].isin(mesi)]
        per_tipo = num(rt, "incentivo_eur").groupby(rt["tipo"]).sum()
        if (abs(v("kwh_condivisi") - num(rt, "kwh_condivisi").sum()) > 0.0005 or abs(v("incentivo_eur") - num(rt, "incentivo_eur").sum()) > 0.005
                or any(abs(v(f"incentivo_{col}_eur") - per_tipo.get(tipo, 0.0)) > 0.005
                       for tipo, col in [("famiglia", "famiglie"), ("impresa", "imprese"), ("ente", "enti")])
                or abs(v("incentivo_famiglie_eur") + v("incentivo_imprese_eur") + v("incentivo_enti_eur") - v("incentivo_eur")) > 0.015
                or abs(v("co2_evitata_condivisa_kg") - num(rt, "co2_evitata_kg").sum()) > 0.0005):
            errori["ripartizione"].append(trimestre)
        if abs(v("co2_evitata_kg") - v("produzione_kwh") * p["fattore_co2_kg_kwh"]) > 0.001:
            errori["co2"].append(trimestre)

        attivi = int((socio["data_adesione"] < fine).sum())
        nuovi = int(((socio["data_adesione"] >= inizio) & (socio["data_adesione"] < fine)).sum())
        if (int(riga["soci_attivi"]), int(riga["nuovi_soci"])) != (attivi, nuovi):
            errori["soci"].append(trimestre)

        dentro = anomalie[(anomalie["inizio"] < t1) & (anomalie["fine"] > t0)]
        trovate = frase.findall(riga["anomalie_dettaglio"])
        frasi = riga["anomalie_dettaglio"].split("; ") if riga["anomalie_dettaglio"] else []
        ok = (all(int(riga[f"anomalie_{tipo}"]) == (dentro["tipo"] == tipo).sum() for tipo in derivate.TIPI_ANOMALIA)
              and sorted(i for i, *_ in trovate) == sorted(dentro["id"]) and len(frasi) == len(trovate))
        for id_, tipo, imp, dal, al, persi in trovate:
            a = dentro[dentro["id"] == id_]
            ore = (pp["impianto_id"] == imp) & (pp["ts"] >= max(dal, t0)) & (pp["ts"] < min(al, t1))
            ok &= (len(a) == 1 and (a.iloc[0]["tipo"], a.iloc[0]["impianto_id"], a.iloc[0]["inizio"], a.iloc[0]["fine"]) == (tipo, imp, dal, al)
                   and float(persi) >= 0 and abs(float(persi) - pp.loc[ore, "perso"].sum()) <= 0.0005)
        if not ok:
            errori["anomalie"].append(trimestre)

        giorni = pt.groupby(pt["ts"].str.slice(0, 10))["kwh_n"].sum()
        if (riga["giorno_max_produzione"], riga["giorno_min_produzione"]) != (giorni.idxmax(), giorni.idxmin()) or \
                abs(v("kwh_giorno_max") - giorni.max()) > 0.0005 or abs(v("kwh_giorno_min") - giorni.min()) > 0.0005:
            errori["giorni"].append(trimestre)

    controlla("produzione per impianto e totale, consumi dei soci attivi = somme di produzione_oraria e consumo_orario del trimestre",
              not errori["energia"], ", ".join(errori["energia"]))
    controlla("energia condivisa, incentivi (totale e per tipo di socio) e CO2 della parte condivisa = somme di ripartizione_mensile",
              not errori["ripartizione"], ", ".join(errori["ripartizione"]))
    controlla("co2_evitata_kg = produzione totale × fattore (KPI di comunità, §3.6)", not errori["co2"], ", ".join(errori["co2"]))
    controlla("soci attivi (aderenti entro fine trimestre) e nuovi soci coerenti con socio.data_adesione",
              not errori["soci"] and R["soci_attivi"].iloc[-1] == str(len(socio)),
              f"a fine periodo {R['soci_attivi'].iloc[-1]} soci attivi" + (f"; diversi: {', '.join(errori['soci'])}" if errori["soci"] else ""))
    controlla("anomalie per tipo = quelle di anomalie_vere che toccano il trimestre; kWh persi = attesa − reale nel trimestre",
              not errori["anomalie"], ", ".join(errori["anomalie"])
              or f"{sum(len(frase.findall(t)) for t in R['anomalie_dettaglio'])} anomalie elencate negli 8 trimestri")
    controlla("giorni di massima e minima produzione della comunità (in UTC)", not errori["giorni"], ", ".join(errori["giorni"]))


def leggi_schema(cartella: Path) -> dict[str, list[str]]:
    """{tabella: [colonne in ordine]} dai CREATE TABLE delle migrazioni (parte "migrate:up").

    Se una migrazione cambia una tabella con ALTER TABLE, questa lettura semplice non
    basta più: il programma si ferma, così il controllo si aggiorna.
    """
    schema = {}
    for percorso in sorted(cartella.glob("*.sql")):
        su = percorso.read_text(encoding="utf-8").split("-- migrate:down")[0]
        if re.search(r"\bALTER\s+TABLE\b", su, flags=re.I):
            raise ValueError(f"{percorso.name} contiene ALTER TABLE: aggiornare leggi_schema")
        for nome, corpo in re.findall(r"CREATE TABLE (\w+) \((.*?)\n\);", su, flags=re.S):
            schema[nome] = [m.group(1) for riga in corpo.splitlines()
                            if (m := re.match(r"\s*([a-z_][a-z0-9_]*)\s+(?:integer|text|double precision|date|timestamptz|numeric|boolean|bigint)\b", riga))]
    return schema


def seed_completa(cartella: Path) -> None:
    sezione("Seed del database: db/seed/carica.sql e schema in db/migrations")
    testo = CARICA_SQL.read_text(encoding="utf-8")
    copie = re.findall(r"^\\copy\s+(\w+)\s+FROM\s+'/csv/([\w.]+)'", testo, flags=re.M)
    tabelle = [t for t, _ in copie]
    controlla("carica.sql carica 13 CSV, ognuno con il nome della sua tabella, cioè le tabelle di config.TABELLE_DB",
              len(copie) == 13 and all(f == f"{t}.csv" for t, f in copie) and sorted(tabelle) == sorted(config.TABELLE_DB),
              f"{len(copie)} file: " + ", ".join(tabelle))
    migrazioni = sorted(MIGRAZIONI.glob("*.sql"))
    schema = leggi_schema(MIGRAZIONI)
    print(f"  schema letto da {', '.join(m.name for m in migrazioni)}: {len(schema)} tabelle")
    for t in tabelle:
        percorso = cartella / f"{t}.csv"
        if not percorso.exists():
            controlla(f"{t}.csv: c'è, con le colonne nell'ordine della tabella (HEADER match)", False, "manca il file")
            continue
        with open(percorso, encoding="utf-8", newline="") as f:
            intestazione = next(csv.reader(f))
        colonne = schema.get(t)
        controlla(f"{t}.csv: c'è, con le colonne nell'ordine della tabella (HEADER match)", intestazione == colonne,
                  f"{len(intestazione)} colonne" if intestazione == colonne else f"CSV {intestazione}, schema {colonne}")


def main_completa(args: argparse.Namespace) -> None:
    conf = config.CONFIGURAZIONI["completa"]
    cartella = conf["cartella"]
    print("Controlli del dataset completo (impianti, soci, meteo, produzione, anomalie, consumi, bollette, "
          f"tabelle calcolate, ripartizione, riepilogo dei trimestri, seed), in {cartella}")
    if not args.senza_rigenerare:
        riproducibilita("completa", cartella)
    T = {f.stem: pd.read_csv(f, dtype=str, keep_default_na=False) for f in sorted(cartella.glob("*.csv"))}

    stato = {}
    for passo in [lambda: file_e_righe_completa(T), lambda: formato(cartella), lambda: serie_complete_completa(T, conf),
                  lambda: integrita_completa(T), lambda: anagrafiche_completa(T, conf), lambda: meteo_completa(T),
                  lambda: stato.update(d=produzione_completa(T, conf)), lambda: anomalie_completa(T, stato["d"]),
                  lambda: consumi_completa(T), lambda: bollette_completa(T),
                  lambda: tabelle_calcolate_completa(T, stato["d"]), lambda: ripartizione_completa(T),
                  lambda: riepilogo_completa(T), lambda: seed_completa(cartella), lambda: confronto_campione(T)]:
        try:
            passo()
        except Exception as errore:  # un errore in una sezione non deve nascondere le altre
            controlla("sezione interrotta da un errore", False, f"{type(errore).__name__}: {errore}")

    sezione("Grafici di controllo")
    grafici = grafici_completa(T, stato["d"]) if "d" in stato else []
    for percorso in [*grafici, grafico_consumi(T)]:
        print(f"  {percorso.relative_to(config.CARTELLA_DATA)}")
    elenco_file(cartella, T)

    falliti = [nome for nome, ok in ESITI if not ok]
    print(f"\nESITO: {len(ESITI) - len(falliti)} controlli ok su {len(ESITI)}" + (f", FALLITI: {len(falliti)}" if falliti else ""))
    for nome in falliti:
        print(f"  - {nome}")
    sys.exit(1 if falliti else 0)


def main() -> None:
    parser = argparse.ArgumentParser(description="Controlli di qualità del dataset UnderTheSun (§6)")
    parser.add_argument("--config", choices=list(config.CONFIGURAZIONI), required=True)
    parser.add_argument("--senza-rigenerare", action="store_true", help="salta i due rilanci di genera.py")
    args = parser.parse_args()
    if args.config == "completa":
        main_completa(args)
        return
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
