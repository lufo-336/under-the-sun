"""Consumi: profili orari per tipo di socio -> consumo_orario (guida §3.4 e §7).

Passi per ogni socio:
1. pesi orari in ora italiana, secondo profilo e tipo di giorno (feriale, sabato,
   domenica o festivo; per la scuola anche i giorni di lezione);
2. abitudini spostate di -1, 0 o +1 ora;
3. passaggio a UTC;
4. rumore orario (media 1, deviazione 0,15, mai sotto zero);
5. riscalatura: con i volumi provvisori (§7) il totale dal 1/9/2025 al 31/8/2026
   è volume annuo × scala; poi si taglia il periodo richiesto.

Dal generatore del socio si estraggono, sempre in quest'ordine: scala,
spostamento, rumore (config.rng_socio). Il rumore copre tutto il periodo del
dataset completo, così le ore di giugno ricevono lo stesso rumore nel campione
e nel dataset completo.
"""

from datetime import date

import holidays
import numpy as np
import pandas as pd

import anagrafiche
import config

FUSO = "Europe/Rome"
DEVIAZIONE_RUMORE = 0.15

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
# 2025/26: https://www.regione.piemonte.it/web/node/20460 (verificato il 19/11/2026).
# 2026/27: https://www.regione.piemonte.it/web/pinforma/notizie/calendario-scolastico-2026-2027
#   (verificato il 19/11/2026: le lezioni iniziano lunedì 14 settembre 2026).
#   Al campione serve perché le prime ore del 1/9/2026, in ora italiana, chiudono
#   l'anno dei volumi provvisori.
# Manca il 2024/25, che serve per la versione completa.
CALENDARI_SCOLASTICI = {
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


def pesi_del_giorno(profilo: str, giorno: date) -> np.ndarray:
    """I 24 pesi di un profilo in un giorno, per ora italiana."""
    tipo = tipo_di_giorno(giorno)
    if profilo == "famiglia":
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


def pesi_orari(profilo: str, ore_utc: pd.DatetimeIndex, spostamento: int) -> np.ndarray:
    """Pesi per ogni ora UTC. Si parte dall'ora UTC, si toglie lo spostamento
    delle abitudini e si guarda che ora è in Italia: così i giorni del cambio
    d'ora (23 o 25 ore) sono gestiti da pandas senza ore mancanti o doppie."""
    locali = (ore_utc - pd.Timedelta(hours=spostamento)).tz_convert(FUSO)
    giorni = locali.date
    pesi_per_giorno = {g: pesi_del_giorno(profilo, g) for g in set(giorni)}
    return np.array([pesi_per_giorno[g][h] for g, h in zip(giorni, locali.hour)])


def ore(primo_ts: str, ultimo_ts: str) -> pd.DatetimeIndex:
    return pd.date_range(primo_ts, ultimo_ts, freq="h")


ORE_COMPLETE = ore(config.CONFIGURAZIONI["completa"]["primo_ts"], config.CONFIGURAZIONI["completa"]["ultimo_ts"])


def consumo_socio(socio_id: int, tipo: str, profilo: str, scala: float, conf: dict) -> pd.DataFrame:
    """Consumo orario di un socio nel periodo della configurazione:
    kwh (con rumore) e kwh_senza_rumore (per previsione_consumo, §7)."""
    if conf["volumi_consumo"] != "provvisori":
        raise NotImplementedError("Volumi mensili ARERA: da fare per il dataset completo (§3.4)")

    rng = config.rng_socio(socio_id)
    anagrafiche.estrai_scala(rng, tipo)  # 1. scala: già in socio_profilo, qui fa solo avanzare il generatore
    spostamento = int(rng.integers(-1, 2))  # 2. -1, 0 o +1 ora
    rumore = np.clip(rng.normal(1.0, DEVIAZIONE_RUMORE, size=len(ORE_COMPLETE)), 0, None)  # 3.

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


def calcola(conf: dict, socio: pd.DataFrame, socio_profilo: pd.DataFrame) -> pd.DataFrame:
    """Consumi di tutti i soci: socio_id, ts, kwh, kwh_senza_rumore (non arrotondati)."""
    soci = socio.merge(socio_profilo, left_on="id", right_on="socio_id")
    parti = [consumo_socio(s.id, s.tipo, s.profilo, s.scala, conf) for s in soci.itertuples()]
    return pd.concat(parti, ignore_index=True)


def genera(conf: dict, socio: pd.DataFrame, socio_profilo: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """consumo_orario, con l'energia a 3 decimali (§2)."""
    consumi = calcola(conf, socio, socio_profilo)
    consumi["kwh"] = consumi["kwh"].round(3) + 0.0
    return {"consumo_orario": consumi[config.COLONNE["consumo_orario"]]}
