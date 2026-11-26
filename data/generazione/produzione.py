"""Produzione: modello sul meteo reale -> produzione_oraria e anomalie_vere (guida §3.2, §3.3).

La produzione si calcola da meteo_orario così come è scritto nel CSV (valori a
1 decimale): chi rifà il calcolo partendo dai file ottiene gli stessi numeri.
Anche le anomalie si ricostruiscono dai soli file: ogni riga di anomalie_vere
basta a calcolare il suo effetto ora per ora (vedi effetto_anomalie).
"""

import numpy as np
import pandas as pd

import config

# Costanti della formula (§3.2)
FATTORE_PERDITE = 0.86  # perdite di sistema del 14%
RISCALDAMENTO_MODULO = 0.03  # °C in più sul modulo per ogni W/m²
COEFF_TEMPERATURA = 0.004  # -0,4% di resa per ogni °C sopra 25

ORA = pd.Timedelta(hours=1)
GIORNO = pd.Timedelta(days=1)

# Anomalie fisse, presenti sia nel campione sia nel dataset completo (§3.3).
# inizio incluso, fine esclusa (§2): il guasto azzera le ore 11, 12, 13 e 14.
ANOMALIE_FISSE = [
    {"impianto_id": 3, "inizio": "2026-06-01T11:00:00Z", "fine": "2026-06-01T15:00:00Z",
     "tipo": "guasto", "perdita_pct": 100.0},
]

# --- Anomalie casuali del dataset completo (§3.3) ------------------------------
#
# A quale impianto va ogni anomalia: scelta fissa, così ogni impianto usa solo il
# proprio generatore casuale (§2) per date, durate e perdite.
# - guasto: 10 in tutto, cioè quello fisso più 9 casuali (uno per impianto, due sul 7);
# - stringa: 4, sugli impianti con più stringhe (capannoni, palestra, RSA);
# - sporcizia: 5, sui moduli poco inclinati o in zona agricola (due sul 7).
ASSEGNAZIONE = {
    "sporcizia": [2, 5, 6, 7, 7],
    "stringa": [2, 4, 7, 8],
    "guasto": [1, 2, 3, 4, 5, 6, 7, 7, 8],
}
ORDINE_TIPI = ["sporcizia", "stringa", "guasto"]  # ordine delle estrazioni per ogni impianto

GUASTO_ORE = (2, 120)  # da 2 ore a 5 giorni, distribuzione log-uniforme (tanti guasti brevi)
STRINGA_PERDITA_PCT = (20.0, 35.0)
STRINGA_GIORNI = (7, 28)  # riparazione in 1-4 settimane
SPORCIZIA_PERDITA_PCT = (10.0, 15.0)  # perdita raggiunta il giorno della pulizia
SPORCIZIA_PCT_SETTIMANA = (0.8, 1.2)  # "circa l'1% a settimana"
SPORCIZIA_MESI_INIZIO = (4, 5, 6, 7)  # inizia tra aprile e luglio: "soprattutto in estate"
SOGLIA_SOLE = 0.10  # guasti e stringhe iniziano in un'ora con produzione attesa ≥ 10% di kwp
DISTACCO = GIORNO  # tra due anomalie dello stesso impianto passano almeno 24 ore
TENTATIVI = 10_000

# Neve (§3.3): produzione al 5% dopo una nevicata
NEVE_SOGLIA_CM = 2.0  # neve caduta nelle 24 ore precedenti
NEVE_TMAX_C = 3.0  # giorni "caldi": temperatura massima sopra 3 °C
NEVE_GIORNI_CALDI = 2
NEVE_PERDITA_PCT = 95.0

# Campione stabile (§3.3): nessuna anomalia casuale tocca giugno 2026 sugli impianti 1-3
CAMPIONE = config.CONFIGURAZIONI["piccola"]
CAMPIONE_IMPIANTI = CAMPIONE["impianti"]
CAMPIONE_DAL = pd.Timestamp(CAMPIONE["primo_ts"])
CAMPIONE_AL = pd.Timestamp(CAMPIONE["ultimo_ts"]) + ORA  # escluso


def _iso(t: pd.Timestamp) -> str:
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


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


# --- Neve -----------------------------------------------------------------------


def episodi_neve(meteo_impianto: pd.DataFrame) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Episodi di neve sui moduli di un impianto, ricavati dal suo meteo (§3.3).

    - inizio: la prima ora in cui la neve caduta nelle 24 ore precedenti è ≥ 2 cm;
    - fine (esclusa): le 00:00 UTC dopo il 2° giorno con temperatura massima sopra
      3 °C. I giorni si contano dal giorno dopo l'ultima ora con almeno 2 cm nelle
      24 ore precedenti: una nuova nevicata fa ripartire il conteggio;
    - se il periodo finisce prima, l'episodio si chiude con il periodo.
    I giorni sono in UTC, come i mesi (§2).
    """
    m = meteo_impianto.assign(t=pd.to_datetime(meteo_impianto["ts"], utc=True)).set_index("t").sort_index()
    # Somma delle 24 ore precedenti (h-24 ... h-1), arrotondata come i dati (1 decimale)
    neve_24h = m["neve_cm"].rolling(24, min_periods=1).sum().shift(1).round(1)
    nevica = neve_24h >= NEVE_SOGLIA_CM
    giorno = m.index.floor("D")
    tmax = m["temperatura_c"].groupby(giorno).max()
    giorni_con_neve = set(giorno[nevica.to_numpy()])
    fine_periodo = m.index[-1] + ORA

    episodi = []
    ore_neve = m.index[nevica.to_numpy()]
    while len(ore_neve):
        inizio = ore_neve[0]
        fine, caldi = fine_periodo, 0
        for g in tmax.index[tmax.index > inizio.floor("D")]:
            if g in giorni_con_neve:  # nuova nevicata: il conteggio riparte
                caldi = 0
            elif tmax[g] > NEVE_TMAX_C:
                caldi += 1
                if caldi == NEVE_GIORNI_CALDI:
                    fine = g + GIORNO
                    break
        episodi.append((inizio, fine))
        ore_neve = ore_neve[ore_neve >= fine]
    return episodi


# --- Anomalie casuali -----------------------------------------------------------


def _libero(inizio, fine, occupati, impianto_id, dal, al) -> bool:
    """True se [inizio, fine) sta nel periodo, è lontano almeno DISTACCO dalle altre
    anomalie dell'impianto e, sugli impianti del campione, non tocca giugno 2026."""
    if inizio < dal or fine > al:
        return False
    if impianto_id in CAMPIONE_IMPIANTI and inizio < CAMPIONE_AL and fine > CAMPIONE_DAL:
        return False
    return all(fine + DISTACCO <= a or inizio >= b + DISTACCO for a, b in occupati)


def anomalie_casuali(impianto, attesa_impianto: pd.DataFrame, occupati: list, dal, al) -> list[dict]:
    """Guasti, stringhe e sporcizia di un impianto, con il suo generatore (§2).

    Ordine fisso delle estrazioni: per ogni tipo di ORDINE_TIPI e per ogni anomalia
    assegnata all'impianto, prima i parametri (perdita, durata), poi l'inizio. Un
    inizio che non rispetta _libero si scarta e se ne estrae un altro.
    """
    rng = config.rng_impianto(int(impianto.id))
    t = pd.to_datetime(attesa_impianto["ts"], utc=True)
    ore_sole = pd.DatetimeIndex(t[attesa_impianto["kwh_attesi"] >= SOGLIA_SOLE * impianto.kwp])
    giorni = pd.date_range(dal, al - GIORNO, freq="D")
    giorni_estate = giorni[giorni.month.isin(SPORCIZIA_MESI_INIZIO)]
    occupati = list(occupati)
    righe = []
    for tipo in ORDINE_TIPI:
        for _ in range(ASSEGNAZIONE[tipo].count(int(impianto.id))):
            if tipo == "guasto":
                durata = pd.Timedelta(hours=int(round(np.exp(rng.uniform(*np.log(GUASTO_ORE))))))
                perdita, candidati = 100.0, ore_sole
            elif tipo == "stringa":
                perdita = round(float(rng.uniform(*STRINGA_PERDITA_PCT)), 1)
                durata = pd.Timedelta(hours=int(round(rng.uniform(*STRINGA_GIORNI) * 24)))
                candidati = ore_sole
            else:  # sporcizia: cresce di circa l'1% a settimana fino alla perdita finale
                perdita = round(float(rng.uniform(*SPORCIZIA_PERDITA_PCT)), 1)
                per_settimana = float(rng.uniform(*SPORCIZIA_PCT_SETTIMANA))
                durata = pd.Timedelta(days=int(round(perdita / per_settimana * 7)))
                candidati = giorni_estate
            for _ in range(TENTATIVI):
                inizio = candidati[int(rng.integers(len(candidati)))]
                if _libero(inizio, inizio + durata, occupati, int(impianto.id), dal, al):
                    break
            else:
                raise RuntimeError(f"Impianto {impianto.id}: nessuno spazio libero per {tipo} di {durata}")
            occupati.append((inizio, inizio + durata))
            righe.append({"impianto_id": int(impianto.id), "inizio": _iso(inizio), "fine": _iso(inizio + durata),
                          "tipo": tipo, "perdita_pct": perdita})
    return righe


def anomalie(conf: dict, impianti: pd.DataFrame | None = None, meteo_orario: pd.DataFrame | None = None,
             attesa: pd.DataFrame | None = None) -> pd.DataFrame:
    """anomalie_vere per gli impianti e il periodo della configurazione.

    - Anomalie fisse del periodo: prendono gli id 1, 2, ... (come nel campione).
    - Dataset completo: per ogni impianto gli episodi di neve, poi le anomalie
      casuali negli spazi liberi; numerate in ordine di inizio.
    """
    tabella = pd.DataFrame(ANOMALIE_FISSE)
    nel_periodo = (
        tabella["impianto_id"].isin(conf["impianti"])
        & (tabella["inizio"] <= conf["ultimo_ts"])  # date ISO in UTC: il confronto tra testi funziona
        & (tabella["fine"] > conf["primo_ts"])
    )
    fisse = tabella[nel_periodo].reset_index(drop=True)

    altre = []
    if conf["anomalie_casuali"]:
        dal, al = pd.Timestamp(conf["primo_ts"]), pd.Timestamp(conf["ultimo_ts"]) + ORA
        for impianto in impianti[impianti["id"].isin(conf["impianti"])].itertuples():
            occupati = [(pd.Timestamp(a.inizio), pd.Timestamp(a.fine))
                        for a in fisse[fisse["impianto_id"] == impianto.id].itertuples()]
            for inizio, fine in episodi_neve(meteo_orario[meteo_orario["impianto_id"] == impianto.id]):
                occupati.append((inizio, fine))
                altre.append({"impianto_id": int(impianto.id), "inizio": _iso(inizio), "fine": _iso(fine),
                              "tipo": "neve", "perdita_pct": NEVE_PERDITA_PCT})
            altre += anomalie_casuali(impianto, attesa[attesa["impianto_id"] == impianto.id], occupati, dal, al)

    altre = pd.DataFrame(altre, columns=fisse.columns)
    if len(altre):
        altre = altre.sort_values(["inizio", "impianto_id"], kind="stable")
    tabella = pd.concat([fisse, altre], ignore_index=True) if len(altre) else fisse
    tabella.insert(0, "id", range(1, len(tabella) + 1))
    return tabella[config.COLONNE["anomalie_vere"]]


def effetto_anomalie(attesa: pd.DataFrame, anomalie_vere: pd.DataFrame) -> pd.Series:
    """Fattore per cui si moltiplica la produzione attesa: 1 senza anomalie.

    Tra inizio (incluso) e fine (esclusa):
    - guasto, stringa, neve: calo fisso, 1 − perdita_pct / 100 (il guasto azzera
      tutte le ore della finestra: di notte la produzione è già 0);
    - sporcizia: calo che cresce in modo lineare ora per ora e raggiunge
      perdita_pct nell'ultima ora; dalla fine (pulizia) si torna a 1.
    """
    effetto = pd.Series(1.0, index=attesa.index)
    ore = None
    for anomalia in anomalie_vere.itertuples():
        if anomalia.tipo not in ("guasto", "stringa", "neve", "sporcizia"):
            raise ValueError(f"Anomalia di tipo sconosciuto: {anomalia.tipo}")
        dentro = (
            (attesa["impianto_id"] == anomalia.impianto_id)
            & (attesa["ts"] >= anomalia.inizio)
            & (attesa["ts"] < anomalia.fine)
        )
        if anomalia.tipo == "sporcizia":
            if ore is None:
                ore = pd.to_datetime(attesa["ts"], utc=True)
            inizio, fine = pd.Timestamp(anomalia.inizio), pd.Timestamp(anomalia.fine)
            quota = ((ore[dentro] - inizio) / ORA + 1) / ((fine - inizio) / ORA)
            effetto[dentro] *= 1 - anomalia.perdita_pct / 100 * quota
        else:
            effetto[dentro] *= 1 - anomalia.perdita_pct / 100
    return effetto


def genera(conf: dict, impianti: pd.DataFrame, meteo_orario: pd.DataFrame, k: dict[int, float]) -> dict[str, pd.DataFrame]:
    """produzione_oraria (con le anomalie) e anomalie_vere."""
    attesa = produzione_attesa(meteo_orario, impianti, k)
    anomalie_vere = anomalie(conf, impianti, meteo_orario, attesa)
    kwh = attesa["kwh_attesi"] * effetto_anomalie(attesa, anomalie_vere)
    produzione = attesa[["impianto_id", "ts"]].assign(kwh=kwh.round(3) + 0.0)  # 3 decimali (§2)
    return {
        "produzione_oraria": produzione[config.COLONNE["produzione_oraria"]],
        "anomalie_vere": anomalie_vere,
    }
