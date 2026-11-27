# Guida al dataset UnderTheSun (team dati)

Versione 1.10 del 27 novembre 2026, a cura di Francesco (riferimento del team dati).

**Novità della v1.10:** le scelte fatte sui file ARERA 2025 durante la parte 2 (§3.4); i testi scritti dal team dati, con un file sorgente fisso in `data/testi/` (§3.7); le tabelle provvisorie che lo zip v1 deve contenere per il seed (§4); le nuove soglie dei controlli (§6); cosa cambia a giugno 2026 tra campione e completo (§7).

La guida parte da `docs/team-dati.md` e `docs/architettura.md` di Luca e fissa le scelte che lì erano aperte. Le voci segnate **[DA CONFERMARE]** vanno discusse alla prossima riunione; tutto il resto è deciso. Se cambia una decisione, si aggiorna prima questa guida e poi il codice.

---

## 0. In breve

- **La comunità:** una CER nel **Pinerolese** (Città metropolitana di Torino), con 8 impianti fotovoltaici tutti ≤ 200 kWp, per 950 kWp in totale, e **240 soci**: 200 famiglie, 30 imprese e 10 enti.
- **Il periodo:** dati **orari** dal **1 nov 2024 00:00 UTC al 31 ott 2026 23:00 UTC**, cioè 730 giorni e 17.520 ore per ogni serie.
- **Le fonti:**
  - **meteo reale** da Open-Meteo;
  - **produzione calcolata** dal meteo reale e **tarata su PVGIS**;
  - **consumi sintetici** calibrati sui dati **ARERA** della provincia di Torino;
  - **fattore CO2** da ISPRA e **tariffa** dal DM CER.
- **Il generatore:** un solo programma Python con due configurazioni e seed fisso `42`.
  - **PICCOLA:** il campione per il SAL 1, con giugno 2026, 3 impianti e 20 soci.
  - **COMPLETA:** il dataset per il SAL 2, condiviso come zip sul Drive del gruppo (§5).
- **Allineamento con `docs/api.md`:** le dimensioni coincidono con i suoi esempi: 240 soci, 8 impianti, 950 kWp e l'impianto 3 "Tetto scuola Pinerolo" da 180 kWp, con un guasto il 1 giugno 2026 dalle 11 alle 15 UTC.

---

## 1. Dove e quando

### 1.1 Perché il Pinerolese

- **Coerenza con `api.md`,** che usa già un impianto a Pinerolo.
- **Una sola cabina primaria.** I comuni sono vicini tra loro, quindi è plausibile che siano sotto la stessa cabina, che è la condizione per condividere energia in una CER. Assumiamo una cabina unica.
- **Neve coerente con il meteo.** I comuni sono un mix di pianura (Pinerolo, Buriasco, Cavour) e di fondovalle (Val Pellice e Val Chisone). In valle nevica di più, quindi l'anomalia "neve" coincide con nevicate vere. Da verificare nella versione completa: gli impianti di valle (5, 6, 8) devono cadere in una cella della griglia meteo diversa da quella degli impianti di pianura.
- **Dati disponibili per tutte le fonti:**
  - Open-Meteo e PVGIS coprono ogni punto d'Europa;
  - ARERA pubblica i dati della provincia di Torino, la più grande del Piemonte, quindi con medie più stabili;
  - la zona di mercato è "Nord", la stessa usata per la tariffa GSE.

### 1.2 Impianti (tabella `impianto`)

| id | nome | comune | lat | lon | kwp | inclinazione_gradi | azimut_gradi | data_attivazione |
|---|---|---|---|---|---|---|---|---|
| 1 | Tetto municipio San Secondo | San Secondo di Pinerolo | 44.87 | 7.30 | 60 | 25 | 15 | 2024-03-15 |
| 2 | Capannone artigiano Buriasco | Buriasco | 44.87 | 7.41 | 150 | 10 | -20 | 2024-05-02 |
| 3 | Tetto scuola Pinerolo | Pinerolo | 44.88 | 7.35 | 180 | 15 | 0 | 2024-04-01 |
| 4 | Palestra comunale Bricherasio | Bricherasio | 44.82 | 7.31 | 80 | 20 | -10 | 2024-06-10 |
| 5 | Pensilina parcheggio Luserna | Luserna San Giovanni | 44.81 | 7.25 | 120 | 5 | 10 | 2024-07-01 |
| 6 | Tetto biblioteca Torre Pellice | Torre Pellice | 44.82 | 7.22 | 50 | 30 | 0 | 2024-09-16 |
| 7 | Capannone agricolo Cavour | Cavour | 44.79 | 7.37 | 200 | 15 | 5 | 2024-08-05 |
| 8 | Tetto RSA Villar Perosa | Villar Perosa | 44.92 | 7.25 | 110 | 25 | -30 | 2024-10-01 |

- **Coordinate.** Sono approssimate al centro del comune, con 2 decimali (circa 1 km). Bastano: la griglia di Open-Meteo è di circa 10 km, quindi impianti a pochi km di distanza possono cadere nella stessa cella e avere lo stesso meteo; cambia solo la temperatura, corretta per la quota. Succede ai tre impianti del campione. L'impianto 3 usa le coordinate di `api.md`. Il primo script le controlla con la geocoding API di Open-Meteo.
- **Potenza.** 950 kWp in totale, tutti ≤ 200 kWp, quindi tutti nella stessa fascia di tariffa (§3.5).
- **Azimut.** 0 = sud, −90 = est, +90 = ovest: è la convenzione di PVGIS e Open-Meteo. Attenzione: la libreria `pvlib` usa invece 180 = sud.
- **Attivazione.** Tutti gli impianti sono attivi prima dell'inizio del periodo, quindi le serie di produzione sono complete.

### 1.3 Soci (tabella `socio`)

- **Composizione:** 240 soci, cioè 200 famiglie, 30 imprese e 10 enti.
- **Nomi:** finti, generati con la libreria Faker (lingua `it_IT`, seed 42). Imprese ed enti hanno nomi plausibili, come "Panificio Rostagno" o "Scuola primaria Lauro".
- **Comune:** uno degli 8 comuni degli impianti, in proporzione approssimativa agli abitanti (pesi indicativi, non verificati). Pinerolo è il più numeroso.
- **ID:** in ordine di data di adesione.
- **Enti:**
  - sono tutti soci fondatori;
  - quelli che ospitano un impianto stanno nel comune dell'impianto: scuola a Pinerolo, uffici comunali a San Secondo, impianto sportivo a Bricherasio, biblioteca a Torre Pellice, RSA a Villar Perosa;
  - gli altri enti stanno in comuni vicini.
- **`data_adesione`:**
  - 120 soci fondatori aderiscono tra giugno e ottobre 2024;
  - gli altri 120 sono distribuiti tra novembre 2024 e giugno 2026.
- **Periodo dei consumi:** i consumi si generano **per tutto il periodo e per tutti i soci**. Il calcolo CER conta un socio solo dalla sua `data_adesione` (§3.6). In questo modo le serie per i modelli di previsione restano complete.
- **Profilo:** ogni socio ha un profilo di consumo, salvato in `socio_profilo.csv` (file di lavoro, **non** va nel database).

| tipo | profilo | ATECO di riferimento | quanti |
|---|---|---|---|
| famiglia | famiglia | (domestico) | 200 |
| impresa | bar | 56.30 | 4 |
| impresa | ristorante | 56.10 | 4 |
| impresa | alimentari | 47.11 | 6 |
| impresa | panificio | 10.71 | 4 |
| impresa | officina | 25.62 | 6 |
| impresa | parrucchiere | 96.02 | 6 |
| ente | scuola | 85.20 | 4 |
| ente | uffici_comunali | 84.11 | 3 |
| ente | biblioteca | 91.01 | 1 |
| ente | rsa | 87.10 | 1 |
| ente | impianto_sportivo | 93.11 | 1 |

Dal 2025 è in vigore la nuova classificazione ATECO: verificate nel file ARERA quali codici compaiono.

### 1.4 Periodo

- **Dataset completo:** da `2024-11-01T00:00:00Z` a `2026-10-31T23:00:00Z`, dove l'ultimo valore è l'inizio dell'ultima ora. Sono 730 giorni × 24 = **17.520 ore**.
- **Perché questo periodo:** sono due anni interi che finiscono con l'ultimo mese completo prima del progetto, e ottobre 2026 è il mese più recente da mostrare alla demo.
- **Campione SAL 1:** da `2026-06-01T00:00:00Z` a `2026-06-30T23:00:00Z`, cioè **720 ore**.

---

## 2. Regole comuni per i file

- **Formato:** CSV in UTF-8 senza BOM, separatore `,`, decimali con `.`. La prima riga contiene le intestazioni in `snake_case`. C'è un file per tabella, con il nome della tabella (`consumo_orario.csv`).
- **Istanti:** sempre in UTC e in formato ISO, per esempio `2026-06-01T10:00:00Z`. **`ts` è l'inizio dell'ora:** `kwh` alle 10:00 è l'energia tra le 10:00 e le 11:00.
- **Date senza ora:** formato `2026-06-01`. La colonna `mese` contiene il primo giorno del mese (`2026-06-01`). I mesi si calcolano in UTC, come farebbe `date_trunc('month', ts)` in PostgreSQL.
- **Unità nel nome della colonna:** `_kwh`, `_kwp`, `_eur`, `_kg`, `_wm2`, `_c`, `_pct`, `_cm`, `_gradi`. Fanno eccezione le colonne che si chiamano solo `kwh` o `kwp` nelle tabelle di Luca: lì il nome è già l'unità, e le API le usano così.
- **Valori mancanti:** cella vuota, che diventa NULL. Mai `NaN`, `None` o `-`.
- **Decimali:** al massimo 3 per l'energia e per i kg di CO2, 2 per gli euro e 1 per il meteo.
- **ID:** interi a partire da 1, coerenti tra i file.
- **Seed:** `42`. Ogni impianto e ogni socio ha un proprio generatore casuale: `numpy.random.default_rng([42, 0, id])` per gli impianti e `numpy.random.default_rng([42, 1, id])` per i soci. Le scelte che riguardano tutta la comunità (tipo, comune e data di adesione dei soci) usano `numpy.random.default_rng([42, 2])`. Così i numeri di un socio non cambiano se si generano più o meno soci, e socio e impianto con lo stesso id non condividono la stessa sequenza casuale. Con lo stesso seed escono gli stessi file.
- **Fine riga:** `\n` (LF). Il file `data/.gitattributes` con la riga `*.csv text eol=lf` evita che Git su Windows li trasformi in CRLF.
- **Intervalli `inizio`–`fine`:** `inizio` è incluso, `fine` è escluso. Un guasto dalle 11:00 alle 15:00 azzera le ore 11, 12, 13 e 14.
- **Cartelle:**
  - `data/esempi/` contiene il campione del SAL 1 e **va su GitHub**;
  - `data/output/` contiene il dataset completo e la cache delle API ed è **escluso da Git**.

---

## 3. Fonti e regole di generazione

### 3.1 Meteo: Open-Meteo (dato reale)

**Chiamata:**

- **Servizio:** Historical Weather API, `https://archive-api.open-meteo.com/v1/archive`. È gratuita per uso non commerciale e non richiede chiave.
- **Una chiamata per impianto** con questi parametri:
  - `latitude`, `longitude`;
  - `start_date=2024-10-31`, `end_date=2026-11-01`, cioè un giorno in più ai bordi per lo spostamento orario descritto sotto;
  - `timezone=GMT`;
  - `tilt` e `azimuth` dell'impianto, necessari per l'irraggiamento sul piano dei moduli;
  - `hourly=shortwave_radiation,global_tilted_irradiance,temperature_2m,cloud_cover,snowfall`.

| Variabile Open-Meteo | Colonna in `meteo_orario` | Nota |
|---|---|---|
| `shortwave_radiation` | `irraggiamento_wm2` | sul piano orizzontale (GHI) |
| `global_tilted_irradiance` | `irraggiamento_pannelli_wm2` | sul piano dei moduli dell'impianto |
| `temperature_2m` | `temperatura_c` | |
| `cloud_cover` | `nuvolosita_pct` | |
| `snowfall` | `neve_cm` | neve caduta nell'ora |

- **Attenzione all'ora.** In Open-Meteo radiazione e neve indicate alle 11:00 sono la media (o la somma) dell'ora **precedente**, cioè dalle 10 alle 11. Nella nostra convenzione vanno su `ts = 10:00`, quindi si spostano indietro di un'ora. Temperatura e nuvolosità sono valori istantanei: si prende il valore all'inizio dell'ora, senza spostamenti.
- **Cache.** Le risposte grezze si salvano in `data/output/cache/openmeteo/` e si rileggono da lì: la stessa cosa non si scarica due volte.
- **Citazione** nel data dictionary e nel report: "Weather data by Open-Meteo.com (CC BY 4.0), basati su ERA5 / Copernicus Climate Change Service".

### 3.2 Produzione: modello sul meteo reale, tarato con PVGIS

**Perché non usiamo direttamente le serie orarie di PVGIS:**

- PVGIS 5.3 ha dati orari **solo fino al 2023**.
- La produzione deve essere coerente con il meteo dello stesso giorno. Altrimenti il modello di previsione non ha niente da imparare e la neve non coincide con le nevicate.

PVGIS fa quindi da **riferimento**: serve a tarare il modello e a validarlo.

**Formula oraria per ogni impianto:**

```
T_modulo    = temperatura_c + 0.03 × irraggiamento_pannelli_wm2
fattore_T   = 1 − 0.004 × (T_modulo − 25)
kwh_teorici = kwp × irraggiamento_pannelli_wm2 / 1000 × 0.86 × fattore_T × k_impianto
kwh         = min(kwh_teorici, kwp) × effetto_anomalie
```

- **0,86:** corrisponde a perdite di sistema del 14%, il valore che PVGIS propone di default.
- **−0,4% per °C:** coefficiente tipico dei moduli in silicio cristallino. Il modulo al sole è più caldo dell'aria e rende meno.
- **`k_impianto`:** fattore di taratura, vicino a 1. Assorbe le differenze locali, per esempio le ombre delle montagne, che PVGIS considera.

**Calcolo di `k_impianto`:**

1. **Scaricare da PVGIS** la produzione oraria del **2023** dell'impianto con `https://re.jrc.ec.europa.eu/api/v5_3/seriescalc` e questi parametri:
   - `lat`, `lon`;
   - `peakpower=<kwp>`, `loss=14`, `angle=<inclinazione>`, `aspect=<azimut>`;
   - `pvcalculation=1`, `startyear=2023`, `endyear=2023`, `outputformat=json`.
2. **Calcolare il modello sul 2023:** scaricare da Open-Meteo lo stesso anno per lo stesso punto e applicare la formula con `k = 1`.
3. **Calcolare il fattore:** `k_impianto = kWh annui PVGIS 2023 / kWh annui del modello 2023`. Ci si aspetta circa 0,95: nel campione, a parità di irraggiamento, il modello rende il 5% più di PVGIS, perché non considera le perdite per riflessione sui moduli.
4. **Validare:** annotare nel report l'errore orario tra modello e PVGIS (MAE e correlazione). Questa è la validazione del modello di produzione.

**Due controlli:**

- **Orari di PVGIS.** PVGIS restituisce la potenza `P` in W, con orari del tipo `20230615:1010` (UTC). Vanno arrotondati all'ora, poi un grafico deve confermare che i picchi di PVGIS e del modello coincidono. Se sono sfasati di un'ora, si corregge lo spostamento.
- **Totale annuo.** La produzione annua per kWp di ogni impianto deve restare entro ±10% del valore PVGIS (`PVcalc`, stessi parametri).

### 3.3 Anomalie iniettate nella produzione

Ogni anomalia "vera" si scrive in `anomalie_vere.csv`, con le colonne `id`, `impianto_id`, `inizio`, `fine`, `tipo` e `perdita_pct`. Il file **non va nel database**: serve a misurare precision e recall del rilevamento anomalie.

| tipo | Effetto sulla produzione | Quante in 2 anni |
|---|---|---|
| `guasto` | Produzione a 0 nelle ore di sole, per un tempo da 2 ore a 5 giorni | 10, tra cui **impianto 3, dal `2026-06-01T11:00:00Z` al `2026-06-01T15:00:00Z`** (come in `api.md`) |
| `stringa` | Calo fisso del 20–35% da una certa data, fino alla riparazione (1–4 settimane) | 4 |
| `sporcizia` | Calo che cresce di circa l'1% a settimana fino al 10–15%, poi torna normale ("pulizia") | 5, soprattutto in estate |
| `neve` | Produzione al 5% dopo una nevicata (≥ 2 cm nelle 24 ore precedenti), finché non passano 2 giorni con temperatura massima sopra 3 °C | Quante ne produce il meteo vero, soprattutto negli impianti di valle (5, 6, 8) |

**Campione stabile:** le anomalie casuali del dataset completo non cadono in giugno 2026 sugli impianti 1–3. In quel mese c'è solo il guasto dell'impianto 3 del 1 giugno, così il campione del SAL 1 resta identico.

### 3.4 Consumi: sintetici, calibrati su ARERA

**Principio:** *quanto* consuma un socio in ogni mese viene da ARERA. *Come* quel consumo si distribuisce nelle ore viene da profili giornalieri per tipo di socio, riscalati in modo da rispettare i dati ARERA.

**Fonti ARERA** (sezione "Monitoraggio retail", file ZIP):

- **Famiglie:** "Analisi dei consumi dei clienti domestici". Contiene il prelievo medio mensile in kWh per provincia, classe di potenza e residenza, la ripartizione per fasce F1/F2/F3 e il prelievo medio orario dei clienti trattati orari. Si usa **provincia di Torino, residenti, classe 1,5–3 kW, tutti i mercati, anno 2025** (scelte al §3.4.1).
- **Imprese ed enti:** "Analisi dei consumi dei clienti non domestici in BT" per ATECO. Contiene il prelievo medio mensile per attività (fino alla classe ATECO a 4 cifre), provincia e classe di potenza. Si usa **provincia di Torino, anno 2025**.
- **Scaricamento:** gli ZIP pesano 20–50 MB. Si scaricano a mano una volta in `data/output/cache/arera/`, poi uno script estrae solo le righe che servono e le salva in un piccolo CSV.

**Passi:**

1. **Volume mensile del profilo.** È la media ARERA del mese per quel profilo (2025, provincia di Torino). Lo stesso valore si usa per i mesi corrispondenti del 2024 e del 2026, perché ARERA non ha ancora pubblicato il 2026. **Conseguenza per i modelli:** i due anni hanno gli stessi volumi mensili, quindi a livello di mese la previsione dei consumi è banale; la varietà tra un anno e l'altro viene solo dal rumore e dal calendario.
2. **Varietà tra soci.** Ogni socio ha un moltiplicatore fisso `scala`, estratto da una distribuzione lognormale con media 1. La deviazione standard è circa 0,35 per le famiglie e 0,5 per imprese ed enti. Così ci sono famiglie piccole e grandi.
3. **Forma oraria.** Un profilo di 24 valori per tipo di socio e tipo di giorno: feriale, sabato, domenica o festivo. I festivi italiani si ricavano con la libreria `holidays`.
   - **Famiglia:** picco la mattina (7–8) e la sera (19–22), consumi bassi di notte, un po' più alti a metà giornata nel weekend.
   - **Imprese ed enti:** consumi alti negli orari di apertura del profilo, bassi fuori orario (resta il consumo di base). Per esempio la scuola è aperta lunedì–venerdì 8–16 nei giorni di lezione del calendario scolastico della Regione Piemonte (nel 2025/26 dal 10 settembre al 10 giugno, con il ponte del 1° giugno; il 2026/27 inizia lunedì 14 settembre) ed è chiusa nelle vacanze, a luglio e ad agosto; nel 2024/25 (DGR 4-8323 del 20 marzo 2024) le lezioni vanno dall'11 settembre 2024 al 7 giugno 2025, con vacanze di Natale dal 23 dicembre al 6 gennaio, Carnevale dal 1° al 4 marzo, Pasqua dal 17 al 22 aprile e scuola chiusa anche il 1° novembre, il 25 aprile, dal 1° al 3 maggio e il 2 giugno; il ristorante lavora 11–15 e 19–23, il bar soprattutto dalla mattina al pomeriggio; l'officina lunedì–venerdì 8–18.
   - **File ARERA delle famiglie (verificato il 27/11):** il "prelievo medio orario" ha un valore per ogni ora, per mese e tipo di giorno, quindi per le famiglie si usa direttamente la forma ARERA (§3.4.1). Il profilo descritto sopra resta solo nel campione.
   - **Le fasce:**
     - F1 = lunedì–venerdì 8–19;
     - F2 = lunedì–venerdì 7–8 e 19–23, sabato 7–23;
     - F3 = lunedì–sabato 23–7, domenica e festivi tutto il giorno.
4. **Ora italiana e UTC.** I profili sono pensati in ora italiana, perché le persone si svegliano alle 7 locali, ma la serie si costruisce sulle ore UTC. Per ogni ora UTC si ricava l'ora italiana con `tz_convert('Europe/Rome')` e si legge il valore del profilo. Così i giorni del cambio d'ora, che hanno 23 o 25 ore, non creano ore mancanti o doppie: nel periodo sono il 30/3/2025, il 26/10/2025, il 29/3/2026 e il 25/10/2026.
5. **Rumore.** Ogni ora si moltiplica per un fattore casuale normale con media 1 e deviazione standard 0,15, troncato a zero. In più ogni socio ha le abitudini spostate di 0 o ±1 ora.
6. **Riscalatura finale.** Il totale di ogni **mese UTC** di ogni socio deve risultare uguale a volume ARERA × `scala`. Si usa il mese UTC perché anche le bollette lo usano (§2): così `bolletta.kwh` torna esattamente. Il periodo deve essere fatto di mesi interi, altrimenti il programma si ferma.
7. **Facoltativo, per una v2 del dataset:** legare i consumi estivi alla temperatura, per cui nei giorni più caldi si usa di più il condizionatore. Così il modello di previsione dei consumi ha una variabile meteo da sfruttare. Non è nella v1.

#### 3.4.1 Scelte sui file ARERA 2025 (parte 2, 27 novembre)

Le scelte sono nel codice (`consumi.py`), non nel CSV estratto: per cambiarle basta cambiare il codice e rigenerare.

**Famiglie**

- **Riga usata:** provincia di Torino, Tipo Mercato "Tutti", Residenza "Residente", Classe potenza "1.5<potenza_impegnata<=3". ARERA non dice quanti clienti ci sono per classe: si sceglie il contratto da 3 kW, il più diffuso. "Tutti" comprende tutti i mercati (`CLASSE_FAMIGLIE`).
- **Volume dal file mensile, forma dal file orario.** Il volume del mese è il "medio consumo mensile" del file mensile, cioè la media ufficiale: **1.552,4 kWh all'anno** (da gennaio a dicembre: 147,0 – 127,4 – 131,8 – 118,1 – 117,7 – 136,8 – 128,3 – 124,5 – 112,0 – 127,4 – 135,5 – 145,9). La somma ore × giorni del file orario dà circa l'1% in più, quindi quel file serve solo per la forma della giornata.
- **Forma oraria ARERA usata così com'è:** 864 valori (12 mesi × 3 tipi di giorno × 24 ore) dal file "TOT", non da quelli per mercato. Il mese della forma è quello del giorno in ora italiana; lo spostamento di ±1 ora delle abitudini vale anche qui.
- **"Ora1" è l'ora 00–01 in ora italiana.** Con questa lettura le quote F1/F2/F3 ricavate dalla forma (31,9 / 30,7 / 37,4%) tornano con quelle del file mensile (31,3 / 30,7 / 38,0%); con "Ora1" = 01–02 tornano peggio.
- **Festivi trattati come domenica.** ARERA ha solo feriale, sabato e domenica, e la fascia F3 mette insieme domeniche e festivi. Con questa ipotesi ore × giorni torna con il mensile (+1%) e le fasce tornano entro 1 punto.
- **Lettura del file:** si saltano le righe con "Anno Mese" = 2025 (totali dell'anno); il mese è una data di Excel (45658 = 1/1/2025).

**Imprese ed enti**

- **Codici ATECO 2007 del §1.3, senza tabella di corrispondenza.** Nel file 2025 i codici vecchi ci sono in tutti i 12 mesi, quelli nuovi (56.11, 96.21, 91.11, 25.53) solo da maggio–giugno. 25.62 vale come "meccanica generale".
- **Classe di potenza per profilo:** negozi 6–10 kW; attività con forni, cucina o macchinari oltre 10 kW; enti oltre 16,5 kW.

| profilo | ATECO | classe | kWh/anno |
|---|---|---|---|
| bar | 56.30 | 6–10 | 15.422 |
| alimentari | 47.11 | 6–10 | 11.829 |
| parrucchiere | 96.02 | 6–10 | 5.348 |
| ristorante | 56.10 | >10 | 20.199 |
| panificio | 10.71 | >10 | 19.272 |
| officina | 25.62 | >10 | 10.152 |
| scuola | 85.20 | >16,5 | 36.776 |
| uffici_comunali | 84.11 | >16,5 | 33.305 |
| rsa | 87.10 | >16,5 | 146.346 |
| impianto_sportivo | 93.11 | >16,5 | 72.998 |
| biblioteca | 91.01 | 6–10 | 18.134 |

- **Biblioteca.** La 6–10 kW è l'unica classe di 91.01 con tutti i 12 mesi, ma da luglio raddoppia (da 976 a 2.092 kWh) perché i clienti sono pochi. Si prende quindi il totale annuo (18.133,6 kWh) e lo si distribuisce sui mesi con la forma degli uffici comunali (84.11) della stessa classe: 1.741, 1.552, 1.609, 1.446, 1.377, 1.310, 1.334, 1.312, 1.384, 1.572, 1.676, 1.823 kWh (`FORMA_MESI_BIBLIOTECA`).
- **Forma oraria:** restano i profili orari approvati il 19/11, perché ARERA dà solo valori mensili.
- **Prezzi:** le bollette di imprese ed enti usano ancora 0,351 €/kWh come le famiglie (§3.5). Va scritto nel `LEGGIMI.txt`.

**File estratto: `data/output/cache/arera/arera_torino_2025.csv`**

- Colonne `cliente`, `ateco`, `classe_potenza`, `mese`, `tipo_giorno`, `ora`, `grandezza`, `valore`, `file`; 1.056 righe, valori come nella fonte, senza arrotondamenti.
- Contiene anche righe che non si usano come volume (per esempio 84.11 a 6–10 kW, che serve per la forma della biblioteca).
- Per rifare l'estrazione basta cancellare il file. Una verifica blocca tutto se mancano mesi o ci sono valori nulli.
- Gli xlsx si leggono con la libreria standard: `requirements.txt` non cambia.

**Calendario scolastico 2024/25:** date del punto 3, con l'anno dal 1/9/2024 al 31/8/2025; tra le sospensioni ci sono anche il 1/11, il 25/4, il 1–3/5 e il 2/6, anche se sono già festivi.

**Risultati (completo, 27/11):** famiglie in media 1.542 kWh all'anno in entrambi gli anni (−0,7% da ARERA); fasce 32,1 / 30,1 / 37,8% contro 31,3 / 30,5 / 38,2%; scuola con rapporto lezione/notte 1,01 a luglio–agosto e 6,72 a ottobre; bolletta annua media famiglia 541 €, impresa 4.242 €, ente 14.236 €. La comunità consuma circa 1.180 MWh all'anno (con tutte le scale a 1) e ne produce 1.181–1.230.

### 3.5 Parametri (tabella `parametro`)

| chiave | valore | fonte |
|---|---|---|
| `fattore_co2_kg_kwh` | 0.4133 | ISPRA, Rapporto 430/2026, Tab. 1.7: produzione termoelettrica lorda solo da fonti fossili, 2025 (dato preliminare). È il metodo ISPRA per le emissioni evitate dalle rinnovabili |
| `tariffa_premio_eur_kwh` | 0.130 | DM MASE 414/2023, Allegato 1. Per impianti ≤ 200 kW vale min(80 + max(0; 180 − Pz); 120) €/MWh, più 10 €/MWh per il fotovoltaico al Nord. Con prezzo zonale Pz ≤ 140 €/MWh vale sempre 130 €/MWh |
| `valorizzazione_arera_eur_kwh` | 0.008 | ARERA, corrispettivo di valorizzazione dell'energia condivisa (TIAD, delibera 727/2022): circa 8 €/MWh nel 2023. **Da aggiornare** con il valore 2025–2026 |
| `prezzo_energia_famiglia_eur_kwh` | 0.351 | ARERA, Relazione annuale presentata a luglio 2026 (dati 2025): prezzo finale medio per i clienti domestici, 35,12 c€/kWh |
| `prezzo_energia_impresa_eur_kwh` | 0.351 | **Da aggiornare** con il prezzo medio dei clienti BT altri usi della stessa Relazione annuale. Finché manca, si usa il valore delle famiglie |
| `prezzo_energia_ente_eur_kwh` | 0.351 | Come la riga precedente |
| `perdite_sistema_pct` | 14 | PVGIS, valore predefinito delle perdite di sistema |
| `coeff_temperatura_pct_c` | -0.4 | Valore tipico per moduli in silicio cristallino |

- **Tariffa costante.** È la risposta alla domanda aperta 2 di `team-dati.md`: il tetto di 120 €/MWh scatta ogni volta che il prezzo zonale è sotto 140 €/MWh, e nelle ore di sole è il caso normale. Per un calcolo ora per ora servono i prezzi zonali orari del GME (zona Nord): è un miglioramento facoltativo.
- **Nessun contributo PNRR.** Ipotizziamo che gli impianti non abbiano ricevuto contributi PNRR in conto capitale, che possono ridurre la tariffa.
- **Alternativa per la CO2.** Un fattore più prudente è quello dei "consumi elettrici", 0,1996 kg/kWh nel 2025. Usiamo il metodo ISPRA e lo citiamo nel report.

### 3.6 Calcolo CER (batch di ripartizione e simulatore)

**Per ogni ora h (in UTC):**

```
kwh_immessi(h)   = somma della produzione di tutti gli impianti
kwh_prelevati(h) = somma dei consumi dei soci con data_adesione ≤ h   (un socio conta dalle 00:00 UTC del giorno di adesione)
kwh_condivisi(h) = min(kwh_immessi(h), kwh_prelevati(h))
quota_s(h)       = kwh_condivisi(h) × consumo_s(h) / kwh_prelevati(h)
```

**Per ogni socio e mese (tabella `ripartizione_mensile`):**

```
kwh_condivisi  = somma delle quote_s del mese
incentivo_eur  = kwh_condivisi × (tariffa_premio_eur_kwh + valorizzazione_arera_eur_kwh)
co2_evitata_kg = kwh_condivisi × fattore_co2_kg_kwh
```

- **Semplificazioni da dichiarare nel report:**
  - tutta la produzione viene immessa in rete, cioè gli impianti non hanno autoconsumo;
  - tutto l'incentivo va ai soci in proporzione ai prelievi (domanda aperta 5);
  - c'è una sola cabina primaria (domanda aperta 1).
- **KPI di comunità:** CO2 evitata = **produzione totale** × fattore, perché tutta l'energia rinnovabile prodotta evita emissioni, non solo quella condivisa.
- **Simulatore** (domanda aperta 6): due input come in `api.md`, cioè `consumo_annuo_kwh` e `quota_spostata_ore_diurne_pct`. La quota indicata si sposta dalle ore 19–8 alle ore 10–16 (ora italiana); poi il backend rifà il calcolo sopra con i consumi modificati.

### 3.7 Testi

#### Segnalazioni

- **Quante:** circa 250 dai soci (canale `email` o `portale`) e circa 30 comunicazioni guasti interne (canale `interno`, `socio_id` vuoto). È la risposta alla domanda aperta 3.
- **Categorie:** `guasto_impianto`, `bolletta_pagamenti`, `incentivi_ripartizione`, `adesione_recesso`, `informazioni`, `reclamo`. Distribuzione indicativa: 25% informazioni, 20% bolletta, 20% guasto, 15% incentivi, 10% adesione, 10% reclamo.
- **Urgenze:** `alta`, `media`, `bassa`.
- **Coerenza con i dati:**
  - per ogni `guasto` e `stringa` in `anomalie_vere.csv` ci sono 1–3 segnalazioni nei giorni successivi su quell'impianto, a volte con il nome esatto e a volte vaghe ("i pannelli della scuola");
  - ogni anomalia ha una comunicazione `interno`.
- **Varietà:** lunghezze da una a dieci righe, registri diversi, errori di battitura e qualche caso ambiguo tra due categorie (circa il 15%). Nel testo il socio scrive l'ora italiana; `ts` resta in UTC.
- **Chi li scrive (deciso il 27/11):** il team dati (Francesco, con Claude come LLM), così Giuseppe classifica testi che non ha scritto. Un campione si controlla a mano, ma **solo nel set di sviluppo** (vedi sotto): chi legge il test non può più usarlo per la misura.
- **Mittenti coerenti:** ogni segnalazione di un socio ha `ts` successivo alla sua `data_adesione`. Le segnalazioni sui guasti vengono di preferenza dall'ente che ospita l'impianto o da soci dello stesso comune.
- **Giugno 2026:** le 15 segnalazioni del campione entrano nel completo con lo stesso testo, socio, impianto e ora. Cambia solo lo `stato`: al 31/10/2026 sono più vecchie di 30 giorni, quindi tutte `chiusa`.

**File sorgente: `data/testi/segnalazioni_sorgente.csv`** (va su GitHub, circa 60 KB). Un testo scritto da un LLM non si rigenera dal codice, quindi i testi stanno in un file fisso e il generatore li legge. Colonne:

| Colonna | Contenuto |
|---|---|
| `ts` | Invio, in UTC con la `Z` |
| `socio_id` | Vuoto per il canale `interno` |
| `canale` | `email`, `portale`, `interno` |
| `impianto_id_indicato` | Impianto scelto dal socio nel modulo del portale, oppure quello del sistema di monitoraggio per `interno`; vuoto per le email |
| `testo` | Il testo |
| `categoria_vera`, `urgenza_vera`, `impianto_id_vero` | Le etichette vere (vuoto = nessun impianto) |
| `stato` | Stato al 31/10/2026 |
| `anomalia_vera_id` | Riferimento a `anomalie_vere.csv` quando il testo racconta un'anomalia (solo per i controlli) |

Il generatore ordina le righe per `ts`, assegna gli `id` da 1 e scrive:

- `segnalazione.csv`: `impianto_id` = `impianto_id_indicato`; `categoria_llm`, `urgenza_llm`, `impianto_id_llm`, `categoria` e `urgenza` **vuote** nel completo (le riempie il batch di classificazione);
- `segnalazione_etichette.csv`: le etichette vere e la colonna `set`.
- **Stato:** le segnalazioni più vecchie di 30 giorni sono tutte `chiusa`. Tra le più recenti, quelle già risolte sono `chiusa` e le altre `aperta` o `in_corso`.
- **Classificazione:** con LLM (domanda aperta 4). Per il report si può aggiungere un confronto con un classificatore classico (TF-IDF + regressione logistica).

#### Chi indica l'impianto

**Scelta ibrida, accolta da Luca nello schema e in `api.md` il 23 novembre (commit 5f1ec52):**

- Il socio **può** indicare l'impianto nel modulo, ma non è obbligato.
- L'LLM legge il testo e restituisce anche l'impianto, se lo riconosce. Per farlo, il prompt riceve l'elenco degli impianti (id, nome, comune).
- Si aggiunge la colonna **`impianto_id_llm`**, cioè la risposta dell'LLM, che non si modifica mai, come `categoria_llm`.
- **`impianto_id`** è il valore in uso: quello del socio se l'ha indicato, altrimenti quello dell'LLM. L'operatore può correggerlo.

**Perché questa scelta:**

- funziona anche con segnalazioni vaghe come "il coso dei pannelli non si accende";
- dà al team dati un compito di estrazione di informazioni, richiesto dalla commessa e misurabile;
- per i WSA cambia poco, perché il `POST` accetta già `impianto_id: null`.

**Alternative:**

- **A:** solo il socio sceglie l'impianto da un menu. È più semplice, ma non c'è estrazione.
- **B:** solo l'LLM indica l'impianto.

Se si sceglie un'alternativa, basta togliere `impianto_id_llm` e la parte del prompt sull'impianto.

#### File delle etichette

- **Il file:** `segnalazione_etichette.csv` (**non** va nel database), con le colonne `segnalazione_id`, `categoria_vera`, `urgenza_vera`, `impianto_id_vero` e `set` (`sviluppo` o `test`).
- **A cosa serve:** misurare l'accuratezza dell'LLM.
- **Divisione:** circa il 30% è il set di **sviluppo**, usato per scrivere il prompt; circa il 70% è il set di **test**, usato per la misura finale. Il test non si guarda mentre si scrive il prompt. La divisione si fa nel generatore, stratificata per categoria, con `numpy.random.default_rng([42, 3])`.
- **Come si riempiono le colonne LLM:**
  - In `segnalazione.csv` le colonne `categoria_llm`, `urgenza_llm`, `impianto_id_llm`, `categoria` e `urgenza` le riempie il batch di classificazione al momento del caricamento.
  - Nel campione del SAL 1 si riempiono a mano. Nel completo restano vuote.

#### Verbali

- **Quanti:** 8 assemblee, una a trimestre: a gennaio, aprile, luglio e ottobre del 2025 e del 2026. Ogni verbale commenta i dati del trimestre appena concluso.
- **Contenuto:** 1–2 pagine ciascuno, coerenti con i dati: nuovi soci, guasti, incentivi ricevuti.
- **Sintesi:** la colonna `sintesi` resta vuota nel dataset, perché la scrive l'LLM.
- **Quando si scrivono:** dopo `riepilogo_trimestri.csv` (§4), perché devono citare energia condivisa e incentivi del trimestre, che escono dalla ripartizione. Le id vanno da 1 (gennaio 2025) a 8 (ottobre 2026); il verbale del 9 luglio 2026 resta l'id 7.
- **Il verbale di luglio 2026 nel completo è diverso da quello del campione:** commenta aprile–giugno su tutti gli 8 impianti, con la produzione tarata su PVGIS. Il campione in `data/esempi/` resta com'è.
- **File sorgente:** `data/testi/verbali/verbale_<data>.md`, uno per assemblea; il generatore li legge e scrive `verbale.csv`.

---

## 4. Tabelle e colonne (data dictionary v1)

Le colonne marcate con **(nuova)** non erano nella bozza di Luca.

### Tabelle generate dal team dati

**`impianto`**

| Colonna | Tipo | Descrizione | Fonte o regola |
|---|---|---|---|
| id | int | Identificativo | 1–8 |
| nome | text | Nome dell'impianto | §1.2 |
| comune | text | Comune | §1.2 |
| lat, lon | float | Coordinate in gradi decimali | Centro del comune |
| kwp | float | Potenza di picco | §1.2 |
| inclinazione_gradi **(nuova)** | float | Inclinazione dei moduli (0 = orizzontali) | §1.2 |
| azimut_gradi **(nuova)** | float | Orientamento: 0 = sud, −90 = est, +90 = ovest | §1.2 |
| data_attivazione | date | Entrata in esercizio | §1.2 |

**`socio`:** `id` (int), `nome` (text), `tipo` (text: `famiglia`, `impresa`, `ente`), `comune` (text), `data_adesione` (date). Regole al §1.3.

**`consumo_orario`:** `socio_id` (int), `ts` (timestamp UTC, inizio dell'ora), `kwh` (float, energia prelevata nell'ora). Regole al §3.4.

**`produzione_oraria`:** `impianto_id` (int), `ts` (timestamp UTC), `kwh` (float, energia prodotta nell'ora). Regole ai §3.2 e §3.3.

**`meteo_orario`**

| Colonna | Tipo | Descrizione |
|---|---|---|
| impianto_id | int | Impianto |
| ts | timestamp | Inizio dell'ora (UTC) |
| irraggiamento_wm2 | float | Irraggiamento orizzontale medio nell'ora (W/m²) |
| irraggiamento_pannelli_wm2 **(nuova)** | float | Irraggiamento sul piano dei moduli (W/m²) |
| temperatura_c | float | Temperatura dell'aria a 2 m (°C) |
| nuvolosita_pct | float | Copertura nuvolosa (%) |
| neve_cm **(nuova)** | float | Neve caduta nell'ora (cm) |

**`bolletta`:** `id` (int), `socio_id` (int), `mese` (date, primo giorno del mese), `kwh` (float, somma dei consumi del mese), `importo_eur` (float, `kwh` × prezzo per tipo di socio, §3.5). Ci sono 24 mesi per ogni socio.

**`parametro`:** `chiave` (text), `valore` (float), `fonte` (text). Valori al §3.5.

**`segnalazione`**

| Colonna | Tipo | Descrizione |
|---|---|---|
| id | int | Identificativo |
| socio_id | int | Socio; vuoto se il canale è `interno` |
| impianto_id | int | Impianto in uso (socio, altrimenti LLM; l'operatore può correggerlo) |
| impianto_id_llm **(nuova)** | int | Impianto estratto dall'LLM, mai modificato |
| ts | timestamp | Momento dell'invio (UTC) |
| canale | text | `email`, `portale`, `interno` |
| testo | text | Testo della segnalazione |
| categoria_llm, urgenza_llm | text | Risposta dell'LLM, mai modificata |
| categoria, urgenza | text | Valori in uso, correggibili dall'operatore |
| stato | text | `aperta`, `in_corso`, `chiusa` |

**`verbale`:** `id` (int), `data_assemblea` (date), `testo` (text), `sintesi` (text, scritta dall'LLM).

### Tabelle calcolate dai batch

Le calcolano i batch del team dati, non il generatore. Lo zip v1 però le contiene comunque, perché `db/seed/carica.sql` carica 13 CSV e si ferma se ne manca uno:

| Tabella | Nello zip v1 |
|---|---|
| `ripartizione_mensile` | Calcolo vero del §3.6 sul completo |
| `previsione_produzione` | Provvisoria: la formula del §3.2 senza anomalie. È anche la baseline dei modelli |
| `previsione_consumo` | Provvisoria: il profilo senza rumore. È anche la baseline dei modelli |
| `anomalia` | Provvisoria: solo il guasto dell'impianto 3 del 1/6/2026, come nel campione. Il batch vero aggiunge le altre e salta quelle già presenti |

Il `LEGGIMI.txt` dice quali sono provvisorie.

- **`previsione_produzione`:** `impianto_id`, `ts`, `kwh_previsti`.
- **`previsione_consumo`:** `socio_id`, `ts`, `kwh_previsti`.
- **`anomalia`:** `id`, `impianto_id`, `inizio`, `fine`, `tipo`, `score`, `stato`.
- **`ripartizione_mensile`:** `socio_id`, `mese`, `kwh_condivisi`, `incentivo_eur`, `co2_evitata_kg`.

### File di lavoro (non vanno nel database)

- **`anomalie_vere.csv`:** le anomalie iniettate, per misurare il rilevamento (§3.3).
- **`segnalazione_etichette.csv`:** le etichette vere delle segnalazioni, per misurare l'LLM (§3.7).
- **`socio_profilo.csv`:** `socio_id`, `profilo`, `ateco` e `scala` di ogni socio (§1.3 e §3.4).
- **`riepilogo_trimestri.csv`:** un trimestre per riga, da nov-dic 2024 a lug-set 2026, con `verbale_id` da 1 a 8. Colonne: produzione per impianto e totale, consumi dei soci attivi, energia condivisa, incentivo totale e per tipo di socio, CO2 evitata (sulla produzione e sulla parte condivisa), soci attivi e nuovi, anomalie per tipo, `anomalie_dettaglio` con i kWh persi stimati, giorni di massima e minima produzione (in UTC). Serve per scrivere i verbali e per il report; l'elenco esatto delle colonne è in `config.py`.
- **`cache/arera/arera_torino_2025.csv`:** le righe ARERA usate (§3.4.1).

### Modifiche rispetto alla bozza di Luca (accolte nello schema il 23 novembre, commit 5f1ec52)

1. **`impianto`:** si aggiungono `inclinazione_gradi` e `azimut_gradi`, necessarie per PVGIS e Open-Meteo.
2. **`meteo_orario`:** le unità entrano nei nomi (`irraggiamento_wm2`, `temperatura_c`, `nuvolosita_pct`) e si aggiungono `irraggiamento_pannelli_wm2` e `neve_cm`. Nessuna API espone questa tabella, quindi per i WSA non cambia nulla.
3. **`segnalazione`:** si aggiunge `impianto_id_llm`, `socio_id` può essere vuoto e il canale `interno` serve per le comunicazioni guasti.
4. **Risposte alle 6 domande aperte di `team-dati.md` §11:**
   1. una sola cabina primaria;
   2. tariffa costante di 0,130 €/kWh;
   3. canale `interno` per le comunicazioni guasti;
   4. classificazione con LLM;
   5. incentivo ripartito in proporzione ai prelievi;
   6. simulatore con due input.

---

## 5. Dimensioni attese

| File | Righe (COMPLETA) | Righe (PICCOLA) |
|---|---|---|
| impianto.csv | 8 | 3 |
| socio.csv | 240 | 20 |
| meteo_orario.csv | 140.160 | 2.160 |
| produzione_oraria.csv | 140.160 | 2.160 |
| consumo_orario.csv | 4.204.800 | 14.400 |
| bolletta.csv | 5.760 | 20 |
| parametro.csv | 8 | 8 |
| segnalazione.csv | circa 280 | circa 15 |
| verbale.csv | 8 | 1 |
| segnalazione_etichette.csv | circa 280 | — |
| anomalie_vere.csv | 41 (19 casuali più 22 righe di neve in 4 episodi) | 1 |
| ripartizione_mensile.csv | 4.579 (una riga per socio e mese, dal mese di adesione) | 20 |
| previsione_produzione.csv | 140.160 (provvisoria) | 2.160 |
| previsione_consumo.csv | 4.204.800 (provvisoria, circa 130 MB) | 14.400 |
| anomalia.csv | 1 (provvisoria) | 1 |
| riepilogo_trimestri.csv | 8 (file di lavoro) | — |

`consumo_orario.csv` e `previsione_consumo.csv` pesano circa 130 MB ciascuno: restano in `data/output/` e non vanno mai su GitHub, che rifiuta i file oltre 100 MB.

**Come si condivide il dataset completo.** Su GitHub va solo il codice. I CSV vanno in uno zip sul Drive condiviso del gruppo.

- **Nome dello zip:** versione e data, per esempio `underthesun-dataset-completo-v1_2026-11-27.zip`. Ogni nuova versione è un nuovo zip con numero più alto; quelli vecchi non si sovrascrivono.
- **Dentro lo zip:** i CSV, senza la cartella `cache/`, e un `LEGGIMI.txt` con versione della guida, data, elenco dei file con il numero di righe e le istruzioni d'uso.
- **Chi lo usa:**
  - scompatta lo zip in `data/output/`, con i CSV direttamente lì e senza sottocartelle;
  - carica il database con `CARTELLA_CSV=output docker compose run --rm seed` (Issue #18);
  - non apre e risalva i CSV con Excel o Google Fogli, che cambiano punti decimali e date.
- **Fonte di verità:** resta il codice. Con lo stesso codice e il seed 42 lo zip si rigenera identico.

---

## 6. Controlli di qualità (`controlli.py`)

Si lanciano dopo ogni generazione. Se un controllo fallisce, il dataset non si consegna.

- Ogni serie ha tutte le ore (17.520, o 720 nel campione), senza duplicati né buchi.
- La produzione è 0 quando `irraggiamento_pannelli_wm2` è 0 e non supera mai `kwp`.
- La produzione annua per kWp di ogni impianto resta entro ±10% di PVGIS `PVcalc`.
- In media i consumi annui delle famiglie sono vicini al valore ARERA di Torino (somma dei 12 mesi) e non ci sono valori negativi.
- Ogni `socio_id` e `impianto_id` esiste nella sua tabella, e ogni `ts` è a ora piena in UTC con la `Z` finale.
- Ogni anomalia di `anomalie_vere.csv` si vede nei dati: la produzione è sotto l'atteso.
- Rilanciando con lo stesso seed si ottengono file identici (confronto degli hash).
- I grafici di controllo stanno in `data/notebook/`: una settimana estiva e una invernale per ogni impianto, e il profilo medio giornaliero per ogni tipo di socio.

**Soglie fissate nella parte 2 (27/11):**

- totale di ogni mese = ARERA × `scala` con uno scarto massimo di 0,4 kWh (744 ore × 0,0005 kWh di arrotondamento);
- media annua delle famiglie entro ±5% da ARERA in ciascuno dei due anni (la media delle 200 scale oscilla di circa il 2,5%);
- fasce F1/F2/F3 delle famiglie entro 3 punti dalla media ARERA pesata sui volumi (31,3 / 30,5 / 38,2%), calcolate in ora italiana, con il sabato festivo in F3;
- scuola: rapporto tra consumo medio dei feriali 9–15 e consumo 0–5 tra 0,8 e 1,25 a luglio–agosto, sopra 3 a ottobre;
- bollette: `kwh` uguale alla somma delle ore entro 0,0005 kWh, `importo_eur` giusto al centesimo.

**Aggiunti nella parte 3a (27/11):** ripartizione rifatta da zero ora per ora (energia condivisa ≤ min(produzione, consumi), nessuna quota oltre il consumo del socio, somma dei soci = totale di comunità, nessuna quota prima della `data_adesione`), tabelle provvisorie, riepilogo dei trimestri ricalcolato e intestazioni uguali alle colonne di `carica.sql`. Completo: 142/142.

**Da aggiungere con i testi (parte 3b):** ogni segnalazione di un socio dopo la sua adesione; ogni `guasto` e `stringa` con almeno una segnalazione e una comunicazione `interno`; categorie e urgenze tra i valori ammessi.

Su Windows, per salvare l'output di `controlli.py` in un file, impostare prima `$env:PYTHONIOENCODING = "utf-8"`.

---

## 7. Versione PICCOLA (campione per il SAL 1, su `main` dalla PR #8)

**Contenuto:**

- **Impianti:** 1, 2 e 3.
- **Soci:** 20, presi dalla lista completa con gli stessi ID e nomi, e aderenti entro il 1 giugno 2026:
  - 14 famiglie, tra cui il socio 42 usato in `api.md`, se è una famiglia aderente in tempo;
  - 4 imprese: bar, panificio, officina, parrucchiere;
  - 2 enti: la scuola di Pinerolo, che è anche il soggetto delle segnalazioni sul guasto dell'impianto 3, e gli uffici comunali di San Secondo di Pinerolo.
- **Periodo:** giugno 2026.
- **Regole:** le stesse del dataset completo, così il campione è un pezzo del dataset finale e i WSA non avranno sorprese.

**Scorciatoie ammesse solo per il campione:**

- **Consumi:** se il file ARERA non è ancora pronto, si usano volumi provvisori, dichiarati tali: famiglia 2.700 kWh/anno, impresa 15.000, ente 40.000.
  - **Come si applicano:** il volume annuo di ogni socio, moltiplicato per la sua scala, si distribuisce sull'anno dal 1/9/2025 al 31/8/2026 seguendo il profilo orario, cioè giorni e orari di apertura. Giugno riceve la sua parte.
  - **Perché quell'anno:** è un anno scolastico intero, coperto dal calendario 2025/26 già verificato.
  - **Effetto:** la scuola, che a giugno fa lezione solo 6 giorni, consuma meno della media annua.
- **Taratura PVGIS:** facoltativa, si può lasciare `k = 1`.
- **Tabelle calcolate, con valori provvisori:**
  - `previsione_produzione`: la formula senza anomalie, così si vede lo scarto del guasto;
  - `previsione_consumo`: il profilo senza rumore;
  - `anomalia`: una riga, cioè il guasto dell'impianto 3 dal `2026-06-01T11:00:00Z` al `2026-06-01T15:00:00Z`, con `score` 0.97 e `stato` `aperta`, come in `api.md`;
  - `ripartizione_mensile`: la formula del §3.6 applicata a giugno.
- **Testi:** 15 segnalazioni e 1 verbale scritti a mano o con un LLM, con le colonne `_llm` riempite a mano. Tra le segnalazioni, 2–3 riguardano il guasto del 1 giugno. Il verbale è quello dell'assemblea del 9 luglio 2026 (id 7) e cita i numeri di giugno degli impianti 1–3, calcolati dai CSV del campione.
- **Il campione resta con le sue scorciatoie** (volumi provvisori, profilo della famiglia scritto a mano, `k = 1`): il vincolo è non cambiarlo. Per questo giugno 2026 nel completo è diverso dal campione.

**Consegna:**

- **Cosa:** i CSV in `data/esempi/` e la v1 di `data/data-dictionary.md`, ricavata dal §4.
- **Nota per i WSA:**
  - `ripartizione_mensile` del campione è calcolata su 3 impianti e 20 soci, quindi l'energia condivisa è quasi uguale ai consumi diurni. Nel dataset completo i valori di giugno cambieranno, perché dipendono da tutti gli 8 impianti e i 240 soci.
  - Cambieranno anche i consumi, quando i volumi ARERA sostituiranno quelli provvisori.
  - Calerà di circa il 5% anche la produzione, quando si farà la taratura con PVGIS (§3.2).
  - **Aggiornamento 27/11:** nel completo è successo. Produzione circa −5% (`k_impianto` ≈ 0,95), famiglie da 2.700 a circa 1.550 kWh all'anno, quindi bollette e ripartizione di giugno cambiano. Anche segnalazioni (stato) e verbale di luglio cambiano (§3.7).
- **Mercoledì 18:** mandare a Luca le intestazioni dei CSV, anche senza dati, perché gli servono per lo script di caricamento.

---

## 8. Struttura del codice

```
data/
  CLAUDE.md              istruzioni per Claude Code
  GUIDA-DATASET.md       questa guida
  data-dictionary.md
  requirements.txt       pandas, numpy, requests, holidays, faker, matplotlib (pvlib facoltativo)
  generazione/
    config.py            PICCOLA / COMPLETA: impianti, soci, periodo, seed
    anagrafiche.py       impianto, socio, socio_profilo, parametro
    meteo.py             Open-Meteo → meteo_orario (+ cache)
    pvgis.py             PVGIS → k_impianto e confronto 2023
    produzione.py        produzione_oraria + anomalie_vere
    consumi.py           ARERA + profili → consumo_orario
    derivate.py          bolletta, ripartizione_mensile, tabelle calcolate provvisorie (campione e completo), riepilogo_trimestri
    testi.py             legge data/testi/ → segnalazione, segnalazione_etichette, verbale
  testi/                 sorgente fisso dei testi (su GitHub): segnalazioni_sorgente.csv, verbali/
    controlli.py         §6
    genera.py            lancia tutto: python genera.py --config piccola
  notebook/              esplorazione e grafici di controllo
  batch/                 previsioni, anomalie, ripartizione, classificazione (dopo il SAL 1)
  esempi/                campione SAL 1 (su GitHub)
  output/                dataset completo + cache API (escluso da Git)
```

---

## 9. Il lavoro di Giuseppe

Valutato nella chat Dataset del progetto: è costruito sul dataset Zenodo del Politecnico di Porto (2019, ogni 15 minuti, ora locale, 15 impianti privati da 3 a 13 kWp con autoconsumo), cioè su una base diversa da questa guida.

- Consumi, produzione e meteo si rifanno da zero con le regole dei §1–4.
- **Aggiornamento 27/11:** i suoi 329 testi sono costruiti in buona parte su modelli ripetuti (tolti saluti e firme restano circa 200 frasi diverse), sono del 2019, citano impianti privati P01–P15 e usano altre categorie (`consumi`, `portale`, `simulatore`). Si usano solo come spunti; i testi del completo si scrivono da capo (§3.7). La struttura dei verbali resta un buon riferimento.
- I file da riusare stanno in `data/output/giuseppe/` (escluso da Git). Il dataset completo di Giuseppe non va nel repo.

---

## 10. Da portare alla prossima riunione

1. **Valori da aggiornare:** valorizzazione ARERA e prezzi per imprese ed enti (§3.5).
2. **Design del database:** lo segue Giuseppe, in coppia con Luca, solo su PostgreSQL (deciso il 26/11). La PR #24 è una prima stesura. Il dataset non dipende da quella proposta: è il database che si costruisce sul dataset (§4).
3. **Per una v2 del dataset:** consumi legati alla temperatura (§3.4, punto 7) e mesi in ora italiana invece che in UTC (§2), che allineerebbero dashboard e ripartizione ai bordi del mese. Oggi costa di più, perché tocca consumi, bollette e ripartizione già generati.
4. **Data della demo:** proposta "oggi = 1/11/2026" nel portale, da concordare con i WSA.

Chiusi il 23 novembre: chi indica l'impianto (§3.7) e le modifiche allo schema (§4), accolti da Luca nel commit 5f1ec52. Chiusi il 26–27 novembre: niente NoSQL, testi scritti dal team dati, colonne di categoria vuote nel completo.

---

## Fonti

- Open-Meteo, Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api
- PVGIS 5.3 (JRC, Commissione europea): https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/pvgis-releases/pvgis-53_en
- ARERA, consumi dei clienti domestici: https://www.arera.it/dati-e-statistiche/dettaglio/analisi-dei-consumi-dei-clienti-domestici
- ARERA, consumi dei clienti non domestici in BT per ATECO: https://www.arera.it/dati-e-statistiche/dettaglio/analisi-dei-consumi-dei-clienti-domestici-ateco
- ISPRA, Rapporto 430/2026 "Settore elettrico: emissioni di CO2 e altri impatti": https://www.isprambiente.gov.it/files2026/pubblicazioni/rapporti/r430-2026-2.pdf
- MASE, "Strumenti di sostegno per le CACER – DM 414 del 2023" (tariffe e massimali): https://greencam.unioncamere.it/wp-content/uploads/2025/06/Strumenti-di-sostegno-per-le-CACER-DM-414-del-2023_Ministero-dell_Ambiente-e-della-Sicurezza-Energetica.pdf
- ANCE, nota sul decreto CER (corrispettivo ARERA di circa 8 €/MWh nel 2023): https://ance.it/wp-content/uploads/allegati/20240125_Decreto_CER_Nota_di_approfondimento.pdf
- Prezzo medio domestico 2025 dalla Relazione annuale ARERA (Teleborsa, 1/7/2026): https://www.teleborsa.it/News/2026/07/01/arera-prezzi-luce-e-gas-italiani-tra-i-piu-alti-in-europa-dell-acqua-differenziale-pesa-su-competitivita-319.html
