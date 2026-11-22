-- Carica i CSV di /csv (data/esempi oppure data/output, vedi CARTELLA_CSV).
-- Un file per tabella, con il nome della tabella. Ordine: prima le tabelle
-- a cui le altre fanno riferimento.
-- HEADER match: le intestazioni del CSV devono avere gli stessi nomi e lo
-- stesso ordine delle colonne della tabella, altrimenti si ferma con l'errore.
-- Gira tutto in una transazione: o si carica tutto, o niente.
--
-- Non carica utente: lo crea il backend, con gli hash delle password.
-- Anomalie, previsioni e ripartizione nel progetto le scrive il batch: qui
-- si caricano i valori provvisori del campione, utili per le pagine.
-- I file 🏷 (anomalie_vere, segnalazione_etichette) e socio_profilo non
-- vanno nel database e restano fuori.

\copy impianto          FROM '/csv/impianto.csv'          WITH (FORMAT csv, HEADER match)
\copy socio             FROM '/csv/socio.csv'             WITH (FORMAT csv, HEADER match)
\copy parametro         FROM '/csv/parametro.csv'         WITH (FORMAT csv, HEADER match)
\copy verbale           FROM '/csv/verbale.csv'           WITH (FORMAT csv, HEADER match)
\copy produzione_oraria FROM '/csv/produzione_oraria.csv' WITH (FORMAT csv, HEADER match)
\copy meteo_orario      FROM '/csv/meteo_orario.csv'      WITH (FORMAT csv, HEADER match)
\copy consumo_orario    FROM '/csv/consumo_orario.csv'    WITH (FORMAT csv, HEADER match)
\copy bolletta          FROM '/csv/bolletta.csv'          WITH (FORMAT csv, HEADER match)
\copy segnalazione      FROM '/csv/segnalazione.csv'      WITH (FORMAT csv, HEADER match)
\copy anomalia          FROM '/csv/anomalia.csv'          WITH (FORMAT csv, HEADER match)
\copy previsione_produzione FROM '/csv/previsione_produzione.csv' WITH (FORMAT csv, HEADER match)
\copy previsione_consumo    FROM '/csv/previsione_consumo.csv'    WITH (FORMAT csv, HEADER match)
\copy ripartizione_mensile  FROM '/csv/ripartizione_mensile.csv'  WITH (FORMAT csv, HEADER match)

-- Gli ID di segnalazioni e anomalie sono arrivati dal CSV: i contatori
-- ripartono dopo l'ultimo, così backend e batch non creano un ID già usato.
SELECT setval(pg_get_serial_sequence('segnalazione', 'id'), max(id)) FROM segnalazione;
SELECT setval(pg_get_serial_sequence('anomalia', 'id'), max(id)) FROM anomalia;
