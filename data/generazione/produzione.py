"""Produzione: modello sul meteo reale -> produzione_oraria e anomalie_vere (guida §3.2, §3.3).

La produzione si calcola da meteo_orario così come è scritto nel CSV (valori a
1 decimale): chi rifà il calcolo partendo dai file ottiene gli stessi numeri.
"""

import pandas as pd

import config

# Costanti della formula (§3.2)
FATTORE_PERDITE = 0.86  # perdite di sistema del 14%
RISCALDAMENTO_MODULO = 0.03  # °C in più sul modulo per ogni W/m²
COEFF_TEMPERATURA = 0.004  # -0,4% di resa per ogni °C sopra 25

# Anomalie fisse, presenti sia nel campione sia nel dataset completo (§3.3).
# inizio incluso, fine esclusa (§2): il guasto azzera le ore 11, 12, 13 e 14.
ANOMALIE_FISSE = [
    {"impianto_id": 3, "inizio": "2026-06-01T11:00:00Z", "fine": "2026-06-01T15:00:00Z",
     "tipo": "guasto", "perdita_pct": 100.0},
]


def produzione_attesa(meteo_orario: pd.DataFrame, impianti: pd.DataFrame, k: dict[int, float]) -> pd.DataFrame:
    """Produzione senza anomalie (kwh_attesi, non arrotondati), ora per ora.

    T_modulo    = temperatura_c + 0.03 × irraggiamento_pannelli_wm2
    fattore_T   = 1 − 0.004 × (T_modulo − 25)
    kwh_teorici = kwp × irraggiamento_pannelli_wm2 / 1000 × 0.86 × fattore_T × k_impianto
    kwh_attesi  = min(kwh_teorici, kwp)
    """
    df = meteo_orario.merge(impianti[["id", "kwp"]], left_on="impianto_id", right_on="id")
    gti = df["irraggiamento_pannelli_wm2"]
    t_modulo = df["temperatura_c"] + RISCALDAMENTO_MODULO * gti
    fattore_t = 1 - COEFF_TEMPERATURA * (t_modulo - 25)
    k_impianto = df["impianto_id"].map(k)
    kwh_teorici = df["kwp"] * gti / 1000 * FATTORE_PERDITE * fattore_t * k_impianto
    df["kwh_attesi"] = kwh_teorici.clip(lower=0, upper=df["kwp"])
    return df[["impianto_id", "ts", "kwh_attesi"]]


def anomalie(conf: dict) -> pd.DataFrame:
    """anomalie_vere per gli impianti e il periodo della configurazione."""
    if conf["anomalie_casuali"]:
        raise NotImplementedError("Anomalie casuali (guasti, stringhe, sporcizia, neve): da fare per il dataset completo (§3.3)")
    tabella = pd.DataFrame(ANOMALIE_FISSE)
    nel_periodo = (
        tabella["impianto_id"].isin(conf["impianti"])
        & (tabella["inizio"] <= conf["ultimo_ts"])  # date ISO in UTC: il confronto tra testi funziona
        & (tabella["fine"] > conf["primo_ts"])
    )
    tabella = tabella[nel_periodo].reset_index(drop=True)
    tabella.insert(0, "id", range(1, len(tabella) + 1))
    return tabella[config.COLONNE["anomalie_vere"]]


def effetto_anomalie(attesa: pd.DataFrame, anomalie_vere: pd.DataFrame) -> pd.Series:
    """Fattore per cui si moltiplica la produzione attesa: 1 senza anomalie.

    Per ora gestisce i cali fissi (guasto, stringa): 1 − perdita_pct / 100 tra inizio
    (incluso) e fine (esclusa). Al guasto basta azzerare tutte le ore della finestra:
    di notte la produzione è già 0.
    """
    effetto = pd.Series(1.0, index=attesa.index)
    for anomalia in anomalie_vere.itertuples():
        if anomalia.tipo not in ("guasto", "stringa"):
            raise NotImplementedError(f"Anomalia di tipo {anomalia.tipo}: da fare per il dataset completo")
        dentro = (
            (attesa["impianto_id"] == anomalia.impianto_id)
            & (attesa["ts"] >= anomalia.inizio)
            & (attesa["ts"] < anomalia.fine)
        )
        effetto[dentro] *= 1 - anomalia.perdita_pct / 100
    return effetto


def genera(conf: dict, impianti: pd.DataFrame, meteo_orario: pd.DataFrame, k: dict[int, float]) -> dict[str, pd.DataFrame]:
    """produzione_oraria (con le anomalie) e anomalie_vere."""
    attesa = produzione_attesa(meteo_orario, impianti, k)
    anomalie_vere = anomalie(conf)
    kwh = attesa["kwh_attesi"] * effetto_anomalie(attesa, anomalie_vere)
    produzione = attesa[["impianto_id", "ts"]].assign(kwh=kwh.round(3) + 0.0)  # 3 decimali (§2)
    return {
        "produzione_oraria": produzione[config.COLONNE["produzione_oraria"]],
        "anomalie_vere": anomalie_vere,
    }
