"""Anagrafiche: impianto, socio, socio_profilo e parametro (guida §1.2, §1.3, §3.5).

Le anagrafiche si generano sempre intere (8 impianti e 240 soci). Per il campione
si filtrano dopo, così ID e nomi coincidono con quelli del dataset completo (§7).
"""

import math

import numpy as np
import pandas as pd
from faker import Faker

import config

# --- Impianti (§1.2) --------------------------------------------------------

IMPIANTI = [
    # id, nome, comune, lat, lon, kwp, inclinazione_gradi, azimut_gradi, data_attivazione
    (1, "Tetto municipio San Secondo", "San Secondo di Pinerolo", 44.87, 7.30, 60.0, 25.0, 15.0, "2024-03-15"),
    (2, "Capannone artigiano Buriasco", "Buriasco", 44.87, 7.41, 150.0, 10.0, -20.0, "2024-05-02"),
    (3, "Tetto scuola Pinerolo", "Pinerolo", 44.88, 7.35, 180.0, 15.0, 0.0, "2024-04-01"),
    (4, "Palestra comunale Bricherasio", "Bricherasio", 44.82, 7.31, 80.0, 20.0, -10.0, "2024-06-10"),
    (5, "Pensilina parcheggio Luserna", "Luserna San Giovanni", 44.81, 7.25, 120.0, 5.0, 10.0, "2024-07-01"),
    (6, "Tetto biblioteca Torre Pellice", "Torre Pellice", 44.82, 7.22, 50.0, 30.0, 0.0, "2024-09-16"),
    (7, "Capannone agricolo Cavour", "Cavour", 44.79, 7.37, 200.0, 15.0, 5.0, "2024-08-05"),
    (8, "Tetto RSA Villar Perosa", "Villar Perosa", 44.92, 7.25, 110.0, 25.0, -30.0, "2024-10-01"),
]

# --- Soci (§1.3) ------------------------------------------------------------

# Abitanti approssimati (ordine di grandezza ISTAT). Servono solo come pesi per
# distribuire famiglie e imprese tra i comuni: Pinerolo è il più numeroso.
ABITANTI = {
    "Pinerolo": 35_700,
    "Luserna San Giovanni": 7_300,
    "Cavour": 5_400,
    "Bricherasio": 4_700,
    "Torre Pellice": 4_400,
    "Villar Perosa": 4_000,
    "San Secondo di Pinerolo": 3_600,
    "Buriasco": 1_400,
}

FAMIGLIE = 200

# Imprese: profilo, codice ATECO, quante, modello del nome (§1.3)
IMPRESE = [
    ("bar", "56.30", 4, "Bar {cognome}"),
    ("ristorante", "56.10", 4, "Ristorante {cognome}"),
    ("alimentari", "47.11", 6, "Alimentari {cognome}"),
    ("panificio", "10.71", 4, "Panificio {cognome}"),
    ("officina", "25.62", 6, "Officina meccanica {cognome}"),
    ("parrucchiere", "96.02", 6, "Acconciature {cognome}"),
]

# Enti: profilo, codice ATECO, comune, modello del nome.
# Il comune è fisso: gli enti che ospitano un impianto stanno nel suo comune.
# La scuola di Pinerolo (impianto 3) e gli uffici comunali di San Secondo
# (impianto 1) sono quelli del campione (§7).
ENTI = [
    ("scuola", "85.20", "Pinerolo", "Scuola primaria {cognome}"),  # impianto 3
    ("scuola", "85.20", "Luserna San Giovanni", "Scuola primaria {cognome}"),
    ("scuola", "85.20", "Cavour", "Scuola primaria {cognome}"),
    ("scuola", "85.20", "Villar Perosa", "Scuola primaria {cognome}"),
    ("uffici_comunali", "84.11", "San Secondo di Pinerolo", "Comune di {comune}"),  # impianto 1
    ("uffici_comunali", "84.11", "Pinerolo", "Comune di {comune}"),
    ("uffici_comunali", "84.11", "Buriasco", "Comune di {comune}"),
    ("biblioteca", "91.01", "Torre Pellice", "Biblioteca civica {cognome}"),  # impianto 6
    ("rsa", "87.10", "Villar Perosa", "RSA Villa {cognome}"),  # impianto 8
    ("impianto_sportivo", "93.11", "Bricherasio", "Palazzetto dello sport di {comune}"),  # impianto 4
]

# Adesioni: 120 soci fondatori (tutti gli enti più altri soci a caso)
# tra giugno e ottobre 2024; gli altri tra novembre 2024 e giugno 2026.
FONDATORI = 120
FONDATORI_DAL, FONDATORI_AL = "2024-06-01", "2024-10-31"
ALTRI_DAL, ALTRI_AL = "2024-11-01", "2026-06-30"

# scala: lognormale con media 1 (§3.4). sigma è la deviazione standard del
# logaritmo; per avere media 1 serve mu = -sigma² / 2 (con mu = 0 la media
# verrebbe più alta di 1).
SIGMA_SCALA = {"famiglia": 0.35, "impresa": 0.5, "ente": 0.5}

# --- Parametri (§3.5) -------------------------------------------------------

PARAMETRI = [
    ("fattore_co2_kg_kwh", 0.4133,
     "ISPRA, Rapporto 430/2026, Tab. 1.7: produzione termoelettrica lorda da fonti fossili, 2025 (dato preliminare)"),
    ("tariffa_premio_eur_kwh", 0.130,
     "DM MASE 414/2023, Allegato 1: impianti fino a 200 kW, fotovoltaico al Nord, prezzo zonale fino a 140 €/MWh"),
    ("valorizzazione_arera_eur_kwh", 0.008,
     "ARERA, TIAD (delibera 727/2022): circa 8 €/MWh nel 2023. Da aggiornare con il valore 2025-2026"),
    ("prezzo_energia_famiglia_eur_kwh", 0.351,
     "ARERA, Relazione annuale 2026 (dati 2025): prezzo finale medio dei clienti domestici, 35,12 c€/kWh"),
    ("prezzo_energia_impresa_eur_kwh", 0.351,
     "Provvisorio, uguale alle famiglie. Da aggiornare con il prezzo medio dei clienti BT altri usi (Relazione annuale ARERA)"),
    ("prezzo_energia_ente_eur_kwh", 0.351,
     "Provvisorio, uguale alle famiglie. Da aggiornare con il prezzo medio dei clienti BT altri usi (Relazione annuale ARERA)"),
    ("perdite_sistema_pct", 14.0, "PVGIS, valore predefinito delle perdite di sistema"),
    ("coeff_temperatura_pct_c", -0.4, "Valore tipico per moduli in silicio cristallino"),
]

# --- Controllo delle coordinate (§1.2) ---------------------------------------

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
SOGLIA_KM = 3.0  # oltre questa distanza dal centro del comune, la coordinata va guardata


def tabella_impianti() -> pd.DataFrame:
    """Gli 8 impianti del §1.2."""
    return pd.DataFrame(IMPIANTI, columns=config.COLONNE["impianto"])


def tabella_parametri() -> pd.DataFrame:
    """Gli 8 parametri del §3.5."""
    return pd.DataFrame(PARAMETRI, columns=config.COLONNE["parametro"])


def _giorni_a_caso(rng: np.random.Generator, dal: str, al: str, quanti: int) -> np.ndarray:
    """Date a caso tra dal e al (estremi inclusi), tutte con la stessa probabilità."""
    giorni = int((np.datetime64(al) - np.datetime64(dal)).astype(int)) + 1
    return np.datetime64(dal) + rng.integers(0, giorni, size=quanti)


def genera_soci() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Genera i 240 soci: restituisce le tabelle socio e socio_profilo."""
    rng = config.rng_anagrafica()

    # 1. L'elenco dei 240 posti: tipo, profilo, ATECO ed eventuale comune fisso
    posti = [
        {"tipo": "famiglia", "profilo": "famiglia", "ateco": None, "comune": None, "modello": None}
        for _ in range(FAMIGLIE)
    ]
    for profilo, ateco, quanti, modello in IMPRESE:
        posti += [
            {"tipo": "impresa", "profilo": profilo, "ateco": ateco, "comune": None, "modello": modello}
            for _ in range(quanti)
        ]
    for profilo, ateco, comune, modello in ENTI:
        posti.append({"tipo": "ente", "profilo": profilo, "ateco": ateco, "comune": comune, "modello": modello})
    posti = pd.DataFrame(posti)

    # 2. Comune di famiglie e imprese, in proporzione agli abitanti
    comuni = list(ABITANTI)
    pesi = np.array(list(ABITANTI.values()), dtype=float)
    senza_comune = posti["comune"].isna().to_numpy()
    posti.loc[senza_comune, "comune"] = rng.choice(comuni, size=senza_comune.sum(), p=pesi / pesi.sum())

    # 3. Fondatori: tutti gli enti, più altri soci a caso fino a 120
    fondatore = posti["tipo"].eq("ente").to_numpy(copy=True)  # copia modificabile (pandas 3)
    altri = np.flatnonzero(~fondatore)
    fondatore[rng.choice(altri, size=FONDATORI - fondatore.sum(), replace=False)] = True

    # 4. Data di adesione
    date = np.empty(len(posti), dtype="datetime64[D]")
    date[fondatore] = _giorni_a_caso(rng, FONDATORI_DAL, FONDATORI_AL, fondatore.sum())
    date[~fondatore] = _giorni_a_caso(rng, ALTRI_DAL, ALTRI_AL, (~fondatore).sum())
    posti["data_adesione"] = date

    # 5. Gli ID seguono l'ordine di adesione (a parità di data, l'ordine dell'elenco)
    posti = posti.sort_values("data_adesione", kind="stable").reset_index(drop=True)
    posti["id"] = np.arange(1, len(posti) + 1)

    # 6. Nomi di fantasia con Faker, assegnati in ordine di ID
    fake = Faker("it_IT")
    fake.seed_instance(config.SEED)
    usati = set()
    nomi = []
    for posto in posti.itertuples():
        while True:
            if posto.tipo == "famiglia":
                nome = f"{fake.first_name()} {fake.last_name()}"
            else:
                nome = posto.modello.format(cognome=fake.last_name(), comune=posto.comune)
            if nome not in usati:
                break
        usati.add(nome)
        nomi.append(nome)
    posti["nome"] = nomi

    # 7. scala: prima estrazione dal generatore proprio del socio (§2)
    scale = []
    for posto in posti.itertuples():
        sigma = SIGMA_SCALA[posto.tipo]
        scala = config.rng_socio(posto.id).lognormal(mean=-(sigma**2) / 2, sigma=sigma)
        scale.append(round(scala, 3))
    posti["scala"] = scale

    posti["data_adesione"] = posti["data_adesione"].dt.strftime("%Y-%m-%d")
    socio = posti[config.COLONNE["socio"]]
    socio_profilo = posti.rename(columns={"id": "socio_id"})[config.COLONNE["socio_profilo"]]
    return socio, socio_profilo


def scegli_campione(socio: pd.DataFrame, socio_profilo: pd.DataFrame, regola: dict) -> list[int]:
    """Sceglie gli ID dei 20 soci del campione con la regola del §7 (vedi config.py)."""
    tutti = socio.merge(socio_profilo, left_on="id", right_on="socio_id")
    adatti = tutti[tutti["data_adesione"] <= regola["aderenti_entro"]]  # date ISO: il confronto tra testi funziona

    # Famiglie: il socio di api.md, se è una famiglia aderente in tempo, più altre
    # prese a intervalli regolari nella lista, così ci sono fondatori e nuovi soci.
    famiglie = sorted(adatti.loc[adatti["tipo"] == "famiglia", "id"])
    obbligatori = [regola["socio_api"]] if regola["socio_api"] in famiglie else []
    candidati = [i for i in famiglie if i not in obbligatori]
    quante = regola["famiglie"] - len(obbligatori)
    posizioni = np.linspace(0, len(candidati) - 1, quante).round().astype(int)
    scelti = obbligatori + [candidati[p] for p in posizioni]

    # Imprese: per ogni profilo, la prima in ordine di ID
    for profilo in regola["imprese"]:
        righe = adatti[adatti["profilo"] == profilo]
        scelti.append(int(righe["id"].min()))

    # Enti: per ogni coppia (profilo, comune), l'unico ente che corrisponde
    for profilo, comune in regola["enti"]:
        righe = adatti[(adatti["profilo"] == profilo) & (adatti["comune"] == comune)]
        if len(righe) != 1:
            raise ValueError(f"Ente {profilo} a {comune}: trovati {len(righe)}, atteso 1")
        scelti.append(int(righe["id"].iloc[0]))

    return sorted(scelti)


def _distanza_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distanza approssimata in km: per pochi km basta il teorema di Pitagora."""
    dy = (lat2 - lat1) * 111.2
    dx = (lon2 - lon1) * 111.2 * math.cos(math.radians((lat1 + lat2) / 2))
    return math.hypot(dx, dy)


def controlla_coordinate(impianti: pd.DataFrame) -> pd.DataFrame:
    """Confronta le coordinate degli impianti con il centro del comune secondo la
    geocoding API di Open-Meteo. Non cambia niente: segnala solo le distanze."""
    righe = []
    for imp in impianti.itertuples():
        cache = config.CARTELLA_CACHE / "geocoding" / (imp.comune.lower().replace(" ", "_") + ".json")
        parametri = {"name": imp.comune, "count": 10, "language": "it", "format": "json", "countryCode": "IT"}
        risposta = config.scarica_json(GEOCODING_URL, parametri, cache)
        trovati = [
            r for r in risposta.get("results", [])
            if r.get("name", "").lower() == imp.comune.lower() and r.get("admin1") in ("Piemonte", "Piedmont")
        ]
        riga = {"impianto_id": imp.id, "comune": imp.comune, "lat": imp.lat, "lon": imp.lon}
        if not trovati:
            righe.append({**riga, "lat_geo": None, "lon_geo": None, "distanza_km": None, "esito": "non trovato"})
            continue
        r = trovati[0]
        distanza = _distanza_km(imp.lat, imp.lon, r["latitude"], r["longitude"])
        righe.append({
            **riga,
            "lat_geo": round(r["latitude"], 4),
            "lon_geo": round(r["longitude"], 4),
            "distanza_km": round(distanza, 1),
            "esito": "ok" if distanza <= SOGLIA_KM else "da guardare",
        })
    return pd.DataFrame(righe)


def genera(conf: dict) -> dict[str, pd.DataFrame]:
    """Le quattro tabelle delle anagrafiche, filtrate secondo la configurazione."""
    impianti = tabella_impianti()
    socio, socio_profilo = genera_soci()
    if conf["soci"] == "tutti":
        ids = socio["id"].to_list()
    else:
        ids = scegli_campione(socio, socio_profilo, conf["soci"])

    return {
        "impianto": impianti[impianti["id"].isin(conf["impianti"])].reset_index(drop=True),
        "socio": socio[socio["id"].isin(ids)].reset_index(drop=True),
        "socio_profilo": socio_profilo[socio_profilo["socio_id"].isin(ids)].reset_index(drop=True),
        "parametro": tabella_parametri(),
    }
