# UnderTheSun – Data dictionary

Versione 1 (campione per il SAL 1), 19 novembre 2026. Team dati: Francesco, Giuseppe, Cecilia.

Le regole complete di generazione sono in `data/GUIDA-DATASET.md`. L'impostazione di questo documento riprende il dizionario preparato da Giuseppe.

## Origine dei dati

| Tipo | File | Origine |
|---|---|---|
| Reale | `meteo_orario.csv` | Open-Meteo, Historical Weather API (CC BY 4.0; dati ERA5, Copernicus) |
| Calcolato da dati reali | `produzione_oraria.csv` | Modello fotovoltaico applicato al meteo di Open-Meteo (guida §3.2), con controllo su PVGIS 5.3 (JRC, Commissione europea) |
| Sintetico | `consumo_orario.csv` | Profili orari per tipo di socio. Nel campione i volumi sono **provvisori**; nel dataset completo saranno tarati sui dati ARERA della provincia di Torino (guida §3.4) |
| Fonti ufficiali | `parametro.csv` | ISPRA, DM MASE 414/2023, ARERA, PVGIS: la fonte di ogni valore è nella colonna `fonte` |
| Sintetico | tutti gli altri file | Generati dagli script in `data/generazione/` con seed 42. I testi sono scritti con un LLM e rivisti a mano |

Sono **di fantasia** i nomi di soci, imprese ed enti e i testi. Sono **ipotesi plausibili** impianti, coordinate, prezzi e regole di ripartizione. Va dichiarato nella documentazione e nella demo.

## Convenzioni

- **Formato:** CSV in UTF-8 senza BOM, separatore `,`, decimali con il punto, intestazioni in `snake_case`. C'è un file per tabella, con il nome della tabella.
- **Orari:** in UTC, nel formato `2026-06-01T10:00:00Z`. `ts` è l'inizio dell'ora e `kwh` è l'energia di quell'ora: nell'esempio, dalle 10:00 alle 11:00 UTC.
- **Date:** formato `YYYY-MM-DD`. `mese` è il primo giorno del mese, calcolato in UTC.
- **Intervalli:** `inizio` è incluso, `fine` è esclusa.
- **Valori mancanti:** cella vuota.
- **Unità:** sono nel nome della colonna (`_kwh`, `_eur`, `_wm2`, `_c`, `_pct`, `_cm`, `_gradi`, `_kg`). Le colonne che si chiamano solo `kwh` o `kwp` hanno già l'unità nel nome.
- **Contenuto del campione:** dal 1 al 30 giugno 2026, cioè 720 ore, con gli impianti 1–3 e 20 soci. Gli ID sono gli stessi del dataset completo (8 impianti, 240 soci).
- **Per rigenerare il campione:** dalla cartella `data/`, `python generazione/genera.py --config piccola`.

> **File etichetta 🏷:** contengono le risposte corrette per valutare i modelli (rilevamento anomalie, classificazione dei testi). Non vanno nel database, non si usano come input dei modelli e non si mostrano nel portale.

---

## Tabelle del database

### impianto.csv (3 righe)

| Colonna | Tipo | Descrizione |
|---|---|---|
| id | intero | Identificativo: 1–3 nel campione, 1–8 nel dataset completo |
| nome | testo | Nome dell'impianto |
| comune | testo | Comune del Pinerolese |
| lat, lon | decimale | Coordinate in gradi decimali (centro del comune) |
| kwp | decimale | Potenza di picco |
| inclinazione_gradi | decimale | Inclinazione dei moduli (0 = orizzontali) |
| azimut_gradi | decimale | Orientamento: 0 = sud, −90 = est, +90 = ovest |
| data_attivazione | data | Entrata in esercizio |

### socio.csv (20 righe)

| Colonna | Tipo | Descrizione |
|---|---|---|
| id | intero | Identificativo, uguale a quello del dataset completo |
| nome | testo | Famiglia, impresa o ente (di fantasia) |
| tipo | testo | `famiglia`, `impresa`, `ente` |
| comune | testo | Uno degli 8 comuni della comunità |
| data_adesione | data | Ingresso nella comunità. La ripartizione conta il socio da questa data |

Il campione comprende 14 famiglie, 4 imprese (bar, panificio, officina, parrucchiere) e 2 enti (la scuola di Pinerolo e gli uffici comunali di San Secondo di Pinerolo).

### consumo_orario.csv (14.400 righe = 20 soci × 720 ore)

| Colonna | Tipo | Descrizione |
|---|---|---|
| socio_id | intero | Socio |
| ts | data e ora (UTC) | Inizio dell'ora |
| kwh | decimale | Energia prelevata dalla rete nell'ora |

⚠ **Volumi provvisori.** Nel campione i consumi annui sono 2.700 kWh per una famiglia, 15.000 per un'impresa e 40.000 per un ente. Ogni volume annuo, moltiplicato per la scala del socio, è distribuito sull'anno dal 1/9/2025 al 31/8/2026 seguendo giorni e orari di apertura: giugno è la parte che gli spetta. Per questo la scuola, che a giugno fa lezione solo 6 giorni (il 1° giugno c'è il ponte e le lezioni finiscono il 10), consuma meno della media. I consumi non sono ancora riscalati sulle fasce F1/F2/F3 di ARERA.

### produzione_oraria.csv (2.160 righe = 3 impianti × 720 ore)

| Colonna | Tipo | Descrizione |
|---|---|---|
| impianto_id | intero | Impianto |
| ts | data e ora (UTC) | Inizio dell'ora |
| kwh | decimale | Energia prodotta nell'ora, **comprese le anomalie**: è il dato "misurato" |

⚠ **Senza taratura.** Nel campione il modello non è ancora tarato su PVGIS e rende circa il 5% più di PVGIS a parità di irraggiamento. Nel dataset completo la produzione di giugno calerà quindi di circa il 5%. Giugno 2026, inoltre, è stato più soleggiato della media: la produzione del mese supera la media PVGIS di giugno del 15–16%.

### meteo_orario.csv (2.160 righe = 3 impianti × 720 ore)

| Colonna | Tipo | Descrizione |
|---|---|---|
| impianto_id | intero | Impianto (il meteo è quello delle sue coordinate) |
| ts | data e ora (UTC) | Inizio dell'ora |
| irraggiamento_wm2 | decimale | Irraggiamento sul piano orizzontale, media dell'ora (W/m²) |
| irraggiamento_pannelli_wm2 | decimale | Irraggiamento sul piano dei moduli dell'impianto, media dell'ora (W/m²) |
| temperatura_c | decimale | Temperatura dell'aria a 2 m (°C) |
| nuvolosita_pct | decimale | Copertura nuvolosa (%) |
| neve_cm | decimale | Neve caduta nell'ora (cm) |

### bolletta.csv (20 righe = 20 soci × 1 mese)

| Colonna | Tipo | Descrizione |
|---|---|---|
| id | intero | Identificativo |
| socio_id | intero | Socio |
| mese | data | Primo giorno del mese |
| kwh | decimale | Consumo del mese |
| importo_eur | decimale | `kwh` × prezzo dell'energia per il tipo di socio (vedi `parametro.csv`) |

### parametro.csv (8 righe)

| Colonna | Tipo | Descrizione |
|---|---|---|
| chiave | testo | Nome del parametro, con l'unità nel nome |
| valore | decimale | Valore |
| fonte | testo | Origine del valore |

| Chiave | Significato |
|---|---|
| `fattore_co2_kg_kwh` | CO2 evitata per ogni kWh rinnovabile (ISPRA) |
| `tariffa_premio_eur_kwh` | Incentivo GSE sull'energia condivisa |
| `valorizzazione_arera_eur_kwh` | Corrispettivo ARERA sull'energia condivisa (da aggiornare) |
| `prezzo_energia_famiglia_eur_kwh` | Prezzo finale medio per le famiglie |
| `prezzo_energia_impresa_eur_kwh` | Prezzo per le imprese (provvisorio, uguale alle famiglie) |
| `prezzo_energia_ente_eur_kwh` | Prezzo per gli enti (provvisorio, uguale alle famiglie) |
| `perdite_sistema_pct` | Perdite dell'impianto fotovoltaico (PVGIS) |
| `coeff_temperatura_pct_c` | Calo di rendimento dei moduli per ogni °C sopra 25 |

### segnalazione.csv (15 righe) – testo non strutturato

| Colonna | Tipo | Descrizione |
|---|---|---|
| id | intero | Identificativo |
| socio_id | intero | Socio che scrive; vuoto per le comunicazioni interne |
| impianto_id | intero | Impianto in uso: quello indicato dal socio, altrimenti quello estratto dall'LLM. L'operatore può correggerlo |
| impianto_id_llm | intero | Impianto estratto dall'LLM, mai modificato. **Da confermare** alla prossima riunione |
| ts | data e ora (UTC) | Momento dell'invio |
| canale | testo | `email`, `portale`, `interno` (comunicazioni guasti dal sistema di monitoraggio, dal gestore o dai tecnici) |
| testo | testo | Testo libero |
| categoria_llm, urgenza_llm | testo | Risposta dell'LLM, mai modificata |
| categoria, urgenza | testo | Valori in uso: l'operatore corregge queste |
| stato | testo | `aperta`, `in_corso`, `chiusa` |

- **Categorie:** `guasto_impianto`, `bolletta_pagamenti`, `incentivi_ripartizione`, `adesione_recesso`, `informazioni`, `reclamo`.
- **Urgenze:** `alta`, `media`, `bassa`.

⚠ **Colonne LLM nel campione.** Sono riempite a mano. In alcuni casi `categoria` è diversa da `categoria_llm`, per simulare una correzione dell'operatore.

### verbale.csv (1 riga) – testo non strutturato

| Colonna | Tipo | Descrizione |
|---|---|---|
| id | intero | Identificativo |
| data_assemblea | data | Data dell'assemblea |
| testo | testo | Verbale completo, con gli a capo racchiusi tra virgolette come previsto dal formato CSV. I numeri citati vengono dai dati del campione |
| sintesi | testo | Vuota: la scrive l'LLM |

Nel campione c'è il verbale dell'assemblea del 9 luglio 2026 (id 7), che commenta i dati di giugno degli impianti 1–3, il guasto del 1° giugno e le segnalazioni del mese.

---

## Tabelle calcolate (provvisorie nel campione)

Nel progetto queste tabelle le scrivono i batch del team dati. Nel campione contengono valori provvisori, utili ai WSA per costruire le pagine.

| File | Righe | Colonne | Come sono calcolate nel campione |
|---|---|---|---|
| `previsione_produzione.csv` | 2.160 | `impianto_id`, `ts`, `kwh_previsti` | La stessa formula della produzione, senza anomalie |
| `previsione_consumo.csv` | 14.400 | `socio_id`, `ts`, `kwh_previsti` | Il profilo del socio, senza rumore |
| `anomalia.csv` | 1 | `id`, `impianto_id`, `inizio`, `fine`, `tipo`, `score`, `stato` | Il guasto dell'impianto 3 del 1 giugno, come se il batch l'avesse trovato |
| `ripartizione_mensile.csv` | 20 | `socio_id`, `mese`, `kwh_condivisi`, `incentivo_eur`, `co2_evitata_kg` | Formula della guida §3.6 applicata a giugno |

**Valori delle colonne di `anomalia`:**

- `fine`: vuota se l'anomalia è ancora in corso;
- `tipo`: `guasto`, `sporcizia`, `stringa`, `neve`, oppure vuoto se il modello non riconosce la causa;
- `score`: da 0 a 1;
- `stato`: `aperta` o `chiusa` (la chiude l'operatore).

⚠ **Ripartizione del campione.** È calcolata su 3 impianti e 20 soci, quindi l'energia condivisa è quasi uguale ai consumi delle ore di sole. Nel dataset completo i valori di giugno cambieranno, perché dipendono da tutti gli 8 impianti e i 240 soci.

---

## File di lavoro (non vanno nel database)

### anomalie_vere.csv 🏷 (1 riga)

| Colonna | Tipo | Descrizione |
|---|---|---|
| id | intero | Identificativo |
| impianto_id | intero | Impianto colpito |
| inizio, fine | data e ora (UTC) | Periodo dell'anomalia (`fine` esclusa) |
| tipo | testo | `guasto`, `stringa`, `sporcizia`, `neve` |
| perdita_pct | decimale | Quota di produzione persa (100 = produzione a zero) |

Nel campione c'è una sola riga: il guasto dell'impianto 3 dal `2026-06-01T11:00:00Z` al `2026-06-01T15:00:00Z`, con perdita del 100%.

### socio_profilo.csv (20 righe)

| Colonna | Tipo | Descrizione |
|---|---|---|
| socio_id | intero | Socio |
| profilo | testo | Profilo di consumo (per esempio `famiglia`, `bar`, `scuola`) |
| ateco | testo | Codice ATECO di riferimento; vuoto per le famiglie |
| scala | decimale | Moltiplicatore del consumo del socio (media 1) |

### segnalazione_etichette.csv 🏷 (solo nel dataset completo)

Contiene le colonne `segnalazione_id`, `categoria_vera`, `urgenza_vera` e `impianto_id_vero`. Serve a misurare l'accuratezza dell'LLM.

---

## Differenze rispetto a `docs/architettura.md` (da approvare al SAL 1)

1. **`impianto`:** si aggiungono `inclinazione_gradi` e `azimut_gradi`, necessarie per i calcoli con Open-Meteo e PVGIS.
2. **`meteo_orario`:** le unità entrano nei nomi delle colonne (`irraggiamento_wm2`, `temperatura_c`, `nuvolosita_pct`) e si aggiungono `irraggiamento_pannelli_wm2` e `neve_cm`. Nessuna API espone questa tabella.
3. **`segnalazione`:** si aggiunge `impianto_id_llm` (da confermare). `socio_id` può essere vuoto, e il canale `interno` serve per le comunicazioni guasti.

## Usi suggeriti

| Requisito del progetto | File |
|---|---|
| Previsione della produzione | `produzione_oraria` + `meteo_orario` + `impianto` → `previsione_produzione` |
| Previsione dei consumi | `consumo_orario` + `socio` (+ `meteo_orario`) → `previsione_consumo` |
| Rilevamento anomalie | `produzione_oraria` confrontata con l'atteso (`meteo_orario` + `impianto`) → `anomalia`; valutazione con `anomalie_vere` 🏷 |
| Ripartizione CER, incentivi, CO2 | `produzione_oraria` + `consumo_orario` + `socio.data_adesione` + `parametro` → `ripartizione_mensile` |
| Portale soci | `socio`, `consumo_orario`, `bolletta`, `ripartizione_mensile` |
| Classificazione ed estrazione di informazioni | `segnalazione.testo` → `categoria_llm`, `urgenza_llm`, `impianto_id_llm`; valutazione con `segnalazione_etichette` 🏷 |
| Sintesi | `verbale.testo` → `sintesi` |
| Simulatore di risparmio | `consumo_orario` + `produzione_oraria` + `parametro` (guida §3.6) |

## Fonti

- Open-Meteo, Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api
- PVGIS 5.3 (JRC, Commissione europea): https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/pvgis-releases/pvgis-53_en
- ARERA, consumi dei clienti domestici: https://www.arera.it/dati-e-statistiche/dettaglio/analisi-dei-consumi-dei-clienti-domestici
- ISPRA, Rapporto 430/2026: https://www.isprambiente.gov.it/files2026/pubblicazioni/rapporti/r430-2026-2.pdf
- MASE, DM 414/2023 sulle CACER: https://greencam.unioncamere.it/wp-content/uploads/2025/06/Strumenti-di-sostegno-per-le-CACER-DM-414-del-2023_Ministero-dell_Ambiente-e-della-Sicurezza-Energetica.pdf
