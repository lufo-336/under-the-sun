"""Generatore del dataset UnderTheSun.

Uso, dalla cartella data/ con l'ambiente virtuale attivo:
    python generazione/genera.py --config piccola                      -> data/esempi/
    python generazione/genera.py --config completa                     -> data/output/
    python generazione/genera.py --config piccola --solo-intestazioni  -> CSV vuoti

I moduli (anagrafiche, meteo, pvgis, produzione, consumi, derivate) si aggiungono
uno alla volta, nell'ordine di CLAUDE.md. Per ora ci sono i passi 1-4:
anagrafiche, meteo, pvgis e produzione.
"""

import argparse
from pathlib import Path

import pandas as pd
import requests

import anagrafiche
import config
import meteo
import produzione
import pvgis


def scrivi_csv(df: pd.DataFrame, nome: str, cartella: Path) -> Path:
    """Scrive una tabella con le regole del §2.

    - UTF-8 senza BOM, separatore ",", decimali con ".";
    - fine riga "\\n" su ogni sistema operativo, così gli hash non cambiano
      tra Windows e Mac;
    - valori mancanti come cella vuota;
    - colonne esattamente quelle del §4, nello stesso ordine.
    """
    attese = config.COLONNE[nome]
    if list(df.columns) != attese:
        raise ValueError(f"{nome}: colonne {list(df.columns)}, attese {attese}")
    cartella.mkdir(parents=True, exist_ok=True)
    percorso = cartella / f"{nome}.csv"
    df.to_csv(percorso, index=False, encoding="utf-8", lineterminator="\n", na_rep="")
    return percorso


def scrivi_tutte(tabelle: dict[str, pd.DataFrame], cartella: Path) -> None:
    """Scrive le tabelle di un passo e ne stampa il numero di righe."""
    for nome, tabella in tabelle.items():
        scrivi_csv(tabella, nome, cartella)
        print(f"  {nome}.csv: {len(tabella)} righe")


def scrivi_intestazioni(cartella: Path) -> None:
    """Scrive i CSV delle tabelle del database con la sola riga di intestazione.

    I file che esistono già non si toccano: alcuni contengono dati, e
    segnalazione.csv e verbale.csv sono scritti a mano.
    """
    for nome in config.TABELLE_DB:
        if (cartella / f"{nome}.csv").exists():
            print(f"  {nome}.csv: esiste già, non lo tocco")
            continue
        vuota = pd.DataFrame(columns=config.COLONNE[nome])
        percorso = scrivi_csv(vuota, nome, cartella)
        print(f"  {percorso.name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generatore del dataset UnderTheSun")
    parser.add_argument("--config", choices=list(config.CONFIGURAZIONI), required=True)
    parser.add_argument(
        "--solo-intestazioni",
        action="store_true",
        help="scrive solo le intestazioni dei CSV delle tabelle del database",
    )
    args = parser.parse_args()

    conf = config.CONFIGURAZIONI[args.config]
    cartella = conf["cartella"]

    if args.solo_intestazioni:
        print(f"Intestazioni in {cartella}:")
        scrivi_intestazioni(cartella)
        return

    print(f"Configurazione {args.config}: {conf['descrizione']}")
    print(f"Cartella: {cartella}")

    print("\n1. Anagrafiche")
    tabelle_anagrafiche = anagrafiche.genera(conf)
    scrivi_tutte(tabelle_anagrafiche, cartella)

    print("\n  Coordinate degli impianti rispetto al centro del comune (geocoding Open-Meteo):")
    try:
        controllo = anagrafiche.controlla_coordinate(anagrafiche.tabella_impianti())
        print(controllo.to_string(index=False))
    except requests.RequestException as errore:
        print(f"  controllo saltato, Open-Meteo non raggiungibile: {errore}")

    impianti = tabelle_anagrafiche["impianto"]

    print("\n2. Meteo (Open-Meteo)")
    tabelle_meteo = meteo.genera(conf, impianti)
    scrivi_tutte(tabelle_meteo, cartella)

    print("\n3. PVGIS (riferimento per la produzione)")
    k = pvgis.k_impianti(conf, impianti)
    print(f"  k_impianto: {k}")
    print("  PVcalc, medie 2005-2023:")
    print(pvgis.riepilogo_pvcalc(impianti).to_string(index=False))

    print("\n4. Produzione")
    scrivi_tutte(produzione.genera(conf, impianti, tabelle_meteo["meteo_orario"], k), cartella)


if __name__ == "__main__":
    main()
