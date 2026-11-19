"""Meteo: Open-Meteo -> meteo_orario (guida §3.1).

Una chiamata per impianto sull'intero periodo, più un giorno ai bordi, salvata
in cache: il campione e il dataset completo usano la stessa risposta.
"""

import pandas as pd

import config

URL = "https://archive-api.open-meteo.com/v1/archive"
DAL, AL = "2024-10-31", "2026-11-01"  # un giorno in più ai bordi per lo spostamento orario

# Variabile Open-Meteo -> (colonna di meteo_orario, unità attesa, da spostare?)
# Radiazione e neve indicate alle hh:00 si riferiscono all'ora precedente: si
# spostano indietro di un'ora, così il valore va sul ts di inizio ora.
# Temperatura e nuvolosità sono istantanee: si prende il valore all'inizio dell'ora.
VARIABILI = {
    "shortwave_radiation": ("irraggiamento_wm2", "W/m²", True),
    "global_tilted_irradiance": ("irraggiamento_pannelli_wm2", "W/m²", True),
    "temperature_2m": ("temperatura_c", "°C", False),
    "cloud_cover": ("nuvolosita_pct", "%", False),
    "snowfall": ("neve_cm", "cm", True),
}


def scarica(impianto) -> dict:
    """La risposta di Open-Meteo per un impianto (dalla cache, se c'è già)."""
    parametri = {
        "latitude": impianto.lat,
        "longitude": impianto.lon,
        "start_date": DAL,
        "end_date": AL,
        "timezone": "GMT",
        "tilt": impianto.inclinazione_gradi,
        "azimuth": impianto.azimut_gradi,
        "hourly": ",".join(VARIABILI),
    }
    cache = config.CARTELLA_CACHE / "openmeteo" / f"impianto_{impianto.id}_{DAL}_{AL}.json"
    return config.scarica_json(URL, parametri, cache)


def controlla_risposta(risposta: dict, impianto_id: int) -> None:
    """Si ferma se la risposta ha una forma diversa da quella attesa (CLAUDE.md:
    meglio fermarsi e chiedere che indovinare)."""
    problemi = []
    if risposta.get("utc_offset_seconds") != 0:
        problemi.append(f"utc_offset_seconds = {risposta.get('utc_offset_seconds')}, atteso 0")
    unita = risposta.get("hourly_units", {})
    for variabile, (_, attesa, _) in VARIABILI.items():
        if unita.get(variabile) != attesa:
            problemi.append(f"{variabile}: unità {unita.get(variabile)!r}, attesa {attesa!r}")
    ore = pd.to_datetime(risposta["hourly"]["time"], utc=True)
    attese = pd.date_range(f"{DAL}T00:00Z", f"{AL}T23:00Z", freq="h")
    if not ore.equals(attese):
        problemi.append(f"ore: {len(ore)} dal {ore.min()} al {ore.max()}, attese {len(attese)} senza buchi")
    if problemi:
        raise ValueError(f"Open-Meteo, impianto {impianto_id}: risposta diversa dall'attesa:\n  " + "\n  ".join(problemi))


def tabella(impianto, risposta: dict, primo_ts: pd.Timestamp, ultimo_ts: pd.Timestamp) -> pd.DataFrame:
    """meteo_orario di un impianto tra primo_ts e ultimo_ts (inclusi)."""
    orario = risposta["hourly"]
    ore = pd.to_datetime(orario["time"], utc=True)
    df = pd.DataFrame(index=ore)
    for variabile, (colonna, _, sposta) in VARIABILI.items():
        serie = pd.Series(orario[variabile], index=ore, dtype=float)
        # shift(-1): il valore delle 11:00 di Open-Meteo (ora 10-11) va sul ts 10:00
        df[colonna] = serie.shift(-1) if sposta else serie

    df = df.loc[primo_ts:ultimo_ts]
    df = df.round(1) + 0.0  # 1 decimale (§2); "+ 0.0" trasforma -0.0 in 0.0
    df.insert(0, "impianto_id", impianto.id)
    df.insert(1, "ts", df.index.strftime("%Y-%m-%dT%H:%M:%SZ"))
    return df.reset_index(drop=True)[config.COLONNE["meteo_orario"]]


def genera(conf: dict, impianti: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """meteo_orario per gli impianti e il periodo della configurazione."""
    primo_ts, ultimo_ts = pd.Timestamp(conf["primo_ts"]), pd.Timestamp(conf["ultimo_ts"])
    parti = []
    for impianto in impianti.itertuples():
        risposta = scarica(impianto)
        controlla_risposta(risposta, impianto.id)
        parti.append(tabella(impianto, risposta, primo_ts, ultimo_ts))
    return {"meteo_orario": pd.concat(parti, ignore_index=True)}
