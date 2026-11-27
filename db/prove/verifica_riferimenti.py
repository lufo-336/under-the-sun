"""Controllo offline della migrazione relazionale, senza PostgreSQL.

Uso:
    python db/prove/verifica_riferimenti.py SCHEMA_INIZIALE.sql MIGRAZIONE.sql CARTELLA_CSV

Controlla:
1. che la migrazione non aggiunga, tolga o rinomini colonne delle 14 tabelle;
2. che le chiavi esterne usino colonne e tabelle esistenti;
3. che il down elimini tutto ciò che crea l'up;
4. che i CSV rispettino tabelle di riferimento e nuove regole.

Non sostituisce una prova vera: la sintassi SQL la controlla solo PostgreSQL.
"""
import csv
import re
import sys
from pathlib import Path

RIFERIMENTI = {
    ("socio", "comune"): "comune",
    ("socio", "tipo"): "tipo_socio",
    ("impianto", "comune"): "comune",
    ("anomalia", "tipo"): "tipo_anomalia",
    ("anomalia", "stato"): "stato_anomalia",
    ("segnalazione", "canale"): "canale_segnalazione",
    ("segnalazione", "stato"): "stato_segnalazione",
    ("segnalazione", "categoria"): "categoria_segnalazione",
    ("segnalazione", "categoria_llm"): "categoria_segnalazione",
    ("segnalazione", "urgenza"): "urgenza",
    ("segnalazione", "urgenza_llm"): "urgenza",
}
CSV_DB = ["impianto", "socio", "parametro", "verbale", "produzione_oraria", "meteo_orario", "consumo_orario",
          "bolletta", "segnalazione", "anomalia", "previsione_produzione", "previsione_consumo",
          "ripartizione_mensile"]
PAROLE_NON_COLONNA = {"PRIMARY", "UNIQUE", "CHECK", "FOREIGN", "CONSTRAINT"}


def senza_commenti(sql):
    return re.sub(r"--[^\n]*", "", sql)


def tabelle(sql):
    """{tabella: [colonne]} dai CREATE TABLE."""
    out = {}
    for m in re.finditer(r"CREATE TABLE (\w+) \(", sql):
        i, livello = m.end(), 1
        while livello:
            livello += {"(": 1, ")": -1}.get(sql[i], 0)
            i += 1
        corpo, parti, corrente, livello = sql[m.end():i - 1], [], "", 0
        for c in corpo:
            livello += {"(": 1, ")": -1}.get(c, 0)
            if c == "," and livello == 0:
                parti.append(corrente)
                corrente = ""
            else:
                corrente += c
        parti.append(corrente)
        nomi = [p.split()[0] for p in parti if p.strip()]
        out[m.group(1)] = [n for n in nomi if n.upper() not in PAROLE_NON_COLONNA]
    return out


def valori_riferimento(up):
    out = {}
    for m in re.finditer(r"INSERT INTO (\w+) \([^)]*\) VALUES(.*?);", up, re.S):
        out[m.group(1)] = {x.replace("''", "'") for x in re.findall(r"\(\s*'((?:[^']|'')*)'", m.group(2))}
    return out


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    iniziale = senza_commenti(Path(sys.argv[1]).read_text(encoding="utf-8")).split("migrate:down")[0]
    testo = Path(sys.argv[2]).read_text(encoding="utf-8")
    up, down = testo.split("-- migrate:down")
    up, down = senza_commenti(up.split("-- migrate:up")[1]), senza_commenti(down)
    cartella = Path(sys.argv[3])
    errori = []

    # 1. Colonne delle tabelle congelate
    base, nuove = tabelle(iniziale), tabelle(up)
    if len(base) != 14:
        errori.append(f"attese 14 tabelle nello schema iniziale, trovate {len(base)}")
    if set(base) & set(nuove):
        errori.append(f"tabelle già esistenti ricreate: {set(base) & set(nuove)}")
    if re.search(r"\b(ADD|DROP|RENAME)\s+COLUMN\b", up + down, re.I):
        errori.append("la migrazione aggiunge, toglie o rinomina colonne")
    if re.search(r"DROP CONSTRAINT\s+(?!uq_|fk_|ck_)", up + down):
        errori.append("la migrazione elimina un vincolo della prima migrazione")

    # 2. Chiavi esterne
    tutte = {**base, **nuove}
    n_fk = 0
    for blocco in re.finditer(r"ALTER TABLE (\w+)(.*?);", up, re.S):
        for fk in re.finditer(r"FOREIGN KEY \((\w+)\)\s+REFERENCES (\w+) \((\w+)\)", blocco.group(2)):
            n_fk += 1
            tab, col, dest, col_dest = blocco.group(1), fk.group(1), fk.group(2), fk.group(3)
            if col not in tutte.get(tab, []):
                errori.append(f"FK: {tab}.{col} non esiste")
            if col_dest not in tutte.get(dest, []):
                errori.append(f"FK: {dest}.{col_dest} non esiste")

    # 3. Simmetria up/down
    for tipo, creati, elimina in [
        ("vista", re.findall(r"CREATE VIEW (\w+)", up), r"DROP VIEW ([\w, \n]+);"),
        ("funzione", re.findall(r"CREATE FUNCTION (\w+)", up), r"DROP FUNCTION (\w+)"),
        ("trigger", re.findall(r"CREATE TRIGGER (\w+)", up), r"DROP TRIGGER (\w+)"),
        ("tabella", list(nuove), r"DROP TABLE ([\w, \n]+);"),
        ("vincolo", re.findall(r"ADD CONSTRAINT (\w+)", up), r"DROP CONSTRAINT (\w+)"),
    ]:
        tolti = set()
        for x in re.findall(elimina, down):
            tolti |= {p.strip() for p in x.split(",")}
        if set(creati) != tolti:
            errori.append(f"{tipo}: differenza tra up e down {set(creati) ^ tolti}")
    # Gli indici sulle tabelle nuove spariscono con le tabelle.
    indici = {}
    for nome, tab in re.findall(r"CREATE (?:UNIQUE )?INDEX (\w+)\s+ON (\w+)", up):
        indici[nome] = tab
    tolti = set()
    for x in re.findall(r"DROP INDEX ([\w, \n]+);", down):
        tolti |= {p.strip() for p in x.split(",")}
    attesi = {n for n, t in indici.items() if t in base}
    if attesi != tolti:
        errori.append(f"indici: differenza tra up e down {attesi ^ tolti}")

    # 4. CSV
    ref = valori_riferimento(up)
    dati = {}
    for tab in CSV_DB:
        f = cartella / f"{tab}.csv"
        if not f.exists():
            errori.append(f"manca {f.name}")
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            r = csv.DictReader(fh)
            if r.fieldnames != base[tab]:
                errori.append(f"{tab}: intestazioni diverse dallo schema")
            if tab in ("socio", "impianto", "anomalia", "segnalazione"):
                dati[tab] = list(r)
    for (tab, col), dest in RIFERIMENTI.items():
        for v in {x.get(col, "") for x in dati.get(tab, [])} - {""}:
            if v not in ref.get(dest, set()):
                errori.append(f"{tab}.{col}: '{v}' non è in {dest}")
    for x in dati.get("segnalazione", []):
        if (x["canale"] == "interno") != (x["socio_id"] == ""):
            errori.append(f"segnalazione {x['id']}: regola canale interno / socio violata")
    coppie = [(x["impianto_id"], x["inizio"]) for x in dati.get("anomalia", [])]
    if len(coppie) != len(set(coppie)):
        errori.append("anomalia: coppie (impianto_id, inizio) doppie")

    print(f"Tabelle esistenti: {len(base)} | nuove: {len(nuove)} | chiavi esterne aggiunte: {n_fk} | "
          f"indici: {len(indici)} | trigger: {len(re.findall('CREATE TRIGGER', up))}")
    print("Righe controllate: " + ", ".join(f"{k} {len(v)}" for k, v in dati.items()))
    if errori:
        print(f"\n{len(errori)} PROBLEMI:")
        for e in errori[:40]:
            print(" -", e)
        sys.exit(1)
    print("Controllo offline superato. La migrazione va comunque provata su PostgreSQL.")


if __name__ == "__main__":
    main()
