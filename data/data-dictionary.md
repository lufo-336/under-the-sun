# UnderTheSun – Data dictionary

Versione 1.1, 27 novembre 2026: campione per il SAL 1 e dataset completo (tabelle e file di lavoro allineati alla guida v1.10, §4). Versione 1 del 19 novembre 2026. Team dati: Francesco, Giuseppe, Cecilia.

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
- **Dataset completo:** dal 1 novembre 2024 al 31 ottobre 2026 (17.520 ore), 8 impianti e 240 soci. Si rigenera con `python generazione/genera.py --config completa` e si condivide come zip sul Drive del gruppo (guida §5). Dove il completo è diverso dal campione, le schede qui sotto lo dicono.

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
| impianto_id_llm | intero | Impianto estratto dall'LLM, mai modificato (accolto nello schema il 23 novembre) |
| ts | data e ora (UTC) | Momento dell'invio |
| canale | testo | `email`, `portale`, `interno` (comunicazioni guasti dal sistema di monitoraggio, dal gestore o dai tecnici) |
| testo | testo | Testo libero |
| categoria_llm, urgenza_llm | testo | Risposta dell'LLM, mai modificata |
| categoria, urgenza | testo | Valori in uso: l'operatore corregge queste |
| stato | testo | `aperta`, `in_corso`, `chiusa` |

- **Categorie:** `guasto_impianto`, `bolletta_pagamenti`, `incentivi_ripartizione`, `adesione_recesso`, `informazioni`, `reclamo`.
- **Urgenze:** `alta`, `media`, `bassa`.

⚠ **Colonne LLM nel campione.** Sono riempite a mano. In alcuni casi `categoria` è diversa da `categoria_llm`, per simulare una correzione dell'operatore.

**Nel dataset completo** (282 righe, da novembre 2024 a ottobre 2026):

- i testi vengono dal file sorgente `data/testi/segnalazioni_sorgente.csv`, scritto dal team dati; le righe sono in ordine di `ts`, con `id` da 1;
- `impianto_id` è l'impianto indicato nella segnalazione (colonna `impianto_id_indicato` del sorgente): quello scelto dal socio, o quello del sistema di monitoraggio per le comunicazioni `interno`; vuoto se nessuno l'ha indicato;
- `categoria_llm`, `urgenza_llm`, `impianto_id_llm`, `categoria` e `urgenza` sono **vuote**: le riempie il batch di classificazione al caricamento. Le risposte giuste sono in `segnalazione_etichette.csv` 🏷;
- `stato` è quello al 31/10/2026: le segnalazioni più vecchie di 30 giorni sono tutte `chiusa`;
- le 15 segnalazioni del campione ci sono con lo stesso testo, socio, impianto e ora; cambia solo lo `stato`, che nel completo è `chiusa`.

### verbale.csv (1 riga) – testo non strutturato

| Colonna | Tipo | Descrizione |
|---|---|---|
| id | intero | Identificativo |
| data_assemblea | data | Data dell'assemblea |
| testo | testo | Verbale completo, con gli a capo racchiusi tra virgolette come previsto dal formato CSV. I numeri citati vengono dai dati del campione |
| sintesi | testo | Vuota: la scrive l'LLM |

Nel campione c'è il verbale dell'assemblea del 9 luglio 2026 (id 7), che commenta i dati di giugno degli impianti 1–3, il guasto del 1° giugno e le segnalazioni del mese.

**Nel dataset completo** ci sono 8 verbali, uno a trimestre: id da 1 (gennaio 2025) a 8 (ottobre 2026), in ordine di data. Ognuno commenta il trimestre appena concluso, con i numeri di `riepilogo_trimestri.csv`. I testi vengono dai file `data/testi/verbali/verbale_<data>.md` e la data dell'assemblea dal nome del file. Il verbale del 9 luglio 2026 resta l'id 7, ma è diverso da quello del campione: commenta aprile–giugno su tutti gli 8 impianti.

---

## Tabelle calcolate (provvisorie nel campione e nello zip v1)

Nel progetto queste tabelle le scrivono i batch del team dati, non il generatore. Il campione e lo zip v1 del dataset completo le contengono comunque, perché `db/seed/carica.sql` carica 13 CSV e si ferma se ne manca uno. Le versioni provvisorie sono utili ai WSA per costruire le pagine e sono anche la baseline dei modelli.

| File | Righe (campione) | Colonne | Nel campione | Nel dataset completo (zip v1) |
|---|---|---|---|---|
| `previsione_produzione.csv` | 2.160 | `impianto_id`, `ts`, `kwh_previsti` | La stessa formula della produzione, senza anomalie | Provvisoria, come nel campione: 140.160 righe |
| `previsione_consumo.csv` | 14.400 | `socio_id`, `ts`, `kwh_previsti` | Il profilo del socio, senza rumore | Provvisoria, come nel campione: 4.204.800 righe (circa 130 MB) |
| `anomalia.csv` | 1 | `id`, `impianto_id`, `inizio`, `fine`, `tipo`, `score`, `stato` | Il guasto dell'impianto 3 del 1 giugno, come se il batch l'avesse trovato | Provvisoria: la stessa riga del campione. Il batch vero aggiunge le altre e salta quelle già presenti |
| `ripartizione_mensile.csv` | 20 | `socio_id`, `mese`, `kwh_condivisi`, `incentivo_eur`, `co2_evitata_kg` | Formula della guida §3.6 applicata a giugno | Calcolo vero del §3.6: 4.579 righe, una per socio e mese dal mese di adesione |

**Valori delle colonne di `anomalia`:**

- `fine`: vuota se l'anomalia è ancora in corso;
- `tipo`: `guasto`, `sporcizia`, `stringa`, `neve`, oppure vuoto se il modello non riconosce la causa;
- `score`: da 0 a 1;
- `stato`: `aperta` o `chiusa` (la chiude l'operatore).

⚠ **Ripartizione del campione.** È calcolata su 3 impianti e 20 soci, quindi l'energia condivisa è quasi uguale ai consumi delle ore di sole. Nel dataset completo i valori di giugno sono diversi, perché dipendono da tutti gli 8 impianti e i 240 soci. Un socio conta dalle 00:00 UTC del giorno di adesione: nel mese di adesione la sua quota è solo dei giorni da socio.

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

Le risposte giuste per ogni segnalazione: servono a misurare l'accuratezza dell'LLM. Una riga per segnalazione (282), con gli stessi `id` di `segnalazione.csv`.

| Colonna | Tipo | Descrizione |
|---|---|---|
| segnalazione_id | intero | Segnalazione (`segnalazione.id`) |
| categoria_vera | testo | Categoria giusta (stessi valori di `categoria`) |
| urgenza_vera | testo | Urgenza giusta: `alta`, `media`, `bassa` |
| impianto_id_vero | intero | Impianto di cui parla il testo; vuoto se non parla di un impianto |
| set | testo | `sviluppo` (circa 30%, per scrivere il prompt) o `test` (circa 70%, per la misura finale) |

La divisione è stratificata per categoria: in ogni categoria il 30% delle righe, arrotondato all'intero più vicino, è di sviluppo. La fa il generatore con `numpy.random.default_rng([42, 3])`, quindi è sempre la stessa. Le righe di test non si guardano mentre si scrive il prompt.

### segnalazione_etichette_sviluppo.csv 🏷 (solo nel dataset completo)

Le sole righe di sviluppo di `segnalazione_etichette.csv` (86), con le stesse colonne: è il file da usare mentre si scrive il prompt, così le etichette di test restano nascoste.

| Colonna | Tipo | Descrizione |
|---|---|---|
| segnalazione_id, categoria_vera, urgenza_vera, impianto_id_vero, set | | Come in `segnalazione_etichette.csv`; `set` vale sempre `sviluppo` |

### riepilogo_trimestri.csv (solo nel dataset completo)

Un trimestre per riga (8 righe), da nov-dic 2024 a lug-set 2026: serve per scrivere i verbali e per il report. I mesi sono in UTC, come in tutte le tabelle.

| Colonna | Tipo | Descrizione |
|---|---|---|
| verbale_id | intero | Verbale dell'assemblea che commenta il trimestre: da 1 (gennaio 2025) a 8 (ottobre 2026) |
| trimestre | testo | `nov-dic 2024`, `gen-mar 2025`, …, `lug-set 2026` (il primo ha solo 2 mesi) |
| produzione_impianto_1_kwh, produzione_impianto_2_kwh, produzione_impianto_3_kwh, produzione_impianto_4_kwh, produzione_impianto_5_kwh, produzione_impianto_6_kwh, produzione_impianto_7_kwh, produzione_impianto_8_kwh | decimale | Produzione di ogni impianto nel trimestre |
| produzione_kwh | decimale | Produzione totale della comunità |
| consumi_kwh | decimale | Consumi dei soci attivi, ognuno contato dalla sua adesione |
| kwh_condivisi | decimale | Energia condivisa (somma di `ripartizione_mensile`) |
| incentivo_eur | decimale | Incentivo totale (somma di `ripartizione_mensile`) |
| incentivo_famiglie_eur, incentivo_imprese_eur, incentivo_enti_eur | decimale | Incentivo per tipo di socio |
| co2_evitata_kg | decimale | CO2 evitata da tutta la produzione: è il KPI di comunità (guida §3.6) |
| co2_evitata_condivisa_kg | decimale | CO2 evitata dalla sola energia condivisa (somma di `ripartizione_mensile`) |
| soci_attivi | intero | Soci aderenti entro la fine del trimestre (non ci sono recessi) |
| nuovi_soci | intero | Soci aderenti durante il trimestre |
| anomalie_guasto, anomalie_stringa, anomalie_sporcizia, anomalie_neve | intero | Anomalie di `anomalie_vere.csv` che toccano il trimestre, per tipo, anche se iniziate prima o finite dopo |
| anomalie_dettaglio | testo | Una frase per anomalia, separate da `; `: id, tipo, impianto, inizio e fine (esclusa), perdita e kWh persi stimati nel trimestre (produzione attesa meno reale) |
| giorno_max_produzione, kwh_giorno_max | data, decimale | Giorno (UTC) di massima produzione della comunità e i suoi kWh |
| giorno_min_produzione, kwh_giorno_min | data, decimale | Giorno (UTC) di minima produzione della comunità e i suoi kWh |

Il dataset completo ha anche `cache/arera/arera_torino_2025.csv`, con le righe ARERA usate per i consumi (guida §3.4.1). Non fa parte dello zip.

---

## Differenze rispetto a `docs/architettura.md` (accolte nello schema il 23 novembre, commit 5f1ec52)

1. **`impianto`:** si aggiungono `inclinazione_gradi` e `azimut_gradi`, necessarie per i calcoli con Open-Meteo e PVGIS.
2. **`meteo_orario`:** le unità entrano nei nomi delle colonne (`irraggiamento_wm2`, `temperatura_c`, `nuvolosita_pct`) e si aggiungono `irraggiamento_pannelli_wm2` e `neve_cm`. Nessuna API espone questa tabella.
3. **`segnalazione`:** si aggiunge `impianto_id_llm`. `socio_id` può essere vuoto, e il canale `interno` serve per le comunicazioni guasti.

## Usi suggeriti

| Requisito del progetto | File |
|---|---|
| Previsione della produzione | `produzione_oraria` + `meteo_orario` + `impianto` → `previsione_produzione` |
| Previsione dei consumi | `consumo_orario` + `socio` (+ `meteo_orario`) → `previsione_consumo` |
| Rilevamento anomalie | `produzione_oraria` confrontata con l'atteso (`meteo_orario` + `impianto`) → `anomalia`; valutazione con `anomalie_vere` 🏷 |
| Ripartizione CER, incentivi, CO2 | `produzione_oraria` + `consumo_orario` + `socio.data_adesione` + `parametro` → `ripartizione_mensile` |
| Portale soci | `socio`, `consumo_orario`, `bolletta`, `ripartizione_mensile` |
| Classificazione ed estrazione di informazioni | `segnalazione.testo` → `categoria_llm`, `urgenza_llm`, `impianto_id_llm`; prompt scritto con `segnalazione_etichette_sviluppo` 🏷, valutazione sulle righe `test` di `segnalazione_etichette` 🏷 |
| Sintesi | `verbale.testo` → `sintesi` |
| Simulatore di risparmio | `consumo_orario` + `produzione_oraria` + `parametro` (guida §3.6) |

## Fonti

- Open-Meteo, Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api
- PVGIS 5.3 (JRC, Commissione europea): https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/pvgis-releases/pvgis-53_en
- ARERA, consumi dei clienti domestici: https://www.arera.it/dati-e-statistiche/dettaglio/analisi-dei-consumi-dei-clienti-domestici
- ISPRA, Rapporto 430/2026: https://www.isprambiente.gov.it/files2026/pubblicazioni/rapporti/r430-2026-2.pdf
- MASE, DM 414/2023 sulle CACER: https://greencam.unioncamere.it/wp-content/uploads/2025/06/Strumenti-di-sostegno-per-le-CACER-DM-414-del-2023_Ministero-dell_Ambiente-e-della-Sicurezza-Energetica.pdf
