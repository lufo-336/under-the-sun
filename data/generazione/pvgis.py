"""PVGIS: riferimento per il modello di produzione (guida §3.2).

- PVcalc: produzione media mensile e annua di ogni impianto (anni 2005-2023),
  con gli stessi parametri del modello. Serve per il controllo del ±10%.
- k_impianto: fattore di taratura. Nel campione vale 1 (scorciatoia del §7).
  Nel dataset completo è kWh PVGIS 2023 / kWh del modello 2023, dove:
  - PVGIS 2023 è la produzione oraria di seriescalc (stessi parametri);
  - il modello 2023 è la formula del §3.2 con k = 1 sul meteo Open-Meteo 2023,
    preso e arrotondato come meteo_orario.
"""

import numpy as np
import pandas as pd

import config
import meteo
import produzione

PVCALC_URL = "https://re.jrc.ec.europa.eu/api/v5_3/PVcalc"
SERIESCALC_URL = "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"
PERDITE_PCT = 14  # perdite di sistema, valore predefinito di PVGIS (§3.2)
GIUGNO = 6

# Anno di confronto: l'ultimo con dati orari in PVGIS 5.3 (§3.2).
ANNO = 2023
PRIMO_TS_ANNO, ULTIMO_TS_ANNO = f"{ANNO}-01-01T00:00:00Z", f"{ANNO}-12-31T23:00:00Z"
# Open-Meteo con un giorno in più ai bordi, come per il dataset (spostamento orario)
DAL_ANNO, AL_ANNO = f"{ANNO - 1}-12-31", f"{ANNO + 1}-01-01"
DECIMALI_K = 3


def pvcalc(impianto) -> dict:
    """La risposta di PVcalc per un impianto (dalla cache, se c'è già)."""
    parametri = {
        "lat": impianto.lat,
        "lon": impianto.lon,
        "peakpower": impianto.kwp,
        "loss": PERDITE_PCT,
        "angle": impianto.inclinazione_gradi,
        "aspect": impianto.azimut_gradi,  # stessa convenzione: 0 = sud, -90 = est
        "outputformat": "json",
    }
    cache = config.CARTELLA_CACHE / "pvgis" / f"pvcalc_impianto_{impianto.id}.json"
    return config.scarica_json(PVCALC_URL, parametri, cache)


def controlla_pvcalc(risposta: dict, impianto) -> None:
    """Si ferma se la risposta non ha la forma attesa o non usa i nostri parametri."""
    problemi = []
    try:
        ingressi = risposta["inputs"]
        montaggio = ingressi["mounting_system"]["fixed"]
        modulo = ingressi["pv_module"]
        mesi = risposta["outputs"]["monthly"]["fixed"]
        totali = risposta["outputs"]["totals"]["fixed"]
    except KeyError as chiave:
        raise ValueError(f"PVcalc, impianto {impianto.id}: manca la chiave {chiave} nella risposta") from None

    attesi = {
        "inclinazione": (montaggio["slope"]["value"], impianto.inclinazione_gradi),
        "azimut": (montaggio["azimuth"]["value"], impianto.azimut_gradi),
        "potenza": (modulo["peak_power"], impianto.kwp),
        "perdite": (modulo["system_loss"], PERDITE_PCT),
    }
    for nome, (letto, atteso) in attesi.items():
        if float(letto) != float(atteso):
            problemi.append(f"{nome}: PVGIS ha usato {letto}, atteso {atteso}")
    if [m["month"] for m in mesi] != list(range(1, 13)):
        problemi.append("i mesi non sono 12")
    if "E_y" not in totali:
        problemi.append("manca il totale annuo E_y")
    if problemi:
        raise ValueError(f"PVcalc, impianto {impianto.id}: risposta diversa dall'attesa:\n  " + "\n  ".join(problemi))


def riepilogo_pvcalc(impianti: pd.DataFrame) -> pd.DataFrame:
    """Per ogni impianto: produzione annua e di giugno per kWp, irraggiamento di giugno
    sul piano dei moduli e perdite totali secondo PVGIS."""
    righe = []
    for impianto in impianti.itertuples():
        risposta = pvcalc(impianto)
        controlla_pvcalc(risposta, impianto)
        giugno = next(m for m in risposta["outputs"]["monthly"]["fixed"] if m["month"] == GIUGNO)
        totali = risposta["outputs"]["totals"]["fixed"]
        righe.append({
            "impianto_id": impianto.id,
            "kwh_kwp_anno": round(totali["E_y"] / impianto.kwp, 1),
            "kwh_kwp_giugno": round(giugno["E_m"] / impianto.kwp, 1),
            "irr_giugno_kwh_m2": round(giugno["H(i)_m"], 1),
            "perdite_totali_pct": round(totali["l_total"], 1),
        })
    return pd.DataFrame(righe)


def seriescalc(impianto) -> dict:
    """La produzione oraria PVGIS del 2023 per un impianto (dalla cache, se c'è già)."""
    parametri = {
        "lat": impianto.lat,
        "lon": impianto.lon,
        "peakpower": impianto.kwp,
        "loss": PERDITE_PCT,
        "angle": impianto.inclinazione_gradi,
        "aspect": impianto.azimut_gradi,
        "pvcalculation": 1,
        "startyear": ANNO,
        "endyear": ANNO,
        "outputformat": "json",
    }
    cache = config.CARTELLA_CACHE / "pvgis" / f"seriescalc_{ANNO}_impianto_{impianto.id}.json"
    return config.scarica_json(SERIESCALC_URL, parametri, cache)


def serie_pvgis(impianto) -> pd.Series:
    """kWh orari PVGIS del 2023, indicizzati per inizio dell'ora in UTC.

    PVGIS dà la potenza P in W con orari come "20230615:1010" (UTC): si arrotonda
    all'ora piena (10:10 -> 10:00). Su un'ora P in W diventa energia in Wh, quindi
    kWh = P / 1000. Si ferma se la risposta ha una forma diversa dall'attesa.
    """
    risposta = seriescalc(impianto)
    problemi = []
    try:
        ingressi = risposta["inputs"]
        montaggio = ingressi["mounting_system"]["fixed"]
        modulo = ingressi["pv_module"]
        orarie = risposta["outputs"]["hourly"]
    except KeyError as chiave:
        raise ValueError(f"seriescalc, impianto {impianto.id}: manca la chiave {chiave} nella risposta") from None
    attesi = {
        "inclinazione": (montaggio["slope"]["value"], impianto.inclinazione_gradi),
        "azimut": (montaggio["azimuth"]["value"], impianto.azimut_gradi),
        "potenza": (modulo["peak_power"], impianto.kwp),
        "perdite": (modulo["system_loss"], PERDITE_PCT),
    }
    for nome, (letto, atteso) in attesi.items():
        if float(letto) != float(atteso):
            problemi.append(f"{nome}: PVGIS ha usato {letto}, atteso {atteso}")
    ore = pd.to_datetime([o["time"] for o in orarie], format="%Y%m%d:%H%M", utc=True).floor("h")
    attese = pd.date_range(PRIMO_TS_ANNO, ULTIMO_TS_ANNO, freq="h")
    if not ore.equals(attese):
        problemi.append(f"ore: {len(ore)} dal {ore.min()} al {ore.max()}, attese {len(attese)} senza buchi")
    if problemi:
        raise ValueError(f"seriescalc, impianto {impianto.id}: risposta diversa dall'attesa:\n  " + "\n  ".join(problemi))
    return pd.Series([o["P"] / 1000 for o in orarie], index=ore, name="kwh_pvgis")


def meteo_anno(impianto) -> pd.DataFrame:
    """meteo_orario del 2023 per un impianto, con le stesse regole del dataset."""
    risposta = meteo.scarica(impianto, DAL_ANNO, AL_ANNO)
    meteo.controlla_risposta(risposta, impianto.id, DAL_ANNO, AL_ANNO)
    return meteo.tabella(impianto, risposta, pd.Timestamp(PRIMO_TS_ANNO), pd.Timestamp(ULTIMO_TS_ANNO))


def confronto_anno(impianto) -> pd.DataFrame:
    """Ora per ora nel 2023: kWh PVGIS e kWh del modello con k = 1 (§3.2, passi 1-2)."""
    impianti = pd.DataFrame([impianto._asdict()]).rename(columns={"Index": "indice"})
    attesa = produzione.produzione_attesa(meteo_anno(impianto), impianti, {int(impianto.id): 1.0})
    modello = pd.Series(attesa["kwh_attesi"].to_numpy(), index=pd.to_datetime(attesa["ts"], utc=True), name="kwh_modello")
    return pd.concat([serie_pvgis(impianto), modello], axis=1)


def _k(confronto: pd.DataFrame) -> float:
    """k_impianto = kWh annui PVGIS / kWh annui del modello con k = 1 (§3.2, passo 3)."""
    return round(float(confronto["kwh_pvgis"].sum() / confronto["kwh_modello"].sum()), DECIMALI_K)


def validazione(impianti: pd.DataFrame) -> pd.DataFrame:
    """Per ogni impianto: k, errore orario e correlazione tra modello tarato e PVGIS
    nel 2023 (§3.2, passo 4), più il controllo dello sfasamento orario.

    - mae_kwh: errore assoluto medio su tutte le ore dell'anno;
    - mae_pct: lo stesso errore in % della produzione media PVGIS nelle ore di sole;
    - r: correlazione di Pearson sulle ore in cui almeno uno dei due produce;
    - r_-1h, r_+1h: la stessa correlazione con il modello spostato di un'ora
      indietro o avanti. Se una delle due supera r, gli orari sono sfasati.
    """
    righe = []
    for impianto in impianti.itertuples():
        c = confronto_anno(impianto)
        k = _k(c)
        tarato = c["kwh_modello"].mul(k).clip(upper=impianto.kwp)
        sole = (c["kwh_pvgis"] > 0) | (tarato > 0)
        errore = (tarato - c["kwh_pvgis"]).abs()

        def r(spostamento: int) -> float:
            m = tarato.shift(spostamento)
            return float(np.corrcoef(m[sole].fillna(0), c["kwh_pvgis"][sole])[0, 1])

        righe.append({
            "impianto_id": impianto.id,
            "kwh_kwp_pvgis": round(c["kwh_pvgis"].sum() / impianto.kwp, 1),
            "kwh_kwp_modello_k1": round(c["kwh_modello"].sum() / impianto.kwp, 1),
            "k": k,
            "mae_kwh": round(errore.mean(), 2),
            "mae_pct": round(errore[sole].mean() / c["kwh_pvgis"][sole].mean() * 100, 1),
            "r": round(r(0), 3),
            "r_-1h": round(r(-1), 3),
            "r_+1h": round(r(1), 3),
        })
    return pd.DataFrame(righe)


def k_impianti(conf: dict, impianti: pd.DataFrame) -> dict[int, float]:
    """k_impianto di ogni impianto: 1 senza taratura (campione), altrimenti il
    rapporto tra PVGIS 2023 e modello 2023, arrotondato a 3 decimali."""
    if not conf["taratura_pvgis"]:
        return {int(i): 1.0 for i in impianti["id"]}
    return {int(impianto.id): _k(confronto_anno(impianto)) for impianto in impianti.itertuples()}
