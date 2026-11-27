-- Design relazionale: estensione compatibile dello schema congelato al SAL 1.
-- PROPOSTA da approvare. Vedi docs/database-relazionale.md.
--
-- Non aggiunge, toglie o rinomina colonne delle 14 tabelle esistenti:
-- CSV, HEADER match, backend e contratto API restano validi.
-- Le tabelle di riferimento usano chiavi di testo, così le chiavi esterne
-- si appoggiano alle colonne che esistono già.

-- migrate:up

-- 1. Tabelle di riferimento

CREATE TABLE comune (
  nome text PRIMARY KEY
);
INSERT INTO comune (nome) VALUES
  ('Bricherasio'),
  ('Buriasco'),
  ('Cavour'),
  ('Luserna San Giovanni'),
  ('Pinerolo'),
  ('San Secondo di Pinerolo'),
  ('Torre Pellice'),
  ('Villar Perosa');

CREATE TABLE tipo_socio (
  codice      text PRIMARY KEY,
  descrizione text NOT NULL
);
INSERT INTO tipo_socio (codice, descrizione) VALUES
  ('famiglia', 'Famiglia'),
  ('impresa',  'Impresa'),
  ('ente',     'Ente');

CREATE TABLE ruolo_utente (
  codice      text PRIMARY KEY,
  descrizione text NOT NULL
);
INSERT INTO ruolo_utente (codice, descrizione) VALUES
  ('socio',     'Vede solo i propri dati'),
  ('operatore', 'Gestisce impianti, anomalie e segnalazioni'),
  ('admin',     'Vede tutti i dati della comunità');

CREATE TABLE canale_segnalazione (
  codice      text PRIMARY KEY,
  descrizione text NOT NULL
);
INSERT INTO canale_segnalazione (codice, descrizione) VALUES
  ('email',   'Email del socio'),
  ('portale', 'Modulo del portale'),
  ('interno', 'Comunicazione interna su guasti e interventi');

CREATE TABLE categoria_segnalazione (
  codice      text PRIMARY KEY,
  descrizione text NOT NULL
);
INSERT INTO categoria_segnalazione (codice, descrizione) VALUES
  ('guasto_impianto',        'Guasto o calo di produzione di un impianto'),
  ('bolletta_pagamenti',     'Bollette e pagamenti'),
  ('incentivi_ripartizione', 'Incentivi e ripartizione tra i soci'),
  ('adesione_recesso',       'Ingresso o uscita dalla comunità'),
  ('informazioni',           'Richiesta di informazioni'),
  ('reclamo',                'Reclamo');

CREATE TABLE urgenza (
  codice      text PRIMARY KEY,
  ordine      smallint NOT NULL UNIQUE,  -- la coda ordina per questo valore: 1 = più urgente
  descrizione text NOT NULL
);
INSERT INTO urgenza (codice, ordine, descrizione) VALUES
  ('alta',  1, 'Da gestire subito'),
  ('media', 2, 'Da gestire a breve'),
  ('bassa', 3, 'Può attendere');

CREATE TABLE stato_segnalazione (
  codice      text PRIMARY KEY,
  descrizione text NOT NULL
);
INSERT INTO stato_segnalazione (codice, descrizione) VALUES
  ('aperta',   'Da prendere in carico'),
  ('in_corso', 'In lavorazione'),
  ('chiusa',   'Risolta');

CREATE TABLE stato_anomalia (
  codice      text PRIMARY KEY,
  descrizione text NOT NULL
);
INSERT INTO stato_anomalia (codice, descrizione) VALUES
  ('aperta', 'Rilevata, da gestire'),
  ('chiusa', 'Chiusa dall''operatore');

CREATE TABLE tipo_anomalia (
  codice      text PRIMARY KEY,
  descrizione text NOT NULL
);
INSERT INTO tipo_anomalia (codice, descrizione) VALUES
  ('guasto',    'Produzione a zero nelle ore di sole'),
  ('sporcizia', 'Calo graduale fino alla pulizia'),
  ('stringa',   'Calo fisso fino alla riparazione'),
  ('neve',      'Produzione quasi nulla dopo una nevicata');

-- 2. Chiavi esterne sulle colonne esistenti
-- I CHECK della prima migrazione restano: la regola è doppia, ma lo schema
-- congelato non viene toccato.

ALTER TABLE socio
  ADD CONSTRAINT fk_socio_comune FOREIGN KEY (comune) REFERENCES comune (nome),
  ADD CONSTRAINT fk_socio_tipo   FOREIGN KEY (tipo)   REFERENCES tipo_socio (codice);

ALTER TABLE impianto
  ADD CONSTRAINT fk_impianto_comune FOREIGN KEY (comune) REFERENCES comune (nome);

ALTER TABLE utente
  ADD CONSTRAINT fk_utente_ruolo FOREIGN KEY (ruolo) REFERENCES ruolo_utente (codice);

ALTER TABLE anomalia
  ADD CONSTRAINT fk_anomalia_tipo  FOREIGN KEY (tipo)  REFERENCES tipo_anomalia (codice),
  ADD CONSTRAINT fk_anomalia_stato FOREIGN KEY (stato) REFERENCES stato_anomalia (codice);

ALTER TABLE segnalazione
  ADD CONSTRAINT fk_segnalazione_canale        FOREIGN KEY (canale)        REFERENCES canale_segnalazione (codice),
  ADD CONSTRAINT fk_segnalazione_stato         FOREIGN KEY (stato)         REFERENCES stato_segnalazione (codice),
  ADD CONSTRAINT fk_segnalazione_categoria     FOREIGN KEY (categoria)     REFERENCES categoria_segnalazione (codice),
  ADD CONSTRAINT fk_segnalazione_categoria_llm FOREIGN KEY (categoria_llm) REFERENCES categoria_segnalazione (codice),
  ADD CONSTRAINT fk_segnalazione_urgenza       FOREIGN KEY (urgenza)       REFERENCES urgenza (codice),
  ADD CONSTRAINT fk_segnalazione_urgenza_llm   FOREIGN KEY (urgenza_llm)   REFERENCES urgenza (codice);

-- 3. Regole in più

-- Le comunicazioni interne non hanno socio, tutte le altre sì.
ALTER TABLE segnalazione
  ADD CONSTRAINT ck_segnalazione_interno CHECK ((canale = 'interno') = (socio_id IS NULL));

-- Il batch può rilanciare con ON CONFLICT DO NOTHING senza riaprire le anomalie chiuse.
ALTER TABLE anomalia
  ADD CONSTRAINT uq_anomalia_impianto_inizio UNIQUE (impianto_id, inizio);

-- Il login confronta lower(email): due account non possono differire solo per le maiuscole.
CREATE UNIQUE INDEX ux_utente_email_lower ON utente (lower(email));

-- 4. Relazioni e storico

-- Collegamento confermato da un operatore. I candidati sono nella vista in fondo.
CREATE TABLE segnalazione_anomalia (
  segnalazione_id integer NOT NULL REFERENCES segnalazione (id) ON DELETE CASCADE,
  anomalia_id     integer NOT NULL REFERENCES anomalia (id) ON DELETE CASCADE,
  confermato_da   integer REFERENCES utente (id) ON DELETE SET NULL,
  confermato_il   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (segnalazione_id, anomalia_id)
);

-- Una riga per ogni campo cambiato. La scrive il trigger, non l'applicazione.
CREATE TABLE storico_segnalazione (
  id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  segnalazione_id integer NOT NULL REFERENCES segnalazione (id) ON DELETE CASCADE,
  utente_id       integer REFERENCES utente (id) ON DELETE SET NULL,  -- null se il backend non lo indica
  ts              timestamptz NOT NULL DEFAULT now(),
  campo           text NOT NULL CHECK (campo IN ('stato', 'categoria', 'urgenza', 'impianto_id')),
  valore_prima    text,
  valore_dopo     text
);

CREATE TABLE tecnico (
  id    integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  nome  text NOT NULL,
  ditta text NOT NULL,
  UNIQUE (nome, ditta)
);

-- Dati strutturati dell'intervento. Il testo resta nella segnalazione con canale 'interno'.
CREATE TABLE intervento (
  id              integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  anomalia_id     integer NOT NULL REFERENCES anomalia (id),
  tecnico_id      integer REFERENCES tecnico (id),
  segnalazione_id integer UNIQUE REFERENCES segnalazione (id) ON DELETE SET NULL,
  inizio          timestamptz NOT NULL,
  fine            timestamptz,
  esito           text,
  CONSTRAINT ck_intervento_periodo CHECK (fine IS NULL OR fine >= inizio)
);

-- 5. Trigger

-- Le risposte dell'LLM si possono riempire una volta, poi non cambiano più.
CREATE FUNCTION blocca_modifica_llm() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF (OLD.categoria_llm   IS NOT NULL AND NEW.categoria_llm   IS DISTINCT FROM OLD.categoria_llm)
  OR (OLD.urgenza_llm     IS NOT NULL AND NEW.urgenza_llm     IS DISTINCT FROM OLD.urgenza_llm)
  OR (OLD.impianto_id_llm IS NOT NULL AND NEW.impianto_id_llm IS DISTINCT FROM OLD.impianto_id_llm) THEN
    RAISE EXCEPTION 'Le colonne *_llm non si modificano (segnalazione %)', OLD.id
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER tr_segnalazione_blocca_llm
  BEFORE UPDATE OF categoria_llm, urgenza_llm, impianto_id_llm ON segnalazione
  FOR EACH ROW EXECUTE FUNCTION blocca_modifica_llm();

-- Il backend può indicare chi agisce, nella stessa transazione:
--   SELECT set_config('app.utente_id', '7', true);
CREATE FUNCTION registra_storico_segnalazione() RETURNS trigger
LANGUAGE plpgsql AS $$
DECLARE
  chi integer := NULLIF(current_setting('app.utente_id', true), '')::integer;
BEGIN
  IF NEW.stato IS DISTINCT FROM OLD.stato THEN
    INSERT INTO storico_segnalazione (segnalazione_id, utente_id, campo, valore_prima, valore_dopo)
    VALUES (NEW.id, chi, 'stato', OLD.stato, NEW.stato);
  END IF;
  IF NEW.categoria IS DISTINCT FROM OLD.categoria THEN
    INSERT INTO storico_segnalazione (segnalazione_id, utente_id, campo, valore_prima, valore_dopo)
    VALUES (NEW.id, chi, 'categoria', OLD.categoria, NEW.categoria);
  END IF;
  IF NEW.urgenza IS DISTINCT FROM OLD.urgenza THEN
    INSERT INTO storico_segnalazione (segnalazione_id, utente_id, campo, valore_prima, valore_dopo)
    VALUES (NEW.id, chi, 'urgenza', OLD.urgenza, NEW.urgenza);
  END IF;
  IF NEW.impianto_id IS DISTINCT FROM OLD.impianto_id THEN
    INSERT INTO storico_segnalazione (segnalazione_id, utente_id, campo, valore_prima, valore_dopo)
    VALUES (NEW.id, chi, 'impianto_id', OLD.impianto_id::text, NEW.impianto_id::text);
    -- Se cambia l'impianto, i collegamenti ad anomalie di altri impianti non valgono più.
    DELETE FROM segnalazione_anomalia sa
    USING anomalia a
    WHERE sa.segnalazione_id = NEW.id
      AND a.id = sa.anomalia_id
      AND a.impianto_id IS DISTINCT FROM NEW.impianto_id;
  END IF;
  RETURN NULL;
END;
$$;

CREATE TRIGGER tr_segnalazione_storico
  AFTER UPDATE OF stato, categoria, urgenza, impianto_id ON segnalazione
  FOR EACH ROW EXECUTE FUNCTION registra_storico_segnalazione();

-- Si collegano solo segnalazione e anomalia dello stesso impianto.
CREATE FUNCTION controlla_segnalazione_anomalia() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM segnalazione s
    JOIN anomalia a ON a.impianto_id = s.impianto_id
    WHERE s.id = NEW.segnalazione_id AND a.id = NEW.anomalia_id
  ) THEN
    RAISE EXCEPTION 'Segnalazione % e anomalia % non riguardano lo stesso impianto',
      NEW.segnalazione_id, NEW.anomalia_id
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER tr_segnalazione_anomalia_controllo
  BEFORE INSERT OR UPDATE ON segnalazione_anomalia
  FOR EACH ROW EXECUTE FUNCTION controlla_segnalazione_anomalia();

-- Un intervento può citare solo una comunicazione interna.
CREATE FUNCTION controlla_intervento() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.segnalazione_id IS NOT NULL AND NOT EXISTS (
    SELECT 1 FROM segnalazione s WHERE s.id = NEW.segnalazione_id AND s.canale = 'interno'
  ) THEN
    RAISE EXCEPTION 'La segnalazione % non è una comunicazione interna', NEW.segnalazione_id
      USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END;
$$;

CREATE TRIGGER tr_intervento_controllo
  BEFORE INSERT OR UPDATE ON intervento
  FOR EACH ROW EXECUTE FUNCTION controlla_intervento();

-- 6. Vista per US-15: stesso impianto, dal giorno prima a tre giorni dopo l'anomalia

CREATE VIEW v_segnalazione_anomalia_candidata AS
SELECT
  s.id AS segnalazione_id,
  a.id AS anomalia_id,
  s.impianto_id,
  s.ts AS segnalazione_ts,
  a.inizio AS anomalia_inizio,
  a.fine AS anomalia_fine,
  a.stato AS anomalia_stato,
  EXISTS (
    SELECT 1 FROM segnalazione_anomalia sa
    WHERE sa.segnalazione_id = s.id AND sa.anomalia_id = a.id
  ) AS confermata
FROM segnalazione s
JOIN anomalia a ON a.impianto_id = s.impianto_id
WHERE s.ts >= a.inizio - interval '1 day'
  AND s.ts <= COALESCE(a.fine, s.ts) + interval '3 days';

-- 7. Indici

CREATE INDEX ix_consumo_orario_ts         ON consumo_orario (ts);
CREATE INDEX ix_produzione_oraria_ts      ON produzione_oraria (ts);
CREATE INDEX ix_ripartizione_mensile_mese ON ripartizione_mensile (mese);
CREATE INDEX ix_segnalazione_coda         ON segnalazione (stato, urgenza, ts);
CREATE INDEX ix_segnalazione_socio_ts     ON segnalazione (socio_id, ts DESC);
CREATE INDEX ix_segnalazione_impianto_ts  ON segnalazione (impianto_id, ts);
CREATE INDEX ix_anomalia_aperte           ON anomalia (impianto_id) WHERE stato = 'aperta';
CREATE INDEX ix_segn_anomalia_anomalia    ON segnalazione_anomalia (anomalia_id);
CREATE INDEX ix_storico_segnalazione      ON storico_segnalazione (segnalazione_id, ts);
CREATE INDEX ix_intervento_anomalia       ON intervento (anomalia_id);
CREATE INDEX ix_intervento_tecnico        ON intervento (tecnico_id);

-- Ricerca nei testi: le query devono usare la stessa espressione,
-- per esempio to_tsvector('italian'::regconfig, testo) @@ plainto_tsquery('italian', 'inverter')
CREATE INDEX ix_segnalazione_testo_fts ON segnalazione USING gin (to_tsvector('italian'::regconfig, testo));
CREATE INDEX ix_verbale_testo_fts      ON verbale      USING gin (to_tsvector('italian'::regconfig, testo));

-- migrate:down

DROP VIEW v_segnalazione_anomalia_candidata;

DROP TRIGGER tr_intervento_controllo ON intervento;
DROP TRIGGER tr_segnalazione_anomalia_controllo ON segnalazione_anomalia;
DROP TRIGGER tr_segnalazione_storico ON segnalazione;
DROP TRIGGER tr_segnalazione_blocca_llm ON segnalazione;
DROP FUNCTION controlla_intervento();
DROP FUNCTION controlla_segnalazione_anomalia();
DROP FUNCTION registra_storico_segnalazione();
DROP FUNCTION blocca_modifica_llm();

DROP TABLE intervento, tecnico, storico_segnalazione, segnalazione_anomalia;

DROP INDEX ix_verbale_testo_fts, ix_segnalazione_testo_fts, ix_anomalia_aperte,
  ix_segnalazione_impianto_ts, ix_segnalazione_socio_ts, ix_segnalazione_coda,
  ix_ripartizione_mensile_mese, ix_produzione_oraria_ts, ix_consumo_orario_ts,
  ux_utente_email_lower;

ALTER TABLE anomalia
  DROP CONSTRAINT uq_anomalia_impianto_inizio,
  DROP CONSTRAINT fk_anomalia_stato,
  DROP CONSTRAINT fk_anomalia_tipo;

ALTER TABLE segnalazione
  DROP CONSTRAINT ck_segnalazione_interno,
  DROP CONSTRAINT fk_segnalazione_urgenza_llm,
  DROP CONSTRAINT fk_segnalazione_urgenza,
  DROP CONSTRAINT fk_segnalazione_categoria_llm,
  DROP CONSTRAINT fk_segnalazione_categoria,
  DROP CONSTRAINT fk_segnalazione_stato,
  DROP CONSTRAINT fk_segnalazione_canale;

ALTER TABLE utente   DROP CONSTRAINT fk_utente_ruolo;
ALTER TABLE impianto DROP CONSTRAINT fk_impianto_comune;
ALTER TABLE socio
  DROP CONSTRAINT fk_socio_tipo,
  DROP CONSTRAINT fk_socio_comune;

DROP TABLE tipo_anomalia, stato_anomalia, stato_segnalazione, urgenza,
  categoria_segnalazione, canale_segnalazione, ruolo_utente, tipo_socio, comune;
