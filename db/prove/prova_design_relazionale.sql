-- Prove della migrazione 20261124090000_design_relazionale.
-- Da lanciare dopo migrate e seed. Tutto avviene in una transazione annullata
-- alla fine: i dati restano com'erano. Può avanzare solo il contatore degli ID
-- di storico_segnalazione, che non influisce sul funzionamento.
-- Se una prova non passa, lo script si ferma con "PROVA FALLITA".

\set ON_ERROR_STOP on
BEGIN;

CREATE FUNCTION pg_temp.deve_fallire(nome text, comando text) RETURNS void
LANGUAGE plpgsql AS $$
DECLARE
  rifiutato boolean := false;
BEGIN
  BEGIN
    EXECUTE comando;
  EXCEPTION WHEN integrity_constraint_violation THEN
    rifiutato := true;
  END;
  IF NOT rifiutato THEN
    RAISE EXCEPTION 'PROVA FALLITA: accettato "%"', nome;
  END IF;
  RAISE NOTICE 'ok (rifiutato): %', nome;
END;
$$;

CREATE FUNCTION pg_temp.deve_valere(nome text, condizione boolean) RETURNS void
LANGUAGE plpgsql AS $$
BEGIN
  IF condizione IS NOT TRUE THEN
    RAISE EXCEPTION 'PROVA FALLITA: %', nome;
  END IF;
  RAISE NOTICE 'ok: %', nome;
END;
$$;

-- Dati di prova con ID alti, per non toccare il campione
INSERT INTO socio (id, nome, tipo, comune, data_adesione) VALUES
  (900001, 'Socio di prova', 'famiglia', 'Pinerolo', '2024-06-01');
INSERT INTO impianto (id, nome, comune, lat, lon, kwp, inclinazione_gradi, azimut_gradi, data_attivazione) VALUES
  (900001, 'Impianto di prova A', 'Pinerolo', 44.88, 7.35, 10, 15, 0, '2024-01-01'),
  (900002, 'Impianto di prova B', 'Cavour',   44.79, 7.37, 10, 15, 0, '2024-01-01');
INSERT INTO utente (id, email, password_hash, ruolo) VALUES
  (900001, 'operatore.prova@example.com', 'x', 'operatore');
INSERT INTO anomalia (id, impianto_id, inizio, fine, tipo, score, stato) VALUES
  (900001, 900001, '2026-06-10T10:00:00Z', '2026-06-10T14:00:00Z', 'guasto', 0.9, 'aperta'),
  (900002, 900002, '2026-06-10T10:00:00Z', NULL, NULL, 0.5, 'aperta');
INSERT INTO segnalazione (id, socio_id, impianto_id, impianto_id_llm, ts, canale, testo,
                          categoria_llm, urgenza_llm, categoria, urgenza, stato) VALUES
  (900001, 900001, 900001, 900001, '2026-06-11T09:00:00Z', 'portale', 'L''inverter è spento',
   'guasto_impianto', 'alta', 'guasto_impianto', 'alta', 'aperta'),
  (900002, NULL, 900001, NULL, '2026-06-11T12:00:00Z', 'interno', 'Intervento concluso',
   NULL, NULL, NULL, NULL, 'chiusa');

-- Tabelle di riferimento
SELECT pg_temp.deve_valere('8 comuni', (SELECT count(*) = 8 FROM comune));
SELECT pg_temp.deve_valere('6 categorie', (SELECT count(*) = 6 FROM categoria_segnalazione));
SELECT pg_temp.deve_valere('alta viene prima di bassa',
  (SELECT a.ordine < b.ordine FROM urgenza a, urgenza b WHERE a.codice = 'alta' AND b.codice = 'bassa'));

SELECT pg_temp.deve_fallire('comune inesistente su socio',
  $q$UPDATE socio SET comune = 'Atlantide' WHERE id = 900001$q$);
SELECT pg_temp.deve_fallire('comune inesistente su impianto',
  $q$UPDATE impianto SET comune = 'Atlantide' WHERE id = 900001$q$);
SELECT pg_temp.deve_fallire('categoria inesistente',
  $q$UPDATE segnalazione SET categoria = 'boh' WHERE id = 900001$q$);
SELECT pg_temp.deve_fallire('cancellare un comune in uso',
  $q$DELETE FROM comune WHERE nome = 'Pinerolo'$q$);

-- Solo una chiave esterna può rifiutare queste cancellazioni (i vecchi CHECK no)
SELECT pg_temp.deve_fallire('cancellare un tipo socio in uso',
  $q$DELETE FROM tipo_socio WHERE codice = 'famiglia'$q$);
SELECT pg_temp.deve_fallire('cancellare un ruolo in uso',
  $q$DELETE FROM ruolo_utente WHERE codice = 'operatore'$q$);
SELECT pg_temp.deve_fallire('cancellare un tipo anomalia in uso',
  $q$DELETE FROM tipo_anomalia WHERE codice = 'guasto'$q$);
SELECT pg_temp.deve_fallire('cancellare uno stato anomalia in uso',
  $q$DELETE FROM stato_anomalia WHERE codice = 'aperta'$q$);
SELECT pg_temp.deve_fallire('cancellare un canale in uso',
  $q$DELETE FROM canale_segnalazione WHERE codice = 'portale'$q$);
SELECT pg_temp.deve_fallire('cancellare uno stato segnalazione in uso',
  $q$DELETE FROM stato_segnalazione WHERE codice = 'aperta'$q$);
SELECT pg_temp.deve_fallire('cancellare una categoria in uso',
  $q$DELETE FROM categoria_segnalazione WHERE codice = 'guasto_impianto'$q$);
SELECT pg_temp.deve_fallire('cancellare una urgenza in uso',
  $q$DELETE FROM urgenza WHERE codice = 'alta'$q$);

-- Regole in più
SELECT pg_temp.deve_fallire('segnalazione portale senza socio',
  $q$INSERT INTO segnalazione (id, socio_id, canale, testo) VALUES (900003, NULL, 'portale', 'x')$q$);
SELECT pg_temp.deve_fallire('comunicazione interna con socio',
  $q$INSERT INTO segnalazione (id, socio_id, canale, testo) VALUES (900004, 900001, 'interno', 'x')$q$);
SELECT pg_temp.deve_fallire('anomalia doppia',
  $q$INSERT INTO anomalia (id, impianto_id, inizio) VALUES (900003, 900001, '2026-06-10T10:00:00Z')$q$);
SELECT pg_temp.deve_fallire('email uguale con maiuscole',
  $q$INSERT INTO utente (id, email, password_hash, ruolo) VALUES (900002, 'OPERATORE.PROVA@example.com', 'x', 'admin')$q$);

-- Il batch può rilanciare senza riaprire un'anomalia chiusa
UPDATE anomalia SET stato = 'chiusa' WHERE id = 900001;
INSERT INTO anomalia (id, impianto_id, inizio, stato)
VALUES (900004, 900001, '2026-06-10T10:00:00Z', 'aperta')
ON CONFLICT (impianto_id, inizio) DO NOTHING;
SELECT pg_temp.deve_valere('anomalia chiusa resta chiusa',
  (SELECT stato = 'chiusa' FROM anomalia WHERE id = 900001));
UPDATE anomalia SET stato = 'aperta' WHERE id = 900001;

-- Colonne LLM
SELECT pg_temp.deve_fallire('modificare categoria_llm',
  $q$UPDATE segnalazione SET categoria_llm = 'reclamo' WHERE id = 900001$q$);
SELECT pg_temp.deve_fallire('modificare impianto_id_llm',
  $q$UPDATE segnalazione SET impianto_id_llm = 900002 WHERE id = 900001$q$);
UPDATE segnalazione SET categoria_llm = 'guasto_impianto', urgenza_llm = 'media' WHERE id = 900002;
SELECT pg_temp.deve_valere('LLM riempie una segnalazione rimasta senza risposta',
  (SELECT categoria_llm = 'guasto_impianto' FROM segnalazione WHERE id = 900002));

-- Storico
SELECT set_config('app.utente_id', '900001', true);
UPDATE segnalazione SET categoria = 'reclamo', stato = 'in_corso' WHERE id = 900001;
SELECT pg_temp.deve_valere('storico: due righe con l''utente',
  (SELECT count(*) = 2 AND bool_and(utente_id = 900001)
   FROM storico_segnalazione WHERE segnalazione_id = 900001));
SELECT pg_temp.deve_valere('storico: valori prima e dopo',
  (SELECT valore_prima = 'guasto_impianto' AND valore_dopo = 'reclamo'
   FROM storico_segnalazione WHERE segnalazione_id = 900001 AND campo = 'categoria'));
SELECT pg_temp.deve_valere('categoria_llm resta originale',
  (SELECT categoria_llm = 'guasto_impianto' FROM segnalazione WHERE id = 900001));
SELECT set_config('app.utente_id', '', true);
UPDATE segnalazione SET urgenza = 'bassa' WHERE id = 900001;
SELECT pg_temp.deve_valere('storico senza utente indicato',
  (SELECT utente_id IS NULL FROM storico_segnalazione
   WHERE segnalazione_id = 900001 AND campo = 'urgenza'));

-- Collegamento segnalazione-anomalia
SELECT pg_temp.deve_valere('la vista propone la coppia giusta',
  EXISTS (SELECT 1 FROM v_segnalazione_anomalia_candidata
          WHERE segnalazione_id = 900001 AND anomalia_id = 900001 AND NOT confermata));
SELECT pg_temp.deve_fallire('collegare impianti diversi',
  $q$INSERT INTO segnalazione_anomalia (segnalazione_id, anomalia_id) VALUES (900001, 900002)$q$);
INSERT INTO segnalazione_anomalia (segnalazione_id, anomalia_id, confermato_da)
VALUES (900001, 900001, 900001);
SELECT pg_temp.deve_valere('la vista mostra la conferma',
  (SELECT confermata FROM v_segnalazione_anomalia_candidata
   WHERE segnalazione_id = 900001 AND anomalia_id = 900001));
UPDATE segnalazione SET impianto_id = 900002 WHERE id = 900001;
SELECT pg_temp.deve_valere('cambiando impianto il collegamento vecchio sparisce',
  NOT EXISTS (SELECT 1 FROM segnalazione_anomalia WHERE segnalazione_id = 900001));

-- Interventi
INSERT INTO tecnico (id, nome, ditta) VALUES (900001, 'Tecnico di prova', 'Ditta di prova');
INSERT INTO intervento (id, anomalia_id, tecnico_id, segnalazione_id, inizio, fine, esito)
VALUES (900001, 900001, 900001, 900002, '2026-06-11T10:00:00Z', '2026-06-11T11:00:00Z', 'Inverter riarmato');
SELECT pg_temp.deve_fallire('intervento su segnalazione non interna',
  $q$INSERT INTO intervento (id, anomalia_id, segnalazione_id, inizio)
     VALUES (900002, 900001, 900001, '2026-06-11T10:00:00Z')$q$);
SELECT pg_temp.deve_fallire('intervento che finisce prima di iniziare',
  $q$INSERT INTO intervento (id, anomalia_id, inizio, fine)
     VALUES (900003, 900001, '2026-06-11T10:00:00Z', '2026-06-11T09:00:00Z')$q$);
SELECT pg_temp.deve_fallire('cancellare anomalia con interventi',
  $q$DELETE FROM anomalia WHERE id = 900001$q$);

-- Ricerca nei testi
SELECT pg_temp.deve_valere('ricerca full-text in italiano',
  EXISTS (SELECT 1 FROM segnalazione
          WHERE id = 900001
            AND to_tsvector('italian'::regconfig, testo) @@ plainto_tsquery('italian', 'inverter')));

ROLLBACK;
\echo 'TUTTE LE PROVE SONO PASSATE (nessuna modifica salvata)'
