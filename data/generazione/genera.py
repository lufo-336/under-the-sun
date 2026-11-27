"""Generatore del dataset UnderTheSun.

Uso, dalla cartella data/ con l'ambiente virtuale attivo:
    python generazione/genera.py --config piccola                      -> data/esempi/
    python generazione/genera.py --config completa                     -> data/output/
    python generazione/genera.py --config piccola --solo-intestazioni  -> CSV vuoti
    python generazione/genera.py --config completa --fino-a produzione -> solo i passi 1-4

I moduli si aggiungono uno alla volta, nell'ordine di CLAUDE.md. Ci sono i passi 1-7:
anagrafiche, meteo, pvgis, produzione, consumi, derivate e testi.

Testi (passo 7):
- completo: segnalazione, segnalazione_etichette (con _sviluppo) e verbale si
  rigenerano ogni volta dal sorgente fisso in data/testi/ (testi.py), che non si tocca;
- campione: segnalazione.csv e verbale.csv li ha scritti a mano Francesco e il
  generatore non li tocca (ne scriverebbe solo le intestazioni, se mancassero).
"""

import argparse
from pathlib import Path

import pandas as pd
import requests

import anagrafiche
import config
import consumi
import derivate
import meteo
import produzione
import pvgis
import testi


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


TESTI = ["segnalazione", "verbale"]  # tabelle di testo: non le scrive il generatore numerico


def scrivi_intestazioni(cartella: Path, nomi: list[str] = config.TABELLE_DB) -> None:
    """Scrive i CSV delle tabelle indicate con la sola riga di intestazione.

    I file che esistono già non si toccano: alcuni contengono dati, e
    segnalazione.csv e verbale.csv sono scritti a mano.
    """
    for nome in nomi:
        if (cartella / f"{nome}.csv").exists():
            print(f"  {nome}.csv: esiste già, non lo tocco")
            continue
        vuota = pd.DataFrame(columns=config.COLONNE[nome])
        percorso = scrivi_csv(vuota, nome, cartella)
        print(f"  {percorso.name}")


PASSI = ["anagrafiche", "meteo", "pvgis", "produzione", "consumi", "derivate", "testi"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Generatore del dataset UnderTheSun")
    parser.add_argument("--config", choices=list(config.CONFIGURAZIONI), required=True)
    parser.add_argument(
        "--solo-intestazioni",
        action="store_true",
        help="scrive solo le intestazioni dei CSV delle tabelle del database",
    )
    parser.add_argument(
        "--fino-a",
        choices=PASSI,
        default=PASSI[-1],
        help="si ferma dopo questo passo (di norma li fa tutti)",
    )
    args = parser.parse_args()

    def fine(passo: str) -> bool:
        """True se ci si ferma dopo questo passo (opzione --fino-a)."""
        if args.fino_a == passo:
            print(f"\nFermo dopo il passo '{passo}' (--fino-a {passo}).")
            return True
        return False

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
    if fine("anagrafiche"):
        return

    impianti = tabelle_anagrafiche["impianto"]

    print("\n2. Meteo (Open-Meteo)")
    tabelle_meteo = meteo.genera(conf, impianti)
    scrivi_tutte(tabelle_meteo, cartella)
    print("\n  Celle della griglia meteo (§1.1):")
    print(meteo.celle(impianti).to_string(index=False))
    if fine("meteo"):
        return

    print("\n3. PVGIS (riferimento per la produzione)")
    k = pvgis.k_impianti(conf, impianti)
    print(f"  k_impianto: {k}")
    if conf["taratura_pvgis"]:
        print(f"  Confronto {pvgis.ANNO} tra modello tarato e PVGIS seriescalc (MAE e correlazione orari):")
        print(pvgis.validazione(impianti).to_string(index=False))
    print("  PVcalc, medie 2005-2023:")
    print(pvgis.riepilogo_pvcalc(impianti).to_string(index=False))
    if fine("pvgis"):
        return

    print("\n4. Produzione")
    tabelle_produzione = produzione.genera(conf, impianti, tabelle_meteo["meteo_orario"], k)
    scrivi_tutte(tabelle_produzione, cartella)
    if fine("produzione"):
        return

    print("\n5. Consumi")
    # Calcolati una volta sola: servono anche per previsione_consumo al passo 6
    consumi_calcolati = consumi.calcola(conf, tabelle_anagrafiche["socio"], tabelle_anagrafiche["socio_profilo"])
    tabelle_consumi = consumi.genera(conf, tabelle_anagrafiche["socio"], tabelle_anagrafiche["socio_profilo"],
                                     consumi_calcolati)
    scrivi_tutte(tabelle_consumi, cartella)
    if fine("consumi"):
        return

    print("\n6. Derivate (bolletta, tabelle calcolate e riepilogo dei trimestri)")
    tutte = {**tabelle_anagrafiche, **tabelle_meteo, **tabelle_produzione, **tabelle_consumi}
    scrivi_tutte(derivate.genera(conf, tutte, k, consumi_calcolati), cartella)
    if fine("derivate"):
        return

    print("\n7. Testi (segnalazioni e verbali)")
    if conf["testi_da_sorgente"]:
        print(f"  sorgente: {testi.SORGENTE_SEGNALAZIONI.relative_to(config.CARTELLA_DATA).as_posix()} "
              f"e {testi.CARTELLA_VERBALI.relative_to(config.CARTELLA_DATA).as_posix()}/")
        scrivi_tutte(testi.genera(), cartella)
    else:
        scrivi_intestazioni(cartella, TESTI)


if __name__ == "__main__":
    main()
