"""PVGIS: riferimento per il modello di produzione (guida §3.2).

- PVcalc: produzione media mensile e annua di ogni impianto (anni 2005-2023),
  con gli stessi parametri del modello. Serve per il controllo del ±10%.
- k_impianto: fattore di taratura. Nel campione vale 1 (scorciatoia del §7);
  la taratura con seriescalc 2023 si fa per il dataset completo, dopo il SAL 1.
"""

import pandas as pd

import config

PVCALC_URL = "https://re.jrc.ec.europa.eu/api/v5_3/PVcalc"
PERDITE_PCT = 14  # perdite di sistema, valore predefinito di PVGIS (§3.2)
GIUGNO = 6


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


def k_impianti(conf: dict, impianti: pd.DataFrame) -> dict[int, float]:
    """k_impianto di ogni impianto: 1 senza taratura (campione)."""
    if not conf["taratura_pvgis"]:
        return {int(i): 1.0 for i in impianti["id"]}
    raise NotImplementedError("Taratura con PVGIS seriescalc 2023: da fare per il dataset completo (§3.2)")
