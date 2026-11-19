"""Generatore del dataset UnderTheSun.

Uso, dalla cartella data/ con l'ambiente virtuale attivo:
    python generazione/genera.py --config piccola                      -> data/esempi/
    python generazione/genera.py --config completa                     -> data/output/
    python generazione/genera.py --config piccola --solo-intestazioni  -> CSV vuoti

I moduli (anagrafiche, meteo, pvgis, produzione, consumi, derivate) si aggiungono
uno alla volta, nell'ordine di CLAUDE.md. Per ora c'è solo --solo-intestazioni.
"""

import argparse
from pathlib import Path

import pandas as pd

import config


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


def scrivi_intestazioni(cartella: Path) -> None:
    """Scrive i CSV delle tabelle del database con la sola riga di intestazione."""
    for nome in config.TABELLE_DB:
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

    raise SystemExit("Nessun modulo ancora pronto: per ora usa --solo-intestazioni.")


if __name__ == "__main__":
    main()
