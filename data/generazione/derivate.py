"""Derivate: bolletta, tabelle calcolate e riepilogo dei trimestri (guida §3.6, §4 e §7).

Tutto si calcola dai valori così come sono scritti nei CSV (energia a 3 decimali):
chi rifà il conto partendo dai file ottiene gli stessi numeri.

Tabelle calcolate (§4), che nel progetto scriveranno i batch. Lo zip v1 del completo
le contiene comunque, perché db/seed/carica.sql carica 13 CSV:
- ripartizione_mensile: il calcolo vero del §3.6, sia nel campione sia nel completo;
- previsione_produzione (provvisoria): la formula della produzione senza anomalie;
- previsione_consumo (provvisoria): il profilo del socio senza rumore;
- anomalia (provvisoria): solo il guasto fisso dell'impianto 3 del 1/6/2026, come se
  il batch l'avesse trovato (score 0.97, aperta).

riepilogo_trimestri (solo nel completo) è un file di lavoro per scrivere i verbali.
"""

import numpy as np
import pandas as pd

import config
import consumi
import produzione

SCORE_PROVVISORIO = 0.97  # come in api.md
STATO_PROVVISORIO = "aperta"

# Un verbale a trimestre: ogni assemblea commenta il trimestre appena concluso (§3.7).
# (verbale_id, trimestre, inizio incluso, fine esclusa). Il primo trimestre ha solo
# 2 mesi, perché il periodo comincia il 1/11/2024. Ottobre 2026 non ha un verbale.
TRIMESTRI = [
    (1, "nov-dic 2024", "2024-11-01", "2025-01-01"),
    (2, "gen-mar 2025", "2025-01-01", "2025-04-01"),
    (3, "apr-giu 2025", "2025-04-01", "2025-07-01"),
    (4, "lug-set 2025", "2025-07-01", "2025-10-01"),
    (5, "ott-dic 2025", "2025-10-01", "2026-01-01"),
    (6, "gen-mar 2026", "2026-01-01", "2026-04-01"),
    (7, "apr-giu 2026", "2026-04-01", "2026-07-01"),
    (8, "lug-set 2026", "2026-07-01", "2026-10-01"),
]
TIPI_ANOMALIA = ["guasto", "stringa", "sporcizia", "neve"]


def _mese(ts: pd.Series) -> pd.Series:
    """Primo giorno del mese in UTC, come date_trunc('month', ts) (§2)."""
    return ts.str.slice(0, 7) + "-01"  # "2026-06-01T10:00:00Z" -> "2026-06-01"


def _istante(giorno: str) -> str:
    """"2025-01-01" -> "2025-01-01T00:00:00Z", per confrontare le date con i ts."""
    return giorno + "T00:00:00Z"


def bolletta(consumo_orario: pd.DataFrame, socio: pd.DataFrame, parametro: pd.DataFrame) -> pd.DataFrame:
    """Una riga per socio e mese: kwh del mese e importo = kwh × prezzo del suo tipo (§3.5)."""
    prezzi = dict(zip(parametro["chiave"], parametro["valore"]))
    df = consumo_orario.assign(mese=_mese(consumo_orario["ts"]))
    df = df.groupby(["socio_id", "mese"], as_index=False)["kwh"].sum()
    df = df.merge(socio[["id", "tipo"]], left_on="socio_id", right_on="id")
    df["kwh"] = df["kwh"].round(3) + 0.0
    prezzo = df["tipo"].map(lambda tipo: prezzi[f"prezzo_energia_{tipo}_eur_kwh"])
    df["importo_eur"] = (df["kwh"] * prezzo).round(2) + 0.0
    df = df.sort_values(["socio_id", "mese"]).reset_index(drop=True)
    df["id"] = np.arange(1, len(df) + 1)
    return df[config.COLONNE["bolletta"]]


def consumi_attivi(consumo_orario: pd.DataFrame, socio: pd.DataFrame) -> pd.DataFrame:
    """Le ore di consumo che contano per la CER: un socio conta dalle 00:00 UTC del
    giorno di adesione (§3.6). Prima di quel giorno i suoi consumi ci sono nel file
    (§1.3), ma non entrano nel calcolo."""
    c = consumo_orario.merge(socio[["id", "data_adesione"]], left_on="socio_id", right_on="id")
    return c[c["ts"] >= c["data_adesione"] + "T00:00:00Z"]


def ripartizione_mensile(produzione_oraria: pd.DataFrame, consumo_orario: pd.DataFrame,
                         socio: pd.DataFrame, parametro: pd.DataFrame) -> pd.DataFrame:
    """Formula del §3.6: energia condivisa ora per ora, divisa tra i soci in
    proporzione ai prelievi, poi sommata per socio e mese.

    Un socio ha una riga per ogni mese a partire da quello della sua adesione; nel
    mese di adesione conta solo dal giorno in cui entra.
    """
    p = dict(zip(parametro["chiave"], parametro["valore"]))
    immessi = produzione_oraria.groupby("ts")["kwh"].sum()

    c = consumi_attivi(consumo_orario, socio).copy()
    prelevati = c.groupby("ts")["kwh"].sum()
    condivisi = np.minimum(immessi.reindex(prelevati.index, fill_value=0.0), prelevati)
    frazione = (condivisi / prelevati).where(prelevati > 0, 0.0)  # quota_s = condivisi × consumo_s / prelevati
    c["quota"] = c["kwh"] * c["ts"].map(frazione)

    df = c.assign(mese=_mese(c["ts"])).groupby(["socio_id", "mese"], as_index=False)["quota"].sum()
    df["kwh_condivisi"] = df["quota"].round(3) + 0.0
    df["incentivo_eur"] = (df["kwh_condivisi"] * (p["tariffa_premio_eur_kwh"] + p["valorizzazione_arera_eur_kwh"])).round(2) + 0.0
    df["co2_evitata_kg"] = (df["kwh_condivisi"] * p["fattore_co2_kg_kwh"]).round(3) + 0.0
    return df.sort_values(["socio_id", "mese"]).reset_index(drop=True)[config.COLONNE["ripartizione_mensile"]]


def anomalia_provvisoria(anomalie_vere: pd.DataFrame) -> pd.DataFrame:
    """Solo le anomalie fisse (il guasto dell'impianto 3 del 1/6/2026), come se il batch
    le avesse trovate. Nel campione è l'unica anomalia; nel completo le altre le
    aggiungerà il batch vero (§4). Gli id ripartono da 1, come nel campione."""
    fisse = pd.DataFrame(produzione.ANOMALIE_FISSE)[["impianto_id", "inizio", "fine", "tipo"]]
    df = anomalie_vere.merge(fisse, on=["impianto_id", "inizio", "fine", "tipo"]).sort_values("inizio")
    df = df.assign(id=np.arange(1, len(df) + 1), score=SCORE_PROVVISORIO, stato=STATO_PROVVISORIO)
    if len(df) != len(fisse):
        raise ValueError(f"anomalie fisse in anomalie_vere: {len(df)}, attese {len(fisse)}")
    return df.reset_index(drop=True)[config.COLONNE["anomalia"]]


def tabelle_provvisorie(conf: dict, tabelle: dict[str, pd.DataFrame], k: dict[int, float],
                        consumi_calcolati: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """Le quattro tabelle calcolate (§4, §7).

    consumi_calcolati: il risultato di consumi.calcola, se genera.py l'ha già calcolato
    al passo 5. Serve per previsione_consumo, così i consumi non si calcolano due volte.
    """
    attesa = produzione.produzione_attesa(tabelle["meteo_orario"], tabelle["impianto"], k)
    previsione_produzione = attesa[["impianto_id", "ts"]].assign(kwh_previsti=attesa["kwh_attesi"].round(3) + 0.0)

    c = consumi_calcolati if consumi_calcolati is not None else consumi.calcola(conf, tabelle["socio"], tabelle["socio_profilo"])
    previsione_consumo = c[["socio_id", "ts"]].assign(kwh_previsti=c["kwh_senza_rumore"].round(3) + 0.0)

    return {
        "previsione_produzione": previsione_produzione[config.COLONNE["previsione_produzione"]],
        "previsione_consumo": previsione_consumo[config.COLONNE["previsione_consumo"]],
        "anomalia": anomalia_provvisoria(tabelle["anomalie_vere"]),
        "ripartizione_mensile": ripartizione_mensile(
            tabelle["produzione_oraria"], tabelle["consumo_orario"], tabelle["socio"], tabelle["parametro"]),
    }


# --- Riepilogo dei trimestri (file di lavoro per i verbali) ---------------------


def _dettaglio_anomalie(anomalie: pd.DataFrame, persi: dict[int, float], nomi: dict[int, str]) -> str:
    """Una frase per anomalia, separate da "; ". "al" è la fine esclusa (§2)."""
    frasi = []
    for a in anomalie.itertuples():
        frasi.append(f"id {a.id} {a.tipo} impianto {a.impianto_id} ({nomi[a.impianto_id]}) dal {a.inizio} al {a.fine}, "
                     f"perdita {a.perdita_pct:g}%, {persi[a.id]:.3f} kWh persi nel trimestre")
    return "; ".join(frasi)


def riepilogo_trimestri(tabelle: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Un trimestre per riga (§4), da nov-dic 2024 a lug-set 2026.

    - produzione per impianto e totale; consumi dei soci attivi (contati dalla loro
      adesione, come nel §3.6);
    - energia condivisa, incentivo (totale e per tipo di socio) e CO2 della parte
      condivisa: somme di ripartizione_mensile sui mesi del trimestre;
    - co2_evitata_kg: produzione totale × fattore, il KPI di comunità del §3.6;
    - soci attivi: aderenti entro la fine del trimestre (non ci sono recessi);
      nuovi soci: aderenti durante il trimestre;
    - anomalie di anomalie_vere che toccano il trimestre (anche iniziate prima o finite
      dopo), contate per tipo; nel dettaglio i kWh persi stimati = produzione attesa
      (previsione_produzione, la formula senza anomalie) − produzione reale, nelle ore
      dell'anomalia che cadono nel trimestre;
    - giorni (in UTC, come i mesi del §2) di massima e minima produzione della comunità.
    """
    p = dict(zip(tabelle["parametro"]["chiave"], tabelle["parametro"]["valore"]))
    socio, rip = tabelle["socio"], tabelle["ripartizione_mensile"]
    nomi = dict(zip(tabelle["impianto"]["id"], tabelle["impianto"]["nome"]))

    prod = tabelle["produzione_oraria"]
    prod_mese = prod.groupby([_mese(prod["ts"]), "impianto_id"])["kwh"].sum().unstack("impianto_id")
    prod_giorno = prod.groupby(prod["ts"].str.slice(0, 10))["kwh"].sum()
    attivi = consumi_attivi(tabelle["consumo_orario"], socio)
    consumi_mese = attivi.groupby(_mese(attivi["ts"]))["kwh"].sum()
    rip = rip.merge(socio[["id", "tipo"]], left_on="socio_id", right_on="id")

    # Produzione attesa e reale ora per ora, per i kWh persi nelle anomalie
    pp = tabelle["previsione_produzione"].merge(prod, on=["impianto_id", "ts"])
    pp["perso"] = pp["kwh_previsti"] - pp["kwh"]
    anomalie = tabelle["anomalie_vere"].sort_values(["inizio", "id"])

    righe = []
    for verbale_id, trimestre, inizio, fine in TRIMESTRI:
        mesi = [m for m in prod_mese.index if inizio <= m < fine]
        riga = {"verbale_id": verbale_id, "trimestre": trimestre}
        for i in sorted(prod_mese.columns):
            riga[f"produzione_impianto_{i}_kwh"] = round(prod_mese.loc[mesi, i].sum(), 3) + 0.0
        riga["produzione_kwh"] = round(prod_mese.loc[mesi].to_numpy().sum(), 3) + 0.0
        riga["consumi_kwh"] = round(consumi_mese.reindex(mesi).sum(), 3) + 0.0

        r = rip[rip["mese"].isin(mesi)]
        riga["kwh_condivisi"] = round(r["kwh_condivisi"].sum(), 3) + 0.0
        riga["incentivo_eur"] = round(r["incentivo_eur"].sum(), 2) + 0.0
        for tipo, colonna in [("famiglia", "famiglie"), ("impresa", "imprese"), ("ente", "enti")]:
            riga[f"incentivo_{colonna}_eur"] = round(r.loc[r["tipo"] == tipo, "incentivo_eur"].sum(), 2) + 0.0
        riga["co2_evitata_kg"] = round(riga["produzione_kwh"] * p["fattore_co2_kg_kwh"], 3) + 0.0
        riga["co2_evitata_condivisa_kg"] = round(r["co2_evitata_kg"].sum(), 3) + 0.0

        riga["soci_attivi"] = int((socio["data_adesione"] < fine).sum())
        riga["nuovi_soci"] = int(((socio["data_adesione"] >= inizio) & (socio["data_adesione"] < fine)).sum())

        t0, t1 = _istante(inizio), _istante(fine)
        dentro = anomalie[(anomalie["inizio"] < t1) & (anomalie["fine"] > t0)]  # toccano il trimestre
        for tipo in TIPI_ANOMALIA:
            riga[f"anomalie_{tipo}"] = int((dentro["tipo"] == tipo).sum())
        persi = {}
        for a in dentro.itertuples():
            ore = (pp["impianto_id"] == a.impianto_id) & (pp["ts"] >= max(a.inizio, t0)) & (pp["ts"] < min(a.fine, t1))
            persi[a.id] = round(pp.loc[ore, "perso"].sum(), 3) + 0.0
        riga["anomalie_dettaglio"] = _dettaglio_anomalie(dentro, persi, nomi)

        giorni = prod_giorno[(prod_giorno.index >= inizio) & (prod_giorno.index < fine)]
        riga["giorno_max_produzione"], riga["kwh_giorno_max"] = giorni.idxmax(), round(giorni.max(), 3) + 0.0
        riga["giorno_min_produzione"], riga["kwh_giorno_min"] = giorni.idxmin(), round(giorni.min(), 3) + 0.0
        righe.append(riga)

    return pd.DataFrame(righe)[config.COLONNE["riepilogo_trimestri"]]


def genera(conf: dict, tabelle: dict[str, pd.DataFrame], k: dict[int, float],
           consumi_calcolati: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    """bolletta, più le tabelle calcolate e il riepilogo se la configurazione li prevede."""
    risultato = {"bolletta": bolletta(tabelle["consumo_orario"], tabelle["socio"], tabelle["parametro"])}
    if conf["tabelle_provvisorie"]:
        risultato.update(tabelle_provvisorie(conf, tabelle, k, consumi_calcolati))
    if conf["riepilogo_trimestri"]:
        risultato["riepilogo_trimestri"] = riepilogo_trimestri({**tabelle, **risultato})
    return risultato
