"""Impostazioni comuni della pipeline dati UnderTheSun.

Qui stanno le scelte fisse di GUIDA-DATASET.md:
- seed e generatori casuali (§2);
- le due configurazioni, PICCOLA e COMPLETA (§1.4 e §7);
- i nomi dei file e delle colonne (§4).

Gli altri moduli leggono da qui. Se cambia una regola, prima si aggiorna la guida,
poi questo file.
"""

import json
from pathlib import Path

import numpy as np
import requests

# --- Cartelle ---------------------------------------------------------------

CARTELLA_DATA = Path(__file__).resolve().parent.parent  # .../data
CARTELLA_ESEMPI = CARTELLA_DATA / "esempi"  # campione SAL 1, va su GitHub
CARTELLA_OUTPUT = CARTELLA_DATA / "output"  # dataset completo, escluso da Git
CARTELLA_CACHE = CARTELLA_OUTPUT / "cache"  # risposte di Open-Meteo, PVGIS, ARERA

# --- Seed e generatori casuali (§2) -----------------------------------------

SEED = 42


def rng_impianto(impianto_id: int) -> np.random.Generator:
    """Generatore casuale proprio di un impianto: default_rng([42, 0, id])."""
    return np.random.default_rng([SEED, 0, impianto_id])


def rng_socio(socio_id: int) -> np.random.Generator:
    """Generatore casuale proprio di un socio: default_rng([42, 1, id]).

    Ordine fisso delle estrazioni (chi lo usa deve rispettarlo):
    1. scala (anagrafiche.py);
    2. spostamento delle abitudini, 0 o ±1 ora (consumi.py);
    3. rumore orario (consumi.py).
    """
    return np.random.default_rng([SEED, 1, socio_id])


def rng_anagrafica() -> np.random.Generator:
    """Generatore per le scelte che riguardano tutta la comunità: tipo, comune e
    data di adesione dei 240 soci. default_rng([42, 2]).

    L'anagrafica si genera sempre intera, quindi queste scelte sono le stesse
    in PICCOLA e in COMPLETA.
    """
    return np.random.default_rng([SEED, 2])


# --- Cache delle fonti (CLAUDE.md) ------------------------------------------


def scarica_json(url: str, parametri: dict, percorso_cache: Path) -> dict:
    """Restituisce la risposta JSON di un'API, scaricandola solo la prima volta.

    La risposta grezza si salva in percorso_cache e da lì si rilegge: la stessa
    cosa non si scarica due volte. Per riscaricarla si cancella il file.
    """
    if not percorso_cache.exists():
        risposta = requests.get(url, params=parametri, timeout=120)
        risposta.raise_for_status()
        percorso_cache.parent.mkdir(parents=True, exist_ok=True)
        percorso_cache.write_text(risposta.text, encoding="utf-8")
    return json.loads(percorso_cache.read_text(encoding="utf-8"))


# --- Le due configurazioni --------------------------------------------------
# primo_ts e ultimo_ts sono entrambi inclusi: ultimo_ts è l'inizio dell'ultima ora.

CONFIGURAZIONI = {
    "piccola": {
        "descrizione": "Campione SAL 1: giugno 2026, impianti 1-3, 20 soci (§7)",
        "primo_ts": "2026-06-01T00:00:00Z",
        "ultimo_ts": "2026-06-30T23:00:00Z",  # 720 ore
        "impianti": [1, 2, 3],
        # Regola di scelta dei 20 soci (§7), applicata in anagrafiche.py
        # alla lista completa dei 240 soci.
        "soci": {
            "aderenti_entro": "2026-06-01",
            "famiglie": 14,
            "socio_api": 42,  # usato in api.md: incluso se è una famiglia aderente in tempo
            "imprese": ["bar", "panificio", "officina", "parrucchiere"],
            "enti": [("scuola", "Pinerolo"), ("uffici_comunali", "San Secondo di Pinerolo")],
        },
        "volumi_consumo": "provvisori",  # scorciatoia del §7: volumi annui fissi per tipo di socio
        "taratura_pvgis": False,  # k_impianto = 1 (scorciatoia del §7)
        "anomalie_casuali": False,  # §3.3: in giugno 2026 sugli impianti 1-3 c'è solo il guasto fisso
        "cartella": CARTELLA_ESEMPI,
    },
    "completa": {
        "descrizione": "Dataset SAL 2: nov 2024 - ott 2026, 8 impianti, 240 soci",
        "primo_ts": "2024-11-01T00:00:00Z",
        "ultimo_ts": "2026-10-31T23:00:00Z",  # 17.520 ore
        "impianti": [1, 2, 3, 4, 5, 6, 7, 8],
        "soci": "tutti",
        "volumi_consumo": "arera",  # volumi mensili ARERA (§3.4)
        "taratura_pvgis": True,
        "anomalie_casuali": True,
        "cartella": CARTELLA_OUTPUT,
    },
}

# --- File e colonne (§4) ----------------------------------------------------
# Nomi esattamente come nella guida: non si aggiungono, tolgono o rinominano
# colonne senza chiedere.

# Tabelle generate dal team dati
TABELLE_GENERATE = {
    "impianto": [
        "id", "nome", "comune", "lat", "lon", "kwp",
        "inclinazione_gradi", "azimut_gradi", "data_attivazione",
    ],
    "socio": ["id", "nome", "tipo", "comune", "data_adesione"],
    "consumo_orario": ["socio_id", "ts", "kwh"],
    "produzione_oraria": ["impianto_id", "ts", "kwh"],
    "meteo_orario": [
        "impianto_id", "ts", "irraggiamento_wm2", "irraggiamento_pannelli_wm2",
        "temperatura_c", "nuvolosita_pct", "neve_cm",
    ],
    "bolletta": ["id", "socio_id", "mese", "kwh", "importo_eur"],
    "parametro": ["chiave", "valore", "fonte"],
    "segnalazione": [
        "id", "socio_id", "impianto_id", "impianto_id_llm", "ts", "canale", "testo",
        "categoria_llm", "urgenza_llm", "categoria", "urgenza", "stato",
    ],
    "verbale": ["id", "data_assemblea", "testo", "sintesi"],
}

# Tabelle calcolate dai batch (nel campione con valori provvisori, §7)
TABELLE_CALCOLATE = {
    "previsione_produzione": ["impianto_id", "ts", "kwh_previsti"],
    "previsione_consumo": ["socio_id", "ts", "kwh_previsti"],
    "anomalia": ["id", "impianto_id", "inizio", "fine", "tipo", "score", "stato"],
    "ripartizione_mensile": ["socio_id", "mese", "kwh_condivisi", "incentivo_eur", "co2_evitata_kg"],
}

# File di lavoro: non vanno nel database
FILE_DI_LAVORO = {
    "anomalie_vere": ["id", "impianto_id", "inizio", "fine", "tipo", "perdita_pct"],
    "segnalazione_etichette": ["segnalazione_id", "categoria_vera", "urgenza_vera", "impianto_id_vero"],
    "socio_profilo": ["socio_id", "profilo", "ateco", "scala"],
}

COLONNE = {**TABELLE_GENERATE, **TABELLE_CALCOLATE, **FILE_DI_LAVORO}

# Le tabelle che finiscono nel database (quelle che servono allo script di Luca)
TABELLE_DB = list(TABELLE_GENERATE) + list(TABELLE_CALCOLATE)
