"""Derivate: bolletta e, solo nel campione, le tabelle calcolate provvisorie (guida §4 e §7).

Tutto si calcola dai valori così come sono scritti nei CSV (energia a 3 decimali):
chi rifà il conto partendo dai file ottiene gli stessi numeri.

Tabelle provvisorie del campione (§7), che nel progetto scriveranno i batch:
- previsione_produzione: la formula della produzione senza anomalie;
- previsione_consumo: il profilo del socio senza rumore;
- anomalia: il guasto dell'impianto 3 come se il batch l'avesse trovato (score 0.97, aperta);
- ripartizione_mensile: la formula del §3.6.
"""

import numpy as np
import pandas as pd

import config
import consumi
import produzione

SCORE_PROVVISORIO = 0.97  # come in api.md
STATO_PROVVISORIO = "aperta"


def _mese(ts: pd.Series) -> pd.Series:
    """Primo giorno del mese in UTC, come date_trunc('month', ts) (§2)."""
    return ts.str.slice(0, 7) + "-01"  # "2026-06-01T10:00:00Z" -> "2026-06-01"


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


def ripartizione_mensile(produzione_oraria: pd.DataFrame, consumo_orario: pd.DataFrame,
                         socio: pd.DataFrame, parametro: pd.DataFrame) -> pd.DataFrame:
    """Formula del §3.6: energia condivisa ora per ora, divisa tra i soci in
    proporzione ai prelievi, poi sommata per socio e mese."""
    p = dict(zip(parametro["chiave"], parametro["valore"]))
    immessi = produzione_oraria.groupby("ts")["kwh"].sum()

    # Un socio conta dalle 00:00 UTC del giorno di adesione
    c = consumo_orario.merge(socio[["id", "data_adesione"]], left_on="socio_id", right_on="id")
    c = c[c["ts"] >= c["data_adesione"] + "T00:00:00Z"].copy()
    prelevati = c.groupby("ts")["kwh"].sum()
    condivisi = np.minimum(immessi.reindex(prelevati.index, fill_value=0.0), prelevati)
    frazione = (condivisi / prelevati).where(prelevati > 0, 0.0)  # quota_s = condivisi × consumo_s / prelevati
    c["quota"] = c["kwh"] * c["ts"].map(frazione)

    df = c.assign(mese=_mese(c["ts"])).groupby(["socio_id", "mese"], as_index=False)["quota"].sum()
    df["kwh_condivisi"] = df["quota"].round(3) + 0.0
    df["incentivo_eur"] = (df["kwh_condivisi"] * (p["tariffa_premio_eur_kwh"] + p["valorizzazione_arera_eur_kwh"])).round(2) + 0.0
    df["co2_evitata_kg"] = (df["kwh_condivisi"] * p["fattore_co2_kg_kwh"]).round(3) + 0.0
    return df.sort_values(["socio_id", "mese"]).reset_index(drop=True)[config.COLONNE["ripartizione_mensile"]]


def tabelle_provvisorie(conf: dict, tabelle: dict[str, pd.DataFrame], k: dict[int, float]) -> dict[str, pd.DataFrame]:
    """Le quattro tabelle calcolate del campione (§7)."""
    attesa = produzione.produzione_attesa(tabelle["meteo_orario"], tabelle["impianto"], k)
    previsione_produzione = attesa[["impianto_id", "ts"]].assign(kwh_previsti=attesa["kwh_attesi"].round(3) + 0.0)

    c = consumi.calcola(conf, tabelle["socio"], tabelle["socio_profilo"])
    previsione_consumo = c[["socio_id", "ts"]].assign(kwh_previsti=c["kwh_senza_rumore"].round(3) + 0.0)

    anomalia = tabelle["anomalie_vere"][["id", "impianto_id", "inizio", "fine", "tipo"]].assign(
        score=SCORE_PROVVISORIO, stato=STATO_PROVVISORIO)

    return {
        "previsione_produzione": previsione_produzione[config.COLONNE["previsione_produzione"]],
        "previsione_consumo": previsione_consumo[config.COLONNE["previsione_consumo"]],
        "anomalia": anomalia[config.COLONNE["anomalia"]],
        "ripartizione_mensile": ripartizione_mensile(
            tabelle["produzione_oraria"], tabelle["consumo_orario"], tabelle["socio"], tabelle["parametro"]),
    }


def genera(conf: dict, tabelle: dict[str, pd.DataFrame], k: dict[int, float]) -> dict[str, pd.DataFrame]:
    """bolletta, più le tabelle provvisorie se la configurazione le prevede."""
    risultato = {"bolletta": bolletta(tabelle["consumo_orario"], tabelle["socio"], tabelle["parametro"])}
    if conf["tabelle_provvisorie"]:
        risultato.update(tabelle_provvisorie(conf, tabelle, k))
    return risultato
