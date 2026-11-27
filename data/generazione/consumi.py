"""Consumi: profili orari per tipo di socio -> consumo_orario (guida §3.4 e §7).

Passi per ogni socio:
1. pesi orari in ora italiana, secondo profilo e tipo di giorno (feriale, sabato,
   domenica o festivo; per la scuola anche i giorni di lezione);
2. abitudini spostate di -1, 0 o +1 ora;
3. passaggio a UTC;
4. rumore orario (media 1, deviazione 0,15, mai sotto zero);
5. riscalatura:
   - campione, volumi provvisori (§7): il totale dal 1/9/2025 al 31/8/2026 è
     volume annuo × scala; poi si taglia il periodo richiesto;
   - dataset completo, volumi ARERA (§3.4): il totale di ogni mese (in UTC, come
     le bollette) è la media ARERA 2025 di quel mese × scala.

Le famiglie del dataset completo usano la forma oraria di ARERA (Torino, residenti,
1,5-3 kW: 24 valori per mese e tipo di giorno). Nel campione resta il profilo
FAMIGLIA scritto a mano, così data/esempi/ non cambia.

Dal generatore del socio si estraggono, sempre in quest'ordine: scala,
spostamento, rumore (config.rng_socio). Il rumore copre tutto il periodo del
dataset completo, così le ore di giugno ricevono lo stesso rumore nel campione
e nel dataset completo.
"""

import csv
import functools
import io
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import date, timedelta

import holidays
import numpy as np
import pandas as pd

import anagrafiche
import config

FUSO = "Europe/Rome"
DEVIAZIONE_RUMORE = 0.15

# --- ARERA, Monitoraggio retail 2025, provincia di Torino (§3.4) --------------
# Gli ZIP si scaricano a mano in cache/arera/domestici/ e cache/arera/non-domestici/.
# estrai_arera() li legge una volta sola, senza scompattarli, e salva le righe
# che servono in FILE_ARERA; da lì in poi si rilegge solo quel CSV.
# Per rifare l'estrazione (per esempio se cambia una classe di potenza qui sotto)
# basta cancellare FILE_ARERA.

CARTELLA_ARERA = config.CARTELLA_CACHE / "arera"
FILE_ARERA = CARTELLA_ARERA / "arera_torino_2025.csv"
COLONNE_ARERA = ["cliente", "ateco", "classe_potenza", "mese", "tipo_giorno", "ora", "grandezza", "valore", "file"]
PROVINCIA = "Torino"

# Famiglie: residenti, classe 1,5-3 kW (il contratto da 3 kW, il più diffuso), tutti i mercati
FILE_DOMESTICI_MENSILE = "Dati prelievo clienti domestici Provinciale 2025.xlsx"
FILE_DOMESTICI_ORARIO = "dati prelievo orario per provincia1_5_a_3 anno 2025TOT.xlsx"
CLASSE_FAMIGLIE = "1,5-3"
TIPI_GIORNO_ARERA = {"Giorno feriale": "feriale", "Sabato": "sabato", "Domenica": "domenica"}

# Imprese ed enti: classe di potenza BT per profilo (decisa il 27/11/2026). I file
# ARERA non dicono quanti clienti ci sono in ogni classe, quindi la regola è:
# negozi 6-10 kW; forni, cucina o macchinari >10 kW; enti (edifici grandi) >16,5 kW.
CLASSI_NON_DOMESTICI = {
    "bar": "6-10", "alimentari": "6-10", "parrucchiere": "6-10",
    "ristorante": ">10", "panificio": ">10", "officina": ">10",
    "scuola": ">16,5", "uffici_comunali": ">16,5", "rsa": ">16,5", "impianto_sportivo": ">16,5",
    "biblioteca": "6-10",
}
# Biblioteca (91.01): a Torino c'è una sola classe con 12 mesi (6-10 kW), ma da luglio
# raddoppia perché i clienti sono pochi. Si usa il suo totale annuo, distribuito sui
# mesi con la forma degli uffici comunali (84.11) della stessa classe.
FORMA_MESI_BIBLIOTECA = ("84.11", "6-10")
# Un CSV ARERA per ogni classe di potenza: nome del file e valore della colonna "Tariffa potenza kW"
FILE_NON_DOMESTICI = {
    "6-10": ("BTA4_6_potenza_10.csv", "BTA4: 6 <>= 10"),
    ">10": ("BTA5_potenza_10.csv", "BTA5: >10"),
    ">16,5": ("BTA6_potenza_16_5.csv", "BTA6: potenza disponibile >16,5"),
}
# Codici ATECO del §1.3 (classificazione 2007): nel file 2025 ci sono in tutti i 12 mesi
ATECO = {profilo: codice for profilo, codice, *_ in [*anagrafiche.IMPRESE, *anagrafiche.ENTI]}

# --- Volumi provvisori (§7) -------------------------------------------------

VOLUMI_PROVVISORI_KWH_ANNO = {"famiglia": 2700, "impresa": 15000, "ente": 40000}
# L'anno su cui si distribuisce il volume: un anno scolastico intero (in UTC, §2)
ANNO_VOLUMI = ("2025-09-01T00:00:00Z", "2026-08-31T23:00:00Z")

# --- Famiglia (§3.4): pesi relativi per ora italiana 0-23 ----------------------

FAMIGLIA = {
    #             0-5         6       7-8           9-11          12-13         14-17               18      19-21               22      23
    "feriale": [0.40] * 6 + [0.60] + [1.00] * 2 + [0.55] * 3 + [0.70] * 2 + [0.55] * 4 + [0.85] + [1.30] * 3 + [1.00] + [0.65],
    #             0-6         7       8       9-11          12-13         14-17               18      19-21               22      23
    "sabato":  [0.40] * 7 + [0.55] + [0.90] + [0.90] * 3 + [1.00] * 2 + [0.70] * 4 + [0.90] + [1.25] * 3 + [1.00] + [0.70],
    "festivo": [0.40] * 7 + [0.55] + [0.70] + [0.90] * 3 + [1.15] * 2 + [0.70] * 4 + [0.90] + [1.25] * 3 + [1.00] + [0.70],
}

# --- Imprese ed enti (tabella approvata il 19/11/2026) -----------------------
# Orari in ora italiana: (dalle, alle, livello). "8, 13" vuol dire le ore che
# iniziano alle 8, 9, 10, 11 e 12. Fuori orario resta il consumo di base.

ORARI = {
    "bar": {"base": 0.25, "feriale": [(6, 20, 1.0)], "sabato": [(6, 20, 1.0)], "festivo": [(7, 13, 1.0)]},
    "ristorante": {
        "base": 0.25,
        "feriale": [(11, 15, 1.0), (19, 23, 1.0)],
        "sabato": [(11, 15, 1.0), (19, 23, 1.0)],
        "festivo": [(11, 15, 1.0), (19, 23, 1.0)],
        "chiuso_il_lunedi": True,
    },
    "alimentari": {"base": 0.40, "feriale": [(8, 13, 1.0), (15, 19, 1.0)], "sabato": [(8, 13, 1.0), (15, 19, 1.0)], "festivo": []},
    "panificio": {
        "base": 0.15,
        "feriale": [(3, 7, 1.0), (7, 13, 0.4), (16, 19, 0.4)],  # forno, poi negozio
        "sabato": [(3, 7, 1.0), (7, 13, 0.4), (16, 19, 0.4)],
        "festivo": [(4, 7, 1.0), (7, 12, 0.4)],
    },
    "officina": {"base": 0.10, "feriale": [(8, 18, 1.0)], "sabato": [], "festivo": []},
    "parrucchiere": {"base": 0.10, "feriale": [(9, 19, 1.0)], "sabato": [(9, 19, 1.0)], "festivo": [], "chiuso_il_lunedi": True},
    "scuola": {"base": 0.15, "feriale": [(8, 16, 1.0)], "sabato": [], "festivo": [], "solo_giorni_di_lezione": True},
    "uffici_comunali": {
        "base": 0.15,
        "feriale": [(8, 14, 1.0)],
        "sabato": [],
        "festivo": [],
        "pomeriggi": {1: [(14, 18, 1.0)], 3: [(14, 18, 1.0)]},  # martedì e giovedì
    },
    "biblioteca": {"base": 0.10, "feriale": [(10, 19, 1.0)], "sabato": [(9, 13, 1.0)], "festivo": [], "chiuso_il_lunedi": True},
    "rsa": {"base": 0.60, "feriale": [(7, 21, 1.0)], "sabato": [(7, 21, 1.0)], "festivo": [(7, 21, 1.0)]},
    "impianto_sportivo": {"base": 0.10, "feriale": [(16, 23, 1.0)], "sabato": [(9, 20, 1.0)], "festivo": [(9, 13, 1.0)]},
}

# --- Calendario scolastico della Regione Piemonte (§3.4) ----------------------
# Date incluse agli estremi, come nel calendario ufficiale. Le lezioni sono dal
# lunedì al venerdì; i festivi nazionali vengono da holidays.
# 2024/25: DGR 4-8323 del 20 marzo 2024, date come nella guida (§3.4). Serve al
#   dataset completo, che inizia il 1/11/2024. Il 1/11, il 25/4, il 1/5 e il 2/6
#   sono anche festivi nazionali: si elencano lo stesso, come nel calendario.
# 2025/26: https://www.regione.piemonte.it/web/node/20460 (verificato il 19/11/2026).
# 2026/27: https://www.regione.piemonte.it/web/pinforma/notizie/calendario-scolastico-2026-2027
#   (verificato il 19/11/2026: le lezioni iniziano lunedì 14 settembre 2026).
#   Al campione serve perché le prime ore del 1/9/2026, in ora italiana, chiudono
#   l'anno dei volumi provvisori.
CALENDARI_SCOLASTICI = {
    "2024/25": {
        "anno": (date(2024, 9, 1), date(2025, 8, 31)),
        "lezioni": (date(2024, 9, 11), date(2025, 6, 7)),
        "sospensioni": [
            (date(2024, 11, 1), date(2024, 11, 1)),  # Ognissanti
            (date(2024, 12, 23), date(2025, 1, 6)),  # Natale
            (date(2025, 3, 1), date(2025, 3, 4)),  # Carnevale
            (date(2025, 4, 17), date(2025, 4, 22)),  # Pasqua
            (date(2025, 4, 25), date(2025, 4, 25)),  # Festa della Liberazione
            (date(2025, 5, 1), date(2025, 5, 3)),  # Festa del Lavoro e ponte
            (date(2025, 6, 2), date(2025, 6, 2)),  # Festa della Repubblica
        ],
    },
    "2025/26": {
        "anno": (date(2025, 9, 1), date(2026, 8, 31)),
        "lezioni": (date(2025, 9, 10), date(2026, 6, 10)),
        "sospensioni": [
            (date(2025, 12, 22), date(2026, 1, 6)),  # Natale
            (date(2026, 2, 14), date(2026, 2, 17)),  # Carnevale
            (date(2026, 4, 2), date(2026, 4, 7)),  # Pasqua
            (date(2026, 5, 2), date(2026, 5, 2)),  # ponte Festa del Lavoro
            (date(2026, 6, 1), date(2026, 6, 1)),  # ponte Festa della Repubblica
        ],
    },
    "2026/27": {
        "anno": (date(2026, 9, 1), date(2027, 8, 31)),
        "lezioni": (date(2026, 9, 14), date(2027, 6, 10)),
        "sospensioni": [
            (date(2026, 12, 7), date(2026, 12, 8)),  # ponte dell'Immacolata
            (date(2026, 12, 23), date(2027, 1, 6)),  # Natale
            (date(2027, 2, 6), date(2027, 2, 10)),  # Carnevale
            (date(2027, 3, 25), date(2027, 3, 30)),  # Pasqua
        ],
    },
}

FESTIVI = holidays.Italy(years=range(2024, 2027))  # solo festività nazionali


def tipo_di_giorno(giorno: date) -> str:
    """feriale, sabato o festivo (domenica o festività nazionale)."""
    if giorno in FESTIVI or giorno.weekday() == 6:
        return "festivo"
    return "sabato" if giorno.weekday() == 5 else "feriale"


def giorno_di_lezione(giorno: date) -> bool:
    """True se la scuola primaria fa lezione in quel giorno."""
    for calendario in CALENDARI_SCOLASTICI.values():
        inizio_anno, fine_anno = calendario["anno"]
        if inizio_anno <= giorno <= fine_anno:
            inizio, fine = calendario["lezioni"]
            sospeso = any(dal <= giorno <= al for dal, al in calendario["sospensioni"])
            return inizio <= giorno <= fine and tipo_di_giorno(giorno) == "feriale" and not sospeso
    raise NotImplementedError(f"Manca il calendario scolastico che contiene il {giorno} (§3.4)")


def _fasce(intervalli: list[tuple[int, int, float]], base: float) -> np.ndarray:
    pesi = np.full(24, base)
    for dalle, alle, livello in intervalli:
        pesi[dalle:alle] = np.maximum(pesi[dalle:alle], livello)
    return pesi


def pesi_del_giorno(profilo: str, giorno: date, forma_famiglia: dict | None = None) -> np.ndarray:
    """I 24 pesi di un profilo in un giorno, per ora italiana.

    forma_famiglia (dataset completo): la forma oraria ARERA delle famiglie, per
    mese e tipo di giorno. ARERA ha solo feriale, sabato e domenica: i festivi
    usano la domenica. Senza forma_famiglia si usa il profilo FAMIGLIA (campione).
    """
    tipo = tipo_di_giorno(giorno)
    if profilo == "famiglia":
        if forma_famiglia is not None:
            return forma_famiglia[(giorno.month, "domenica" if tipo == "festivo" else tipo)]
        return np.array(FAMIGLIA[tipo])
    orari = ORARI[profilo]
    chiuso = np.full(24, orari["base"])
    if orari.get("chiuso_il_lunedi") and tipo == "feriale" and giorno.weekday() == 0:
        return chiuso
    if orari.get("solo_giorni_di_lezione") and not giorno_di_lezione(giorno):
        return chiuso
    intervalli = list(orari[tipo])
    if tipo == "feriale":
        intervalli += orari.get("pomeriggi", {}).get(giorno.weekday(), [])
    return _fasce(intervalli, orari["base"])


def pesi_orari(profilo: str, ore_utc: pd.DatetimeIndex, spostamento: int, forma_famiglia: dict | None = None) -> np.ndarray:
    """Pesi per ogni ora UTC. Si parte dall'ora UTC, si toglie lo spostamento
    delle abitudini e si guarda che ora è in Italia: così i giorni del cambio
    d'ora (23 o 25 ore) sono gestiti da pandas senza ore mancanti o doppie."""
    locali = (ore_utc - pd.Timedelta(hours=spostamento)).tz_convert(FUSO)
    giorni = locali.date
    pesi_per_giorno = {g: pesi_del_giorno(profilo, g, forma_famiglia) for g in set(giorni)}
    return np.array([pesi_per_giorno[g][h] for g, h in zip(giorni, locali.hour)])


def ore(primo_ts: str, ultimo_ts: str) -> pd.DatetimeIndex:
    return pd.date_range(primo_ts, ultimo_ts, freq="h")


@functools.cache
def testo_ore(primo_ts: str, ultimo_ts: str) -> np.ndarray:
    """Le ore come testo ("2026-06-01T10:00:00Z"), calcolate una volta sola e
    condivise da tutti i soci: con 240 soci e 17.520 ore si risparmia memoria."""
    return np.asarray(ore(primo_ts, ultimo_ts).strftime("%Y-%m-%dT%H:%M:%SZ"), dtype=object)


ORE_COMPLETE = ore(config.CONFIGURAZIONI["completa"]["primo_ts"], config.CONFIGURAZIONI["completa"]["ultimo_ts"])


# --- Lettura dei file ARERA (§3.4) ---------------------------------------------

_XLSX = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _cerca_nello_zip(cartella, nome_file: str) -> tuple:
    """(ZIP, nome interno) del file nome_file, cercato in tutti gli ZIP della cartella."""
    for percorso in sorted(cartella.glob("*.zip")):
        with zipfile.ZipFile(percorso) as zf:
            for interno in zf.namelist():
                if interno.split("/")[-1] == nome_file:
                    return percorso, interno
    raise FileNotFoundError(f"{nome_file} non è in nessuno ZIP di {cartella}: scaricalo dal sito ARERA (§3.4)")


def _leggi_dallo_zip(cartella, nome_file: str) -> bytes:
    percorso, interno = _cerca_nello_zip(cartella, nome_file)
    with zipfile.ZipFile(percorso) as zf:
        return zf.read(interno)


def _righe_xlsx(dati: bytes):
    """Righe del primo foglio di un file xlsx, come liste di testi.

    Basta la libreria standard: un xlsx è uno ZIP di file XML. I testi stanno in
    xl/sharedStrings.xml, le celle in xl/worksheets/sheet1.xml; la cella "C7" è
    la terza colonna della riga 7.
    """
    xlsx = zipfile.ZipFile(io.BytesIO(dati))
    testi = []
    for _, el in ET.iterparse(xlsx.open("xl/sharedStrings.xml")):
        if el.tag == _XLSX + "si":
            testi.append("".join(t.text or "" for t in el.iter(_XLSX + "t")))
            el.clear()
    for _, el in ET.iterparse(xlsx.open("xl/worksheets/sheet1.xml")):
        if el.tag != _XLSX + "row":
            continue
        celle = {}
        for c in el.iter(_XLSX + "c"):
            lettere = re.match(r"[A-Z]+", c.get("r")).group()
            colonna = 0
            for lettera in lettere:
                colonna = colonna * 26 + ord(lettera) - ord("A") + 1
            v = c.find(_XLSX + "v")
            testo = "" if v is None else (v.text or "")
            if v is not None and c.get("t") == "s":
                testo = testi[int(testo)]
            celle[colonna - 1] = testo.strip()
        el.clear()
        yield [celle.get(i, "") for i in range(max(celle) + 1)] if celle else []


def _mese_excel(valore: str) -> int:
    """'45658' -> 1. Nei file domestici il mese è una data di Excel (giorni dal
    30/12/1899): 45658 è il 1/1/2025."""
    giorno = date(1899, 12, 30) + timedelta(days=int(float(valore)))
    if giorno.year != 2025 or giorno.day != 1:
        raise ValueError(f"Mese ARERA inatteso: {valore} = {giorno}")
    return giorno.month


def _riga(cliente: str, ateco: str, classe: str, mese: int, grandezza: str, valore: float, file: str,
          tipo_giorno: str = "", ora=pd.NA) -> dict:
    return {"cliente": cliente, "ateco": ateco, "classe_potenza": classe, "mese": mese, "tipo_giorno": tipo_giorno,
            "ora": ora, "grandezza": grandezza, "valore": valore, "file": file}


def _domestici() -> list[dict]:
    """Famiglie di Torino, residenti, 1,5-3 kW, tutti i mercati (riga "Tutti").

    - file mensile: kWh medi del mese e quote F1/F2/F3 (da 0 a 1);
    - file orario: kWh medi in ogni ora, per mese e tipo di giorno. "Ora1" è
      l'ora 00-01 in ora italiana: con questa lettura le quote F1/F2/F3 ricavate
      dalla forma oraria tornano con quelle del file mensile entro 1 punto.
    Le righe "2025" (totale o media dell'anno) si saltano.
    """
    cartella, classe_arera = CARTELLA_ARERA / "domestici", "1.5<potenza_impegnata<=3"
    righe = []

    gen = _righe_xlsx(_leggi_dallo_zip(cartella, FILE_DOMESTICI_MENSILE))
    i = {nome: posizione for posizione, nome in enumerate(h.strip() for h in next(gen))}
    for r in gen:
        if (r[i["Provincia"]], r[i["Tipo Mercato"]], r[i["Residenza"]], r[i["Classe potenza"]]) != (
                PROVINCIA, "Tutti", "Residente", classe_arera) or r[i["Anno Mese"]] == "2025":
            continue
        mese = _mese_excel(r[i["Anno Mese"]])
        for grandezza, colonna in [("kwh_mese", "medio consumo mensile"), ("quota_f1", "F1(%)"),
                                   ("quota_f2", "F2(%)"), ("quota_f3", "F3(%)")]:
            righe.append(_riga("domestico", "", CLASSE_FAMIGLIE, mese, grandezza, float(r[i[colonna]]), FILE_DOMESTICI_MENSILE))

    gen = _righe_xlsx(_leggi_dallo_zip(cartella, FILE_DOMESTICI_ORARIO))
    i = {nome: posizione for posizione, nome in enumerate(h.strip() for h in next(gen))}
    for r in gen:
        if (r[i["Provincia"]], r[i["Tipo mercato"]], r[i["Residenza"]], r[i["Classe_potenza"]]) != (
                PROVINCIA, "Tutti", "Residente", classe_arera) or r[i["Anno Mese"]] == "2025":
            continue
        ora = int(re.fullmatch(r"Ora(\d+)", r[i["Orario"]]).group(1)) - 1
        righe.append(_riga("domestico", "", CLASSE_FAMIGLIE, _mese_excel(r[i["Anno Mese"]]), "kwh_ora",
                           float(r[i["Prelievo medio Orario Provinciale (kWh)"]]), FILE_DOMESTICI_ORARIO,
                           tipo_giorno=TIPI_GIORNO_ARERA[r[i["Working Day"]]], ora=ora))
    return righe


def _combinazioni_non_domestici() -> set[tuple[str, str]]:
    """Le coppie (codice ATECO, classe di potenza) che servono."""
    return {(ATECO[profilo], classe) for profilo, classe in CLASSI_NON_DOMESTICI.items()} | {FORMA_MESI_BIBLIOTECA}


def _non_domestici() -> list[dict]:
    """Imprese ed enti di Torino: kWh medi del mese per codice ATECO e classe di potenza.

    I CSV hanno ";" come separatore e la virgola nei decimali. Il codice ATECO è
    la prima parola della colonna "Classe ATECO" ("56.30  Attività di ...").
    """
    servono = _combinazioni_non_domestici()
    righe = []
    for classe in sorted({c for _, c in servono}):
        nome, etichetta = FILE_NON_DOMESTICI[classe]
        testo = _leggi_dallo_zip(CARTELLA_ARERA / "non-domestici", nome).decode("utf-8-sig", errors="replace")
        lettore = csv.reader(io.StringIO(testo, newline=""), delimiter=";")
        i = {nome_colonna: posizione for posizione, nome_colonna in enumerate(h.strip() for h in next(lettore))}
        for r in lettore:
            if r[i["Provincia"]] != PROVINCIA:
                continue
            codice = (r[i["Classe ATECO"]].split() or [""])[0]
            if (codice, classe) not in servono:
                continue
            if r[i["Tariffa potenza kW"]] != etichetta or r[i["Anno"]] != "2025":
                raise ValueError(f"{nome}: riga inattesa {r}")
            righe.append(_riga("non_domestico", codice, classe, int(r[i["Mese"]]), "kwh_mese",
                               float(r[i["Prelievo medio mensile"]].replace(",", ".")), nome))
    return righe


def _verifica_arera(df: pd.DataFrame) -> None:
    """Le righe estratte devono bastare al generatore; se no si ferma tutto."""
    rifai = f"Cancella {FILE_ARERA} per rifare l'estrazione dagli ZIP."
    chiave = ["cliente", "ateco", "classe_potenza", "mese", "tipo_giorno", "ora", "grandezza"]
    if df.duplicated(chiave).any():
        raise ValueError(f"ARERA: righe doppie in {FILE_ARERA.name}")
    dom = df[df["cliente"] == "domestico"]
    for grandezza, attese in [("kwh_mese", 12), ("quota_f1", 12), ("quota_f2", 12), ("quota_f3", 12), ("kwh_ora", 12 * 3 * 24)]:
        if (dom["grandezza"] == grandezza).sum() != attese:
            raise ValueError(f"ARERA famiglie: servono {attese} righe '{grandezza}'. {rifai}")
    quote = dom[dom["grandezza"].str.startswith("quota_")].groupby("mese")["valore"].sum()
    if (quote - 1).abs().max() > 0.001:
        raise ValueError("ARERA famiglie: le quote F1/F2/F3 di un mese non sommano a 1")
    nd = df[df["cliente"] == "non_domestico"]
    for ateco, classe in sorted(_combinazioni_non_domestici()):
        mesi = nd[(nd["ateco"] == ateco) & (nd["classe_potenza"] == classe)]
        if sorted(mesi["mese"]) != list(range(1, 13)) or not (mesi["valore"] > 0).all():
            raise ValueError(f"ARERA: per ATECO {ateco}, classe {classe} kW servono 12 mesi con valori positivi. {rifai}")
    if not (df["valore"] > 0).all():
        raise ValueError("ARERA: ci sono valori nulli o negativi")


def estrai_arera() -> pd.DataFrame:
    """Legge gli ZIP ARERA (senza scompattarli) e scrive FILE_ARERA con le sole righe che servono."""
    df = pd.DataFrame(_domestici() + _non_domestici(), columns=COLONNE_ARERA)
    df["ora"] = df["ora"].astype("Int64")
    df = df.sort_values(["cliente", "ateco", "classe_potenza", "grandezza", "mese", "tipo_giorno", "ora"]).reset_index(drop=True)
    _verifica_arera(df)
    FILE_ARERA.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(FILE_ARERA, index=False, encoding="utf-8", lineterminator="\n", na_rep="")
    return df


@functools.cache
def leggi_arera() -> pd.DataFrame:
    """Le righe ARERA che servono: dal CSV piccolo se c'è, altrimenti dagli ZIP."""
    if not FILE_ARERA.exists():
        print(f"  estraggo le righe di Torino dagli ZIP ARERA -> {FILE_ARERA.relative_to(config.CARTELLA_DATA)}")
        estrai_arera()
    df = pd.read_csv(FILE_ARERA, dtype=str, keep_default_na=False)
    if list(df.columns) != COLONNE_ARERA:
        raise ValueError(f"{FILE_ARERA.name}: colonne {list(df.columns)}, attese {COLONNE_ARERA}")
    df["mese"] = df["mese"].astype(int)
    df["ora"] = pd.to_numeric(df["ora"]).astype("Int64")
    df["valore"] = df["valore"].astype(float)
    _verifica_arera(df)
    return df


@functools.cache
def volumi_mensili() -> dict[str, np.ndarray]:
    """kWh medi di ogni mese (gennaio-dicembre 2025) per profilo, da ARERA (§3.4, passo 1)."""
    a = leggi_arera()
    mensili = a[a["grandezza"] == "kwh_mese"]

    def mesi(cliente: str, ateco: str, classe: str) -> np.ndarray:
        sel = mensili[(mensili["cliente"] == cliente) & (mensili["ateco"] == ateco) & (mensili["classe_potenza"] == classe)]
        return sel.set_index("mese")["valore"].reindex(range(1, 13)).to_numpy()

    volumi = {"famiglia": mesi("domestico", "", CLASSE_FAMIGLIE)}
    for profilo, classe in CLASSI_NON_DOMESTICI.items():
        volumi[profilo] = mesi("non_domestico", ATECO[profilo], classe)
    forma = mesi("non_domestico", *FORMA_MESI_BIBLIOTECA)
    volumi["biblioteca"] = volumi["biblioteca"].sum() * forma / forma.sum()
    return volumi


@functools.cache
def forma_famiglia_arera() -> dict[tuple[int, str], np.ndarray]:
    """{(mese, tipo di giorno): 24 kWh medi per ora italiana} delle famiglie (§3.4, passo 3)."""
    a = leggi_arera()
    orari = a[a["grandezza"] == "kwh_ora"].sort_values("ora")
    return {(int(m), t): g["valore"].to_numpy() for (m, t), g in orari.groupby(["mese", "tipo_giorno"])}


@functools.cache
def quote_fasce_arera() -> pd.DataFrame:
    """Quote F1/F2/F3 delle famiglie per mese (righe 1-12, colonne F1, F2, F3), per i controlli."""
    a = leggi_arera()
    q = a[a["grandezza"].str.startswith("quota_")]
    return q.pivot_table(index="mese", columns="grandezza", values="valore").rename(columns=lambda c: c[-2:].upper())


# --- Consumo orario di un socio ------------------------------------------------


def _somma_per_mese(valori: np.ndarray, gruppi: np.ndarray) -> np.ndarray:
    """Per ogni ora, la somma dei valori del suo mese."""
    return np.bincount(gruppi, weights=valori)[gruppi]


def consumo_socio(socio_id: int, tipo: str, profilo: str, scala: float, conf: dict) -> pd.DataFrame:
    """Consumo orario di un socio nel periodo della configurazione:
    kwh (con rumore) e kwh_senza_rumore (per previsione_consumo, §7)."""
    rng = config.rng_socio(socio_id)
    anagrafiche.estrai_scala(rng, tipo)  # 1. scala: già in socio_profilo, qui fa solo avanzare il generatore
    spostamento = int(rng.integers(-1, 2))  # 2. -1, 0 o +1 ora
    rumore = np.clip(rng.normal(1.0, DEVIAZIONE_RUMORE, size=len(ORE_COMPLETE)), 0, None)  # 3.

    if conf["volumi_consumo"] == "arera":
        return _consumo_arera(socio_id, profilo, scala, conf, spostamento, rumore)
    if conf["volumi_consumo"] != "provvisori":
        raise ValueError(f"volumi_consumo sconosciuto: {conf['volumi_consumo']}")

    anno = ore(*ANNO_VOLUMI)
    pesi = pesi_orari(profilo, anno, spostamento)
    rumore_anno = rumore[ORE_COMPLETE.get_indexer(anno)]
    obiettivo = VOLUMI_PROVVISORI_KWH_ANNO[tipo] * scala
    con_rumore = pesi * rumore_anno
    df = pd.DataFrame({
        "kwh": con_rumore * obiettivo / con_rumore.sum(),
        "kwh_senza_rumore": pesi * obiettivo / pesi.sum(),
    }, index=anno)

    periodo = ore(conf["primo_ts"], conf["ultimo_ts"])
    if not periodo.isin(anno).all():
        raise ValueError("Il periodo della configurazione esce dall'anno dei volumi provvisori")
    df = df.loc[periodo]
    df.insert(0, "socio_id", socio_id)
    df.insert(1, "ts", periodo.strftime("%Y-%m-%dT%H:%M:%SZ"))
    df.attrs["spostamento"] = spostamento
    return df.reset_index(drop=True)


def _consumo_arera(socio_id: int, profilo: str, scala: float, conf: dict, spostamento: int, rumore: np.ndarray) -> pd.DataFrame:
    """Dataset completo (§3.4): ogni mese UTC del periodo riceve volume ARERA del
    mese × scala. Lo stesso mese del 2025 vale anche per il 2024 e il 2026 (passo 1)."""
    periodo = ore(conf["primo_ts"], conf["ultimo_ts"])
    if periodo[0].day != 1 or periodo[0].hour != 0 or (periodo[-1] + pd.Timedelta(hours=1)).day != 1:
        raise ValueError("Con i volumi ARERA il periodo deve essere fatto di mesi interi (in UTC)")
    forma = forma_famiglia_arera() if profilo == "famiglia" else None
    pesi = pesi_orari(profilo, periodo, spostamento, forma)
    con_rumore = pesi * rumore[ORE_COMPLETE.get_indexer(periodo)]

    _, mese_di = np.unique(periodo.year * 100 + periodo.month, return_inverse=True)  # 0, 1, 2, ... per mese UTC
    obiettivo = volumi_mensili()[profilo][periodo.month - 1] * scala  # per ogni ora, il volume del suo mese
    df = pd.DataFrame({
        "socio_id": socio_id,
        "ts": testo_ore(conf["primo_ts"], conf["ultimo_ts"]),
        "kwh": con_rumore * obiettivo / _somma_per_mese(con_rumore, mese_di),
        "kwh_senza_rumore": pesi * obiettivo / _somma_per_mese(pesi, mese_di),
    })
    df.attrs["spostamento"] = spostamento
    return df


def calcola(conf: dict, socio: pd.DataFrame, socio_profilo: pd.DataFrame) -> pd.DataFrame:
    """Consumi di tutti i soci: socio_id, ts, kwh, kwh_senza_rumore (non arrotondati)."""
    soci = socio.merge(socio_profilo, left_on="id", right_on="socio_id")
    parti = [consumo_socio(s.id, s.tipo, s.profilo, s.scala, conf) for s in soci.itertuples()]
    return pd.concat(parti, ignore_index=True)


def genera(conf: dict, socio: pd.DataFrame, socio_profilo: pd.DataFrame,
           calcolati: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """consumo_orario, con l'energia a 3 decimali (§2).

    calcolati: il risultato di calcola, se c'è già. genera.py lo calcola una volta sola
    e lo riusa per previsione_consumo (derivate.py).
    """
    if calcolati is None:
        calcolati = calcola(conf, socio, socio_profilo)
    consumi = calcolati[["socio_id", "ts"]].assign(kwh=calcolati["kwh"].round(3) + 0.0)
    return {"consumo_orario": consumi[config.COLONNE["consumo_orario"]]}
