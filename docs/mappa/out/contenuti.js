// Contenuti strutturati di tutte le viste di UnderTheSun.
// Per far crescere la documentazione col progetto basta aggiornare questo file e ricompilare i .d2 con ./compila.sh.
window.UTS_DATA = {
  navOrder: [
    { id: 'generale', label: 'Vista generale' },
    { id: 'database', label: 'Database' },
    { id: 'backend', label: 'Backend' },
    { id: 'flusso_llm', label: 'Flusso LLM' },
    { id: 'frontend', label: 'Frontend' },
    { id: 'dati', label: 'Pipeline dati' },
    { id: 'devops', label: 'CI & DevOps' },
    { id: 'sprint1', label: 'Sprint 1' },
    { id: 'storico', label: 'Storico GitHub' }
  ],

  calendario: [
    { date: 'ven 6 nov', title: '1 · Kickoff', desc: 'Creazione del repo su brief Buby Green; due team: WSA e data analyst', stato: 'fatto' },
    { date: '6 → 23 nov', title: '2 · Sprint 0 · Fondamenta', desc: 'Bozza docs 6 nov · piano v0.1 13 nov · DB in Docker 16 nov · campione dati 19 nov · backend, mappa e Pages 23 nov', stato: 'fatto' },
    { date: 'lun 23 nov', title: '3 · SAL 1 · schema e API congelati', desc: 'Schema e contratto API congelati; #6, #8, #9 su main (presentazione rimandata)', stato: 'fatto' },
    { date: '23 nov → 4 dic', title: '4 · Sprint 1 (in corso)', desc: '11 Issue (#11–#20, #25) · PR aperte al 25 nov: #10 CI, #23 login JWT, #24 proposta DB, #28 verbali', stato: 'sprint1', link: 'sprint1' },
    { date: 'ven 27 nov', title: '5 · Mini SAL col cliente', desc: 'Stato progetto, architettura e 3–4 domande puntuali', stato: 'sprint1' },
    { date: 'ven 4 dic', title: '6 · SAL 2', desc: 'Dataset 2 anni, modelli, classificazione testi', stato: 'sprint2' },
    { date: '4 → 14 dic', title: '7 · Sprint 2', desc: 'Tutte le pagine, simulatore, batch e operatore/admin', stato: 'sprint2' },
    { date: 'ven 18 dic', title: '8 · SAL finale col cliente', desc: 'Prototipo con le 5 storie complete', stato: 'sprint2' },
    { date: 'gennaio 2027', title: '9 · Presentazione finale', desc: '2–3 lezioni di rifinitura, presentazione nell\'ultima', stato: 'sprint2' }
  ],

  views: {
    generale: {
      title: 'UnderTheSun — Architettura della piattaforma',
      subtitle: 'Portale della <strong>Comunità Energetica Rinnovabile Buby Green</strong> · team <strong>PlusUltra</strong> · stato al <strong>25 novembre 2026</strong>. Clicca qualunque blocco nel diagramma qui sotto per aprirne i dettagli con zoom-in.',
      badges: [
        { cls: 'fatto', text: '10 PR unite su main (#1–#3, #6, #8, #9, #21, #22, #26, #27)' },
        { cls: 'revisione', text: 'PR aperte: #10 CI, #23 frontend, #28 verbali · proposta DB #24' },
        { cls: 'sprint1', text: 'Sprint 1 · 11 Issue (#11–#20, #25)' },
        { cls: 'sprint2', text: 'Sprint 2 · 4 → 14 dic' }
      ],
      diagrams: [
        {
          id: 'generale',
          caption: 'Vista semplificata · architettura e collegamenti principali',
          hint: 'Clicca un blocco per esplorarlo'
        }
      ],
      showCalendar: true,
      choicesTitle: 'Le 6 scelte che reggono l\'architettura (e perché)',
      choices: [
        {
          title: '1 · Il database è il punto d\'incontro',
          body: 'Frontend e pipeline Python <strong>non si parlano mai</strong>: si incontrano nelle 14 tabelle. Lo schema SQL e <code>docs/api.md</code>, congelati al SAL 1, sono il contratto tra WSA e team dati.',
          why: 'Due gruppi con competenze diverse lavorano in parallelo senza aspettarsi; se una parte cambia, la CI (job integrazione) se ne accorge subito.'
        },
        {
          title: '2 · Niente calcoli pesanti al clic',
          body: 'Previsioni, anomalie e ripartizione dell\'incentivo le calcolano <strong>batch Python offline</strong> e le salvano nel DB. Al volo si fanno solo il simulatore e la classificazione di una nuova segnalazione.',
          why: 'Pagine veloci, Python resta separato da Node, e i modelli si possono rifare senza toccare il backend.'
        },
        {
          title: '3 · Tempo sempre in UTC',
          body: 'Colonne <code>timestamptz</code>, contenitori con <code>TZ=UTC</code>, API in ISO 8601 con la <code>Z</code>. Solo il browser converte in ora italiana (<code>Europe/Rome</code>).',
          why: 'Col cambio dell\'ora legale un giorno può avere 23 o 25 ore: in UTC le serie orarie non hanno buchi né doppioni.'
        },
        {
          title: '4 · Permessi decisi dal server',
          body: 'Il token JWT porta solo <code>ruolo</code> e <code>socio_id</code>. Nell\'area socio il backend usa <strong>sempre</strong> il <code>socio_id</code> del token, mai un id mandato dal browser. L\'operatore vede i consumi solo aggregati.',
          why: 'Il frontend si può manomettere, il server no; e il GDPR chiede minimizzazione dei dati.'
        },
        {
          title: '5 · L\'LLM aiuta ma non blocca',
          body: 'La chiave dell\'LLM vive solo nel <code>.env</code> del backend. Se il servizio gratuito è lento o finisce la quota, la segnalazione si salva lo stesso (<code>201</code>) e l\'operatore la classifica a mano.',
          why: 'Una segnalazione persa è peggio di una non classificata. Le colonne <code>*_llm</code> restano immutate per misurare l\'accuratezza (US-12).'
        },
        {
          title: '6 · Riproducibile su ogni PC',
          body: 'Docker Compose (Docker Desktop su Windows, Podman su Fedora), dati generati da script con <strong>seed fisso 42</strong>. Nel repo vanno solo script e campione di giugno, mai i 2 anni completi.',
          why: 'Chiunque del team rigenera gli stessi file e lo stesso database con due comandi, e il repo resta leggero.'
        }
      ]
    },

    database: {
      title: 'Database · PostgreSQL 17 + dbmate',
      subtitle: '<strong>Unito su main</strong> (PR #6 di <strong>Luca (@lufo-336)</strong>, approvata da <strong>Mirko (@mirkodivincenzo)</strong> e provata da <strong>Stefano (@stefanospadaccini-888)</strong> su Docker Desktop/Windows 11 e da <strong>Luca (@lufo-336)</strong> su Podman/Fedora). Schema <strong>congelato al SAL 1</strong> con <strong>14 tabelle</strong>: anagrafiche (<code>socio</code>, <code>utente</code>, <code>impianto</code>, <code>parametro</code>, <code>verbale</code>), serie e bollette (<code>produzione_oraria</code>, <code>meteo_orario</code>, <code>consumo_orario</code>, <code>bolletta</code>), derivate (<code>previsione_produzione</code>, <code>previsione_consumo</code>, <code>ripartizione_mensile</code>, <code>anomalia</code>) e <code>segnalazione</code>.',
      badges: [
        { cls: 'fatto', text: 'PR #6 unita su main · dbmate:2.38.1' },
        { cls: 'fatto', text: '14 tabelle · vincoli CHECK · TZ=UTC · 13 CSV' },
        { cls: 'sprint2', text: 'PR #24 proposta team dati (aperta, non su main)' },
        { cls: 'sprint1', text: 'Sprint 1: 2 anni locali con CARTELLA_CSV=output (#18)' }
      ],
      links: [
        { label: 'PR #6 su GitHub ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/6' },
        { label: 'PR #24 (proposta team dati) ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/24', secondary: true },
        { label: 'Issue #18 (dataset 2 anni) ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/18', secondary: true }
      ],
      diagrams: [
        { id: 'database_avvio', caption: 'Avvio in Docker Compose · healthcheck e depends_on' },
        { id: 'database', caption: 'Modello relazionale completo · 14 tabelle', hint: 'Usa "Espandi" per leggere tutte le colonne a schermo intero' }
      ],
      fatto: {
        title: 'Già fatto in quest\'area',
        items: [
          { date: '9 → 13 nov', who: 'Luca (@lufo-336)', what: 'Correzioni al modello dati (previsioni, stato anomalie, correzioni operatore) nei documenti di progetto', ref: 'PR #2', href: 'https://github.com/lufo-336/under-the-sun/pull/2', stato: 'fatto' },
          { date: '16 nov', who: 'Luca (@lufo-336)', what: 'Database PostgreSQL 17 in Compose con <code>dbmate:2.38.1</code>, 14 tabelle e caricamento atomico di 13 CSV (commit <code>542728c</code>)', ref: 'PR #6', href: 'https://github.com/lufo-336/under-the-sun/pull/6', stato: 'fatto' },
          { date: '17 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Approvazione della PR #6', ref: 'PR #6', href: 'https://github.com/lufo-336/under-the-sun/pull/6', stato: 'fatto' },
          { date: '22 nov', who: 'Luca (@lufo-336)', what: 'Schema SQL allineato al data dictionary v1 del team dati (commit <code>5f1ec52</code>)', ref: 'PR #6', href: 'https://github.com/lufo-336/under-the-sun/pull/6', stato: 'fatto' },
          { date: '23 nov', who: 'Stefano (@stefanospadaccini-888) · Luca (@lufo-336)', what: 'Prova del commit finale con i 13 CSV della PR #8: avvio, migrazioni e seed su Docker Desktop/Windows 11 (Stefano) e su Podman/Fedora (Luca)', ref: 'PR #6', href: 'https://github.com/lufo-336/under-the-sun/pull/6', stato: 'fatto' },
          { date: '23 nov', who: 'Luca (@lufo-336)', what: 'Merge su <code>main</code> (<code>31dfa21</code>); schema iniziale congelato al SAL 1', ref: 'PR #6', href: 'https://github.com/lufo-336/under-the-sun/pull/6', stato: 'fatto' },
          { date: '23 nov', who: 'Giuseppe (@ASTROBLAST25)', what: 'Proposta aperta di seconda migrazione relazionale (tabelle di riferimento, storico interventi, trigger, indici e prove SQL/Python), non unita su <code>main</code>', ref: 'PR #24', href: 'https://github.com/lufo-336/under-the-sun/pull/24', stato: 'sprint2' },
          { date: 'Sprint 1', who: 'Francesco (@francescocolohan)', what: 'Caricamento locale del dataset completo di 2 anni tramite <code>CARTELLA_CSV=output</code>', ref: 'Issue #18', href: 'https://github.com/lufo-336/under-the-sun/issues/18', stato: 'sprint1' }
        ]
      },
      choices: [
        {
          title: 'Vincoli nel database, non solo nel codice',
          body: '<code>CHECK</code> su ruoli, categorie, urgenze, canali, stati, <code>score</code> tra 0 e 1, <code>kwp &gt; 0</code>, <code>inclinazione_gradi</code> 0–90, <code>azimut_gradi</code> −180..180, <code>mese</code> sempre il giorno 1; chiavi esterne ovunque.',
          why: 'I dati arrivano da due strade (CSV di Python e API di Node): un solo guardiano nel DB ferma gli errori di entrambe.'
        },
        {
          title: 'Migrazioni versionate con dbmate',
          body: 'Un file SQL con <code>-- migrate:up</code> e <code>-- migrate:down</code>; il servizio <code>migrate</code> (<code>dbmate:2.38.1</code>) applica solo i file nuovi.',
          why: 'È SQL puro (lo legge anche il team dati), gira uguale in locale e in CI e non lega lo schema a un ORM di Node.'
        },
        {
          title: 'Caricamento atomico con HEADER match',
          body: '<code>\\copy ... WITH (FORMAT csv, HEADER match)</code> dentro <code>--single-transaction</code>: se un CSV ha colonne diverse o in altro ordine si ferma senza lasciare dati a metà.',
          why: 'È il controllo automatico del contratto dati tra team dati e WSA.'
        },
        {
          title: 'Valori LLM separati da quelli in uso',
          body: 'In <code>segnalazione</code> coesistono <code>categoria_llm</code>/<code>categoria</code>, <code>urgenza_llm</code>/<code>urgenza</code> e <code>impianto_id_llm</code>/<code>impianto_id</code>.',
          why: 'L\'operatore corregge solo i valori in uso: il confronto diretto misura l\'accuratezza dell\'LLM (US-12).'
        },
        {
          title: 'ID dai CSV, contatori riallineati',
          body: 'Solo <code>utente</code>, <code>anomalia</code> e <code>segnalazione</code> generano ID da sole; dopo il seed <code>setval</code> sposta le sequenze dopo l\'ultimo ID caricato.',
          why: 'Stessi ID tra campione e dataset completo, senza collisioni quando scrive il backend.'
        },
        {
          title: 'Cross-platform Windows + Fedora SELinux',
          body: 'Porte esposte solo su <code>127.0.0.1</code> (<code>5433</code> di default); volumi del repo montati con <code>:ro,z</code> (necessario su Fedora SELinux, ignorato altrove; mai <code>:Z</code>).',
          why: 'Lo stesso <code>compose.yaml</code> funziona sia su Docker Desktop Windows 11 sia su Podman Fedora.'
        }
      ],
      codeBlocks: [
        {
          file: 'db/migrations/20261116090000_schema_iniziale.sql · utente',
          lang: 'sql',
          code: `CREATE TABLE utente (
  id            integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  email         text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  ruolo         text NOT NULL CHECK (ruolo IN ('socio', 'operatore', 'admin')),
  socio_id      integer UNIQUE REFERENCES socio (id),
  -- un socio ha sempre il suo socio_id, un dipendente mai
  CHECK ((ruolo = 'socio') = (socio_id IS NOT NULL))
);`,
          note: '<strong>Nota:</strong> l\'ultimo <code>CHECK</code> confronta due booleani: un socio deve avere <code>socio_id</code>, un operatore o admin non può averlo.'
        },
        {
          file: 'db/migrations/20261116090000_schema_iniziale.sql · segnalazione',
          lang: 'sql',
          code: `CREATE TABLE segnalazione (
  id              integer GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
  socio_id        integer REFERENCES socio (id),      -- null per le comunicazioni interne
  impianto_id     integer REFERENCES impianto (id),   -- valore in uso, l'operatore può correggerlo
  impianto_id_llm integer REFERENCES impianto (id),   -- dall'LLM, mai modificato
  ts              timestamptz NOT NULL DEFAULT now(),
  canale          text NOT NULL CHECK (canale IN ('email', 'portale', 'interno')),
  testo           text NOT NULL,
  categoria_llm   text,   -- dall'LLM, mai modificata
  urgenza_llm     text,   -- dall'LLM, mai modificata
  categoria       text,   -- valore in uso, l'operatore può correggerlo
  urgenza         text,   -- valore in uso, l'operatore può correggerlo
  stato           text NOT NULL DEFAULT 'aperta' CHECK (stato IN ('aperta', 'in_corso', 'chiusa')),
  CHECK (categoria_llm IN ('guasto_impianto', 'bolletta_pagamenti', 'incentivi_ripartizione',
                           'adesione_recesso', 'informazioni', 'reclamo')),
  CHECK (categoria     IN ('guasto_impianto', 'bolletta_pagamenti', 'incentivi_ripartizione',
                           'adesione_recesso', 'informazioni', 'reclamo')),
  CHECK (urgenza_llm IN ('alta', 'media', 'bassa')),
  CHECK (urgenza     IN ('alta', 'media', 'bassa'))
);`,
          note: '<strong>Nota:</strong> in SQL un <code>CHECK</code> su <code>NULL</code> passa: così una segnalazione arrivata con l\'LLM irraggiungibile si salva comunque, mentre una categoria inventata viene rifiutata.'
        },
        {
          file: 'db/seed/carica.sql · caricamento atomico e setval',
          lang: 'sql',
          code: `\\copy impianto             FROM '/csv/impianto.csv'             WITH (FORMAT csv, HEADER match)
\\copy socio                FROM '/csv/socio.csv'                WITH (FORMAT csv, HEADER match)
-- ... tutte le 13 tabelle in ordine di chiave esterna ...
\\copy ripartizione_mensile FROM '/csv/ripartizione_mensile.csv' WITH (FORMAT csv, HEADER match)

SELECT setval(pg_get_serial_sequence('segnalazione', 'id'), max(id)) FROM segnalazione;
SELECT setval(pg_get_serial_sequence('anomalia', 'id'), max(id)) FROM anomalia;`,
          note: '<strong>Nota:</strong> <code>utente</code> resta fuori dai CSV (password hashate dal backend via <code>npm run crea-utenti</code>). Per ricaricare da zero serve <code>docker compose down -v</code>.'
        }
      ]
    },

    backend: {
      title: 'Backend · Node 22 + Express 5 + pg',
      subtitle: 'Scheletro <strong>unito su main</strong> (PR #9 di <strong>Stefano (@stefanospadaccini-888)</strong>, merge <code>c0adefd</code>): Express <code>^5.3.0</code>, <code>pg ^8.23.1</code>, <code>jsonwebtoken ^9.0.3</code>, <code>bcryptjs ^3.0.3</code>, <strong>4 endpoint pronti</strong> e <strong>7 test</strong> verdi. In revisione la PR #28 di <strong>Geoffrey (@geoffreyagwasim)</strong> (<code>/api/verbali</code>); nello Sprint 1 anche area socio (<code>#14</code>) e segnalazioni LLM (<code>#16</code>).',
      badges: [
        { cls: 'fatto', text: 'PR #9 unita su main · 4 endpoint · 7/7 test verdi' },
        { cls: 'revisione', text: 'PR #28 in revisione (/api/verbali)' },
        { cls: 'sprint1', text: 'Sprint 1: #14, #16 (Stefano) · #25 (Geoffrey)' }
      ],
      links: [
        { label: 'PR #9 su GitHub ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/9' },
        { label: 'PR #28 (verbali) ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/28', secondary: true },
        { label: 'Flusso segnalazione + LLM →', internal: 'flusso_llm', secondary: true },
        { label: 'Issue #14 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/14', secondary: true },
        { label: 'Issue #16 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/16', secondary: true },
        { label: 'Issue #25 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/25', secondary: true }
      ],
      diagrams: [
        { id: 'backend', caption: 'Percorso di una richiesta dentro Express 5' }
      ],
      fatto: {
        title: 'Già fatto in quest\'area',
        items: [
          { date: '6 → 23 nov', who: 'Luca (@lufo-336)', what: 'Contratto API in <code>docs/api.md</code>: bozza del 6 nov (<code>29c89c6</code>), correzioni nella PR #2 (13 nov), congelato al SAL 1 nella PR #22 (21 endpoint su 6 aree e 3 ruoli)', ref: 'Storia di api.md', href: 'https://github.com/lufo-336/under-the-sun/commits/main/docs/api.md', stato: 'fatto' },
          { date: '23 nov', who: 'Stefano (@stefanospadaccini-888)', what: 'Scheletro Express 5 + <code>pg</code> + JWT HS256: 4 endpoint (<code>/api/salute</code>, <code>/api/auth/login</code>, <code>/api/auth/me</code>, <code>/api/impianti</code>), script <code>crea-utenti</code> e 7 test con <code>node:test</code> + <code>supertest</code>', ref: 'PR #9', href: 'https://github.com/lufo-336/under-the-sun/pull/9', stato: 'fatto' },
          { date: '23 nov', who: 'Luca (@lufo-336)', what: 'Approvazione PR #9 (verificati 7/7 test, build su Podman Fedora, <code>crea-utenti</code> e 200/403) e merge su <code>main</code> (<code>c0adefd</code>)', ref: 'PR #9', href: 'https://github.com/lufo-336/under-the-sun/pull/9', stato: 'fatto' },
          { date: '25 nov', who: 'Geoffrey (@geoffreyagwasim)', what: 'Endpoint <code>GET /api/verbali</code> e <code>GET /api/verbali/:id</code> per ruolo <code>admin</code> con test su branch <code>backend/verbali</code> (<code>971541a</code>, PR aperta in revisione)', ref: 'PR #28', href: 'https://github.com/lufo-336/under-the-sun/pull/28', stato: 'revisione' },
          { date: 'Sprint 1', who: 'Stefano (@stefanospadaccini-888)', what: 'Endpoint area socio <code>GET /api/me/riepilogo</code> e <code>GET /api/me/consumi</code> (US-02)', ref: 'Issue #14', href: 'https://github.com/lufo-336/under-the-sun/issues/14', stato: 'sprint1' },
          { date: 'Sprint 1', who: 'Stefano (@stefanospadaccini-888)', what: 'Endpoint segnalazioni socio <code>GET</code> / <code>POST /api/me/segnalazioni</code> con chiamata LLM e fallback <code>201</code> (US-05)', ref: 'Issue #16', href: 'https://github.com/lufo-336/under-the-sun/issues/16', stato: 'sprint1' }
        ]
      },
      table: {
        title: 'Endpoint di docs/api.md (21 + /api/salute) · stato di avanzamento',
        headers: ['Stato', 'Endpoint', 'Ruoli ammessi', 'Responsabile / rif.'],
        rows: [
          ['<span class="badge fatto">Su main</span>', '<code>GET /api/salute</code>', 'pubblico', 'Stefano (@stefanospadaccini-888) · PR #9 (healthcheck DB)'],
          ['<span class="badge fatto">Su main</span>', '<code>POST /api/auth/login</code> · <code>GET /api/auth/me</code>', 'pubblico / tutti i loggati', 'Stefano (@stefanospadaccini-888) · PR #9'],
          ['<span class="badge fatto">Su main</span>', '<code>GET /api/impianti</code>', 'operatore, admin', 'Stefano (@stefanospadaccini-888) · PR #9 (403 al socio)'],
          ['<span class="badge revisione">In revisione</span>', '<code>GET /api/verbali</code> · <code>GET /api/verbali/:id</code>', 'admin', 'Geoffrey (@geoffreyagwasim) · Issue #25 · PR #28 (US-14)'],
          ['<span class="badge sprint1">Sprint 1</span>', '<code>GET /api/me/riepilogo</code> · <code>GET /api/me/consumi</code>', 'socio', 'Stefano (@stefanospadaccini-888) · Issue #14 (US-02)'],
          ['<span class="badge sprint1">Sprint 1</span>', '<code>GET</code> / <code>POST /api/me/segnalazioni</code>', 'socio', 'Stefano (@stefanospadaccini-888) · Issue #16 (US-05 + LLM)'],
          ['<span class="badge sprint2">Sprint 2</span>', '<code>POST /api/me/simulazione</code>', 'socio', 'Stefano (@stefanospadaccini-888) · US-04'],
          ['<span class="badge sprint2">Sprint 2</span>', '<code>GET /api/impianti/:id</code> · <code>/api/impianti/:id/produzione</code> · <code>GET</code> / <code>PATCH /api/anomalie</code>', 'operatore, admin', 'Stefano (@stefanospadaccini-888) · US-06, US-07'],
          ['<span class="badge sprint2">Sprint 2</span>', '<code>GET</code> / <code>PATCH /api/segnalazioni</code> · <code>GET /api/comunita/kpi</code> · <code>/api/comunita/energia</code>', 'operatore, admin', 'Stefano (@stefanospadaccini-888) · US-08, US-09'],
          ['<span class="badge sprint2">Sprint 2</span>', '<code>GET /api/soci</code> · <code>GET /api/soci/:id/riepilogo</code>', 'admin', 'Stefano (@stefanospadaccini-888) · /api/soci']
        ]
      },
      choices: [
        {
          title: 'Dependency injection per test istantanei',
          body: '<code>creaApp({ db, config })</code> riceve pool e config dall\'esterno: <code>server.js</code> passa Postgres, i test un DB finto in memoria.',
          why: '<code>npm test</code> (7 test in <code>backend/test/api.test.js</code> con <code>node:test</code> + <code>supertest ^7.3.2</code>) gira in meno di un secondo anche senza database acceso.'
        },
        {
          title: 'Login anti-enumerazione e JWT HS256',
          body: 'Email inesistente e password sbagliata danno lo stesso <code>401 CREDENZIALI_ERRATE</code> e confrontano comunque contro un <code>HASH_FITTIZIO</code> bcrypt. Algoritmo JWT fissato a <code>HS256</code> (scadenza default <code>8h</code>).',
          why: 'Risposte e tempi uniformi non rivelano quali email sono registrate; niente algoritmi JWT inattesi.'
        },
        {
          title: 'Numeri JSON veri e container non-root',
          body: '<code>pg.types.setTypeParser(NUMERIC, Number)</code> converte gli euro in numeri reali; Dockerfile <code>node:22-alpine</code> con <code>USER node</code> e shutdown pulito su <code>SIGTERM</code>/<code>SIGINT</code>.',
          why: 'Risposte conformi a <code>docs/api.md</code>, immagine snella e meno superficie d\'attacco.'
        }
      ],
      codeBlocks: [
        {
          file: 'backend/src/auth.js · verifica JWT HS256 e ruoli',
          lang: 'js',
          code: `export function autentica(config) {
  return (req, res, next) => {
    const [schema, token] = (req.get('authorization') ?? '').split(' ');
    if (schema !== 'Bearer' || !token) return next(nonAutenticato());
    try {
      const dati = jwt.verify(token, config.jwtSegreto, { algorithms: ['HS256'] });
      req.utente = { id: Number(dati.sub), ruolo: dati.ruolo, socio_id: dati.socio_id ?? null };
      next();
    } catch {
      next(nonAutenticato('Token non valido o scaduto'));
    }
  };
}

export function richiediRuolo(...ruoli) {
  return (req, res, next) => {
    if (!ruoli.includes(req.utente?.ruolo)) return next(vietato());
    next();
  };
}`,
          note: '<strong>Nota:</strong> tutte le rotte di <code>/api/me/*</code> (Sprint 1) leggono <code>req.utente.socio_id</code> da qui, mai da un parametro del client.'
        },
        {
          file: 'backend/src/routes/impianti.js · modello per i nuovi endpoint (anche #25)',
          lang: 'js',
          code: `router.use(autentica(config), richiediRuolo('operatore', 'admin'));

router.get('/', async (req, res) => {
  const { rows } = await db.query(\`
    SELECT i.id, i.nome, i.comune, i.lat, i.lon, i.kwp,
           to_char(i.data_attivazione, 'YYYY-MM-DD') AS data_attivazione,
           count(a.id)::int AS anomalie_aperte
    FROM impianto i
    LEFT JOIN anomalia a ON a.impianto_id = i.id AND a.stato = 'aperta'
    GROUP BY i.id
    ORDER BY i.id\`);
  res.json(rows);
});`,
          note: '<strong>Nota:</strong> <code>to_char</code> formatta la data esattamente in <code>YYYY-MM-DD</code> e <code>::int</code> evita che il conteggio arrivi come stringa.'
        }
      ]
    },

    flusso_llm: {
      title: 'Percorso di una segnalazione · LLM con fallback',
      subtitle: '<strong>Solo schema, campione manuale e contratto sono su main</strong>: in <code>backend/src/</code> nessuna rotta o chiamata LLM è ancora implementata. Il flusso descrive quanto deciso e documentato in <code>docs/architettura.md</code>, <code>docs/api.md</code> e <code>data/GUIDA-DATASET.md</code>; implementazione backend (<code>#16</code>), UI socio (<code>#17</code>) e prompt con testi (<code>#19</code>) nello Sprint 1.',
      badges: [
        { cls: 'fatto', text: 'Su main: tabella segnalazione, CHECK, campione (15 righe) e contratto API' },
        { cls: 'sprint1', text: 'Da implementare in Sprint 1: #16 (backend) · #17 (frontend) · #19 (prompt)' }
      ],
      links: [
        { label: 'Vai al Backend →', internal: 'backend', secondary: true },
        { label: 'Issue #16 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/16' },
        { label: 'Issue #17 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/17', secondary: true },
        { label: 'Issue #19 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/19', secondary: true }
      ],
      diagrams: [
        { id: 'flusso_llm', caption: 'Flusso progettato · caso normale vs LLM irraggiungibile (non ancora attivo su main)' }
      ],
      fatto: {
        title: 'Già fatto in quest\'area',
        items: [
          { date: '6 → 23 nov', who: 'Luca (@lufo-336)', what: 'Flusso documentato in <code>docs/architettura.md</code> e contratto <code>POST /api/me/segnalazioni</code> / <code>PATCH /api/segnalazioni/:id</code> fissato in <code>docs/api.md</code>', ref: 'PR #2', href: 'https://github.com/lufo-336/under-the-sun/pull/2', stato: 'fatto' },
          { date: '16 → 23 nov', who: 'Luca (@lufo-336)', what: 'Tabella <code>segnalazione</code> su PostgreSQL con colonne <code>*_llm</code> immutabili e <code>CHECK</code> su 3 canali, 6 categorie, 3 urgenze e 3 stati (<code>NULL</code> ammessi in fallback)', ref: 'PR #6', href: 'https://github.com/lufo-336/under-the-sun/pull/6', stato: 'fatto' },
          { date: '19 → 23 nov', who: 'Francesco (@francescocolohan)', what: '15 segnalazioni nel campione giugno 2026 (<code>data/esempi/segnalazione.csv</code>) con colonne <code>*_llm</code> compilate a mano e correzioni simulate', ref: 'PR #8', href: 'https://github.com/lufo-336/under-the-sun/pull/8', stato: 'fatto' },
          { date: 'Sprint 1', who: 'Stefano (@stefanospadaccini-888)', what: 'Implementazione backend <code>GET</code> / <code>POST /api/me/segnalazioni</code> con chiamata LLM, provider finto per test e fallback <code>201</code>', ref: 'Issue #16', href: 'https://github.com/lufo-336/under-the-sun/issues/16', stato: 'sprint1' },
          { date: 'Sprint 1', who: 'Mirko (@mirkodivincenzo)', what: 'Pagina socio per invio e storico segnalazioni collegata al backend (US-05)', ref: 'Issue #17', href: 'https://github.com/lufo-336/under-the-sun/issues/17', stato: 'sprint1' },
          { date: 'Sprint 1', who: 'Francesco (@francescocolohan)', what: '200–300 segnalazioni etichettate (<code>segnalazione_etichette.csv</code>) e prompt definitivo LLM', ref: 'Issue #19', href: 'https://github.com/lufo-336/under-the-sun/issues/19', stato: 'sprint1' },
          { date: 'Sprint 2', who: 'Stefano (@stefanospadaccini-888) · Team dati', what: 'Coda operatore (<code>GET</code> / <code>PATCH /api/segnalazioni</code>) e misura dell\'accuratezza LLM (US-08, US-12)', ref: 'Piano v0.2', href: 'https://github.com/lufo-336/under-the-sun/blob/main/docs/piano-di-progetto.md', stato: 'sprint2' }
        ]
      },
      choices: [
        {
          title: 'Canali, categorie e urgenze già fissati nei CHECK SQL',
          body: 'Canali: <code>email</code>, <code>portale</code>, <code>interno</code> (con <code>socio_id = NULL</code>). 6 categorie: <code>guasto_impianto</code>, <code>bolletta_pagamenti</code>, <code>incentivi_ripartizione</code>, <code>adesione_recesso</code>, <code>informazioni</code>, <code>reclamo</code>. 3 urgenze: <code>alta</code>, <code>media</code>, <code>bassa</code>.',
          why: 'Lo schema PostgreSQL rifiuta qualsiasi etichetta fuori contratto prima ancora che entrino in coda.'
        },
        {
          title: 'Segnalazione dal portale e impianto opzionale',
          body: 'Il socio invia testo libero (<code>POST /api/me/segnalazioni</code> con <code>canale = \'portale\'</code> e <code>impianto_id</code> opzionale/<code>null</code>). Nello schema SQL esiste anche <code>impianto_id_llm</code> (segnato da confermare in <code>GUIDA-DATASET.md</code>).',
          why: 'Il socio non deve conoscere i nomi tecnici degli impianti; eventuali estrazioni dell\'LLM restano verificabili dall\'operatore.'
        },
        {
          title: 'Mai perdere una segnalazione (fallback 201)',
          body: 'In caso di timeout, errore o quota esaurita del piano gratuito, il salvataggio deve riuscire comunque con <code>categoria</code>, <code>urgenza</code> e <code>impianto_id</code> a <code>NULL</code> (i <code>CHECK</code> SQL li accettano).',
          why: 'Un servizio gratuito può mancare anche durante la demo: il flusso del socio non si blocca mai.'
        },
        {
          title: 'Piano gratuito, chiave nel backend e accuratezza (US-12)',
          body: 'Per la futura implementazione (#16) è previsto l\'uso di un piano gratuito con chiave solo nel <code>.env</code> del backend e un provider finto per sviluppo/demo. Le colonne <code>*_llm</code> restano immutate mentre l\'operatore aggiorna solo i campi in uso.',
          why: 'Nessun segreto nel browser e confronto diretto in SQL tra etichetta proposta dall\'LLM e correzione dell\'operatore.'
        }
      ],
      codeBlocks: [
        {
          file: 'docs/api.md · contratto POST /api/me/segnalazioni (da implementare in #16)',
          lang: 'json',
          code: `// Richiesta (dal socio: solo testo)
{ "testo": "Da ieri l'app non mostra più i consumi di marzo", "impianto_id": null }

// Risposta 201 Created (se l'LLM non risponde: categoria e urgenza sono null)
{
  "id": 318,
  "ts": "2026-11-06T15:02:11Z",
  "canale": "portale",
  "testo": "Da ieri l'app non mostra più i consumi di marzo",
  "categoria": "informazioni",
  "urgenza": "bassa",
  "stato": "aperta",
  "impianto_id": null
}`,
          note: '<strong>Nota:</strong> al socio non vengono mai esposti i campi <code>*_llm</code>, visibili solo a operatore e admin (<code>GET /api/segnalazioni</code>).'
        }
      ]
    },

    frontend: {
      title: 'Frontend · React + Vite + Tailwind + Recharts',
      subtitle: 'La cartella <code>frontend/</code> <strong>non è ancora su <code>main</code></strong>: tutto il codice vive nella <strong>PR #23 aperta (in revisione)</strong> di <strong>Mirko (@mirkodivincenzo)</strong> su branch <code>frontend/login-jwt</code> (+4059 righe in 34 file, chiude #12 e #13). Raccoglie il setup iniziale, il wireframe delle 8 viste e il restyling delle PR #4, #5 e #7 (chiuse perché inglobate in #23) insieme a login JWT, <code>AuthContext</code>, <code>ProtectedRoute</code>, <code>UserBar</code> e proxy <code>/api</code>.',
      badges: [
        { cls: 'revisione', text: 'In PR #23 (in revisione, non ancora su main)' },
        { cls: 'revisione', text: '34 file · 8 viste per ruolo · chiude #12 e #13' },
        { cls: 'sprint2', text: 'PR #4, #5, #7 chiuse (inglobate in #23)' },
        { cls: 'sprint1', text: 'Sprint 1: #15 (dashboard) · #17 (segnalazioni) · #20 (Compose/QA)' }
      ],
      links: [
        { label: 'PR #23 (in revisione) ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/23' },
        { label: 'PR #4 (chiusa) ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/4', secondary: true },
        { label: 'PR #5 (chiusa) ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/5', secondary: true },
        { label: 'PR #7 (chiusa) ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/7', secondary: true },
        { label: 'Issue #15 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/15', secondary: true },
        { label: 'Issue #17 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/17', secondary: true }
      ],
      diagrams: [
        { id: 'frontend', caption: 'Struttura dell\'app React (in PR #23, non ancora su main)' }
      ],
      fatto: {
        title: 'Già fatto in quest\'area',
        items: [
          { date: '15 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Setup iniziale React + Vite con Router e Recharts (<code>6710a4c</code>, 16 file); PR chiusa il 23 nov perché inglobata in #23', ref: 'PR #4', href: 'https://github.com/lufo-336/under-the-sun/pull/4', stato: 'sprint2' },
          { date: '15 → 23 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Bozza wireframe delle 8 viste per ruolo e allineamento mock al contratto API (29 file); PR chiusa il 24 nov perché confluita in #23', ref: 'PR #5', href: 'https://github.com/lufo-336/under-the-sun/pull/5', stato: 'sprint2' },
          { date: '17 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Restyling UI responsive con Tailwind (<code>3cbe968</code>, 33 file); PR chiusa il 23 nov perché integrata in #5 e #23', ref: 'PR #7', href: 'https://github.com/lufo-336/under-the-sun/pull/7', stato: 'sprint2' },
          { date: '23 → 24 nov', who: 'Mirko (@mirkodivincenzo)', what: 'PR aperta (<strong>non ancora su <code>main</code></strong>): login JWT reale, <code>AuthContext</code>, <code>ProtectedRoute</code>, <code>UserBar</code>, <code>authService</code>, <code>apiClient</code> con proxy <code>/api</code> e logout (34 file, chiude #12 e #13)', ref: 'PR #23', href: 'https://github.com/lufo-336/under-the-sun/pull/23', stato: 'revisione' },
          { date: 'Sprint 1', who: 'Mirko (@mirkodivincenzo)', what: 'Dashboard socio collegata alle API reali (<code>/api/me/riepilogo</code> e <code>/api/me/consumi</code>, US-02)', ref: 'Issue #15', href: 'https://github.com/lufo-336/under-the-sun/issues/15', stato: 'sprint1' },
          { date: 'Sprint 1', who: 'Mirko (@mirkodivincenzo)', what: 'Invio e storico segnalazioni socio collegati al backend (US-05)', ref: 'Issue #17', href: 'https://github.com/lufo-336/under-the-sun/issues/17', stato: 'sprint1' },
          { date: 'Sprint 1', who: 'Geoffrey (@geoffreyagwasim)', what: 'Prova pratica della PR #23 e aggiunta del servizio <code>frontend</code> in <code>compose.yaml</code>', ref: 'Issue #20', href: 'https://github.com/lufo-336/under-the-sun/issues/20', stato: 'sprint1' }
        ]
      },
      choices: [
        {
          title: 'Le 8 viste per ruolo (nella PR #23)',
          body: '<code>LoginPage</code>; area socio (<code>SocioDashboardPage</code>, <code>SocioSimulatorePage</code>, <code>SocioSegnalazioniPage</code>); area operatore (<code>OperatoreImpiantiPage</code>, <code>OperatoreSegnalazioniPage</code>); area admin (<code>AdminKpiPage</code>, <code>AdminAssembleePage</code>), più <code>AppLayout</code>, <code>SidebarNav</code>, <code>KpiCard</code>, <code>Panel</code>, <code>StatusBadge</code> e <code>UrgencyBadge</code>.',
          why: 'Copre tutte le storie del piano; dopo il merge di #23 si sostituiscono i mock pagina per pagina.'
        },
        {
          title: 'Proxy Vite /api e auth centralizzata (nella PR #23)',
          body: 'In <code>vite.config.js</code> le chiamate <code>/api</code> passano dal proxy Vite; <code>apiClient.js</code> e <code>authService.js</code> gestiscono token <code>Bearer</code> e errori <code>{ errore: { codice, messaggio } }</code> con <code>AuthContext</code> e <code>ProtectedRoute</code>.',
          why: 'Zero problemi CORS in sviluppo e gestione uniforme di sessione, logout e 401.'
        },
        {
          title: 'Mock allineati al contratto e ora italiana a schermo',
          body: '<code>mockData.js</code> usa ID numerici, <code>score</code> 0–1 e le 6 categorie del data dictionary; <code>formatters.js</code> converte le date UTC in ora italiana (<code>Europe/Rome</code>).',
          why: 'Nello Sprint 1 passare dai mock alle API vere non richiede di riscrivere i componenti.'
        }
      ],
      codeBlocks: [
        {
          file: 'frontend/src/services/apiClient.js · in PR #23 (non ancora su main)',
          lang: 'js',
          code: `const accessToken = token || localStorage.getItem('under_the_sun_token')
if (accessToken) {
  config.headers.Authorization = \`Bearer \${accessToken}\`
}
const response = await fetch(\`\${API_BASE_URL}\${endpoint}\`, config)
if (!response.ok) {
  const errore = data?.errore
  if (response.status === 401) window.dispatchEvent(new CustomEvent('auth:unauthorized'))
  throw new ApiError(errore?.codice || 'ERRORE_API', errore?.messaggio || 'Errore API', response.status)
}`,
          note: '<strong>Nota:</strong> estratto da PR #23; intercetta il formato JSON ufficiale del backend e notifica <code>AuthContext</code> in caso di token scaduto (401).'
        },
        {
          file: 'frontend/src/components/ProtectedRoute.jsx · in PR #23 (non ancora su main)',
          lang: 'jsx',
          code: `export default function ProtectedRoute({ allowedRole, children }) {
  const { isAuthenticated, loading, user } = useAuth()
  if (loading) return <div>Caricamento…</div>
  if (!isAuthenticated) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  if (allowedRole && user.ruolo !== allowedRole) {
    return <Navigate to={roleHomes[user.ruolo] || '/login'} replace />
  }
  return children
}`,
          note: '<strong>Nota:</strong> estratto da PR #23; protegge la navigazione lato UI mentre la sicurezza effettiva resta garantita lato server dal backend (403).'
        }
      ]
    },

    dati: {
      title: 'Pipeline dati · Python (pandas 3.1.1, numpy 2.5.5)',
      subtitle: 'Generatore e <strong>123 controlli automatici</strong> uniti su <code>main</code> (<strong>PR #8</strong> di <strong>Francesco (@francescocolohan)</strong> con <strong>Giuseppe (@ASTROBLAST25)</strong> e <strong>Cecilia (@ceciliamontebello)</strong>): campione di giugno 2026 con <strong>15 CSV</strong> in <code>data/esempi/</code> (13 per il DB + 2 file di lavoro) e seed fisso <code>42</code>. Nello Sprint 1: dataset completo 2 anni (<code>#18</code>) e 200–300 segnalazioni + modelli (<code>#19</code>).',
      badges: [
        { cls: 'fatto', text: 'PR #8 unita su main · 15 CSV · 123/123 controlli' },
        { cls: 'fatto', text: 'Seed fisso 42 · Python >= 3.11' },
        { cls: 'sprint2', text: 'PR #24 proposta DB aperta (non su main)' },
        { cls: 'sprint1', text: 'Sprint 1: #18 (2 anni) · #19 (segnalazioni + modelli)' }
      ],
      links: [
        { label: 'PR #8 su GitHub ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/8' },
        { label: 'PR #24 (proposta DB) ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/24', secondary: true },
        { label: 'Issue #18 (2 anni) ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/18', secondary: true },
        { label: 'Issue #19 (testi e modelli) ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/19', secondary: true }
      ],
      diagrams: [
        { id: 'dati', caption: 'genera.py · dai dati reali ai CSV validati e ai batch offline' }
      ],
      fatto: {
        title: 'Già fatto in quest\'area',
        items: [
          { date: '13 nov', who: 'Luca (@lufo-336)', what: 'Brief iniziale del team dati allineato ai ruoli del piano (<code>docs/team-dati.md</code>)', ref: 'PR #3', href: 'https://github.com/lufo-336/under-the-sun/pull/3', stato: 'fatto' },
          { date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Guida al dataset v1.1 → v1.3, data dictionary v1, struttura pipeline Python e intestazioni CSV con seed <code>42</code> (<code>44ab791</code>, <code>6080a00</code>, <code>58c545a</code>, <code>e9f662e</code>)', ref: 'PR #8', href: 'https://github.com/lufo-336/under-the-sun/pull/8', stato: 'fatto' },
          { date: '19 nov', who: 'Francesco (@francescocolohan)', what: '15 segnalazioni, anagrafiche, meteo Open-Meteo, produzione, consumi provvisori e bolletta del campione giugno 2026 (<code>b63bb2b</code> → <code>93c43b4</code>)', ref: 'PR #8', href: 'https://github.com/lufo-336/under-the-sun/pull/8', stato: 'fatto' },
          { date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Guida v1.8, verbale del 9 luglio 2026 (id 7), <code>controlli.py</code> (123 controlli) e grafici in <code>data/notebook/</code> (<code>70c4e29</code>)', ref: 'PR #8', href: 'https://github.com/lufo-336/under-the-sun/pull/8', stato: 'fatto' },
          { date: '20 → 23 nov', who: 'Mirko (@mirkodivincenzo) · Luca (@lufo-336)', what: 'Approvazioni PR #8 (20 e 23 nov) e merge su <code>main</code> (<code>e0d80d0</code>): 13 dei 15 CSV di <code>data/esempi/</code> caricati in Postgres (gli altri 2 sono file di lavoro)', ref: 'PR #8', href: 'https://github.com/lufo-336/under-the-sun/pull/8', stato: 'fatto' },
          { date: '23 nov', who: 'Giuseppe (@ASTROBLAST25)', what: 'Proposta aperta di seconda migrazione relazionale del DB (tabelle di riferimento, storico, trigger, indici e prove SQL/Python)', ref: 'PR #24', href: 'https://github.com/lufo-336/under-the-sun/pull/24', stato: 'sprint2' },
          { date: 'Sprint 1', who: 'Francesco (@francescocolohan)', what: 'Dataset completo di 2 anni (8 impianti, 240 soci, 17.520 ore, taratura PVGIS e profili ARERA) in <code>data/output/</code>', ref: 'Issue #18', href: 'https://github.com/lufo-336/under-the-sun/issues/18', stato: 'sprint1' },
          { date: 'Sprint 1', who: 'Francesco (@francescocolohan)', what: '200–300 segnalazioni etichettate, prompt LLM, primi modelli e formule CER/simulatore', ref: 'Issue #19', href: 'https://github.com/lufo-336/under-the-sun/issues/19', stato: 'sprint1' }
        ]
      },
      table: {
        title: 'Le due configurazioni di genera.py (config.py)',
        headers: ['Voce', 'piccola · campione SAL 1 (su main)', 'completa · dataset SAL 2 (#18)'],
        rows: [
          ['Periodo', 'giugno 2026 · 720 ore', 'nov 2024 → ott 2026 · 17.520 ore (730 giorni)'],
          ['Impianti / Soci', '3 impianti (id 1–3) · 20 soci (14 famiglie, 4 imprese, 2 enti)', '8 impianti (950 kWp) · 240 soci (200 famiglie, 30 imprese, 10 enti)'],
          ['Volumi consumi', 'provvisori (2.700 / 15.000 / 40.000 kWh/anno)', 'profili mensili ARERA (Torino 2025)'],
          ['Resa PVGIS', '<code>k_impianto = 1</code> (senza taratura)', 'tarata su PVGIS 5.3 (2023)'],
          ['Anomalie', 'guasto fisso del 1° giugno 11–15 UTC (impianto 3)', 'guasto fisso + <code>guasto</code>, <code>stringa</code>, <code>sporcizia</code>, <code>neve</code>'],
          ['Cartella e file', '<code>data/esempi/</code> (15 CSV nel repo)', '<code>data/output/</code> (esclusa da Git) + <code>segnalazione_etichette.csv</code>']
        ]
      },
      choices: [
        {
          title: 'Seed dedicato per ogni entità',
          body: '<code>default_rng([42, 0, impianto_id])</code>, <code>default_rng([42, 1, socio_id])</code> e <code>default_rng([42, 2])</code> per l\'anagrafica: ogni impianto e socio ha il suo generatore (Faker <code>40.54.0</code> con seed 42).',
          why: 'Passare da 3 a 8 impianti o da 20 a 240 soci non altera i numeri dei primi elementi: campione e dataset completo restano coerenti.'
        },
        {
          title: 'Storia coerente per la demo',
          body: 'Il 1° giugno 2026 l\'impianto <em>Tetto scuola Pinerolo</em> si ferma (11:00–15:00 UTC, 442 kWh persi): anomalia, segnalazioni e verbale del 9 luglio 2026 coincidono.',
          why: 'Verificato automaticamente da <code>controlli.py</code> (123 controlli su formato, serie orarie, integrità, resa PVGIS, coerenza verbale e riproducibilità bit a bit).'
        },
        {
          title: 'Energia condivisa ora per ora (regola GSE)',
          body: 'Ogni ora <code>condivisa = min(immessa, prelevata)</code>, ripartita tra i soci attivi (<code>ts >= data_adesione</code>) in proporzione ai loro prelievi in quell\'ora; tariffa premio <code>0,130 €/kWh</code> + valorizzazione ARERA <code>0,008 €/kWh</code> e CO2 ISPRA <code>0,4133 kg/kWh</code>.',
          why: 'Chi sposta i consumi nelle ore di sole riceve più incentivo, dando base reale al simulatore.'
        }
      ],
      codeBlocks: [
        {
          file: 'data/generazione/genera.py · scrivi_csv (metà Python del contratto)',
          lang: 'python',
          code: `def scrivi_csv(df: pd.DataFrame, nome: str, cartella: Path) -> Path:
    """UTF-8 senza BOM, fine riga \\n su ogni OS, colonne identiche a Postgres."""
    attese = config.COLONNE[nome]
    if list(df.columns) != attese:
        raise ValueError(f"{nome}: colonne {list(df.columns)}, attese {attese}")
    cartella.mkdir(parents=True, exist_ok=True)
    percorso = cartella / f"{nome}.csv"
    df.to_csv(percorso, index=False, encoding="utf-8", lineterminator="\\n", na_rep="")
    return percorso`,
          note: '<strong>Nota:</strong> con <code>lineterminator="\\n"</code> e <code>data/.gitattributes</code> (<code>*.csv text eol=lf</code>) lo stesso CSV ha identico hash su Windows, macOS e Linux, e rispetta al 100% <code>HEADER match</code>.'
        },
        {
          file: 'data/generazione/config.py · seed per entità',
          lang: 'python',
          code: `SEED = 42

def rng_impianto(impianto_id: int) -> np.random.Generator:
    return np.random.default_rng([SEED, 0, impianto_id])

def rng_socio(socio_id: int) -> np.random.Generator:
    return np.random.default_rng([SEED, 1, socio_id])`,
          note: '<strong>Nota:</strong> con le versioni fissate in <code>data/requirements.txt</code>, due rilanci producono file identici bit per bit (verificato da <code>controlli.py</code>).'
        }
      ]
    },

    devops: {
      title: 'CI, DevOps e processo Git',
      subtitle: 'Su <code>main</code> ci sono <code>compose.yaml</code> (4 servizi: <code>db</code> Postgres 17, <code>migrate</code> dbmate, <code>seed</code>, <code>backend</code> Node 22 da PR #6 e #9), la mappa D2 (PR #21, #22, #26) e il deploy su GitHub Pages (<strong>PR #27</strong>, <code>.github/workflows/pages.yml</code>). Il workflow CI (<code>.github/workflows/ci.yml</code>, 3 job) è aperto nella <strong>PR #10 (in revisione, non ancora su <code>main</code>)</strong>.',
      badges: [
        { cls: 'fatto', text: 'Compose (4 servizi) e GitHub Pages (PR #27) su main' },
        { cls: 'revisione', text: 'PR #10 (CI) in revisione · 3/3 check verdi · non ancora su main' },
        { cls: 'sprint1', text: 'Sprint 1: #11 (check obbligatori) · #20 (QA + frontend Compose)' }
      ],
      links: [
        { label: 'PR #10 (CI, aperta) ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/10' },
        { label: 'PR #27 (Pages, su main) ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/27', secondary: true },
        { label: 'Mappa live su Pages ↗', href: 'https://lufo-336.github.io/under-the-sun/', secondary: true },
        { label: 'Issue #11 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/11', secondary: true },
        { label: 'Issue #20 (Geoffrey) ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/20', secondary: true }
      ],
      diagrams: [
        { id: 'devops', caption: 'Giro di una modifica e stato dei merge di fondazione' }
      ],
      fatto: {
        title: 'Già fatto in quest\'area',
        items: [
          { date: '16 → 23 nov', who: 'Luca (@lufo-336)', what: '<code>compose.yaml</code> con PostgreSQL 17, <code>migrate</code> (<code>dbmate:2.38.1</code>) e <code>seed</code> (profilo <code>strumenti</code>, 13 CSV in transazione)', ref: 'PR #6', href: 'https://github.com/lufo-336/under-the-sun/pull/6', stato: 'fatto' },
          { date: '23 nov', who: 'Stefano (@stefanospadaccini-888)', what: 'Servizio <code>backend</code> in <code>compose.yaml</code> con <code>Dockerfile</code> <code>node:22-alpine</code> e healthcheck <code>/api/salute</code>', ref: 'PR #9', href: 'https://github.com/lufo-336/under-the-sun/pull/9', stato: 'fatto' },
          { date: '23 nov', who: 'Luca (@lufo-336)', what: 'Mappa interattiva D2 (<code>docs/mappa/</code>, script <code>compila.sh</code>) pubblicata e aggiornata con storico GitHub e barra rapida', ref: 'PR #21 · #22 · #26', href: 'https://github.com/lufo-336/under-the-sun/pull/26', stato: 'fatto' },
          { date: '23 nov', who: 'Luca (@lufo-336)', what: 'Workflow <code>.github/workflows/pages.yml</code> unito su <code>main</code> (<code>ac7e13b</code>) per pubblicare la mappa D2 su GitHub Pages', ref: 'PR #27', href: 'https://github.com/lufo-336/under-the-sun/pull/27', stato: 'fatto' },
          { date: '23 nov', who: 'Luca (@lufo-336)', what: 'Workflow <code>.github/workflows/ci.yml</code> (3 job: backend, frontend, Compose + seed, +126 righe) in <strong>PR aperta, non ancora su <code>main</code></strong>', ref: 'PR #10', href: 'https://github.com/lufo-336/under-the-sun/pull/10', stato: 'revisione' },
          { date: 'Sprint 1', who: 'Luca (@lufo-336)', what: 'Chiusura dei merge di base e attivazione dei check CI obbligatori su <code>main</code>', ref: 'Issue #11', href: 'https://github.com/lufo-336/under-the-sun/issues/11', stato: 'sprint1' },
          { date: 'Sprint 1', who: 'Geoffrey (@geoffreyagwasim)', what: 'Review PR #10 (CI), prova pratica PR #23 e aggiunta del servizio <code>frontend</code> in <code>compose.yaml</code>', ref: 'Issue #20', href: 'https://github.com/lufo-336/under-the-sun/issues/20', stato: 'sprint1' }
        ]
      },
      table: {
        title: 'Workflow CI (in PR #10, non ancora su main) e deploy GitHub Pages (su main)',
        headers: ['Job / Workflow', 'Cosa verifica / esegue', 'Stato e nota tecnica'],
        rows: [
          ['<strong>Pubblica mappa D2</strong> (<code>pages.yml</code>)', 'Deploy di <code>docs/mappa/out/index/</code> su <code>lufo-336.github.io/under-the-sun/</code>', '<span class="badge fatto">Su main</span> · PR #27 (<code>actions/deploy-pages@v4</code>)'],
          ['<strong>Backend (test)</strong> (<code>ci.yml</code>)', 'Node 22 · <code>npm ci</code> · lint · <code>npm test</code> (7 test)', '<span class="badge revisione">In PR #10</span> · salta pulitamente se <code>backend/</code> manca'],
          ['<strong>Frontend (lint e build)</strong> (<code>ci.yml</code>)', 'Node 22 · <code>npm ci</code> · <code>oxlint</code> · <code>vite build</code>', '<span class="badge revisione">In PR #10</span> · intercetta lockfile rotti e import case-sensitive'],
          ['<strong>Database, seed e Compose</strong> (<code>ci.yml</code>)', '<code>up --build --wait backend</code> · <code>seed</code> 13 CSV · <code>crea-utenti</code> · <code>curl /api/salute</code>', '<span class="badge revisione">In PR #10</span> · verifica contratto schema ↔ CSV; <code>down -v</code>']
        ]
      },
      choices: [
        {
          title: 'Compose a 4 servizi su main (frontend in #20)',
          body: '<code>compose.yaml</code> orchestra <code>db</code> (<code>postgres:17</code>), <code>migrate</code> (<code>dbmate:2.38.1</code>), <code>seed</code> (profilo <code>strumenti</code>) e <code>backend</code> (Node 22, porta <code>127.0.0.1:3000</code>). Il servizio <code>frontend</code> arriverà con la Issue #20.',
          why: 'Chiunque avvia DB e API con un solo comando; le porte su <code>127.0.0.1</code> evitano esposizioni involontarie in rete.'
        },
        {
          title: 'La CI prova il contratto dati, non solo la build',
          body: 'In PR #10 (non ancora su <code>main</code>), il job integrazione avvia Postgres 17, applica le migrazioni e carica i 13 CSV reali con <code>HEADER match</code>.',
          why: 'Se una PR rompe l\'allineamento tra schema SQL e CSV, il controllo fallisce prima del merge.'
        },
        {
          title: 'La CI non sostituisce la prova umana',
          body: '<code>ci.yml</code> usa <code>permissions: contents: read</code> e <code>concurrency</code>; <strong>Geoffrey (@geoffreyagwasim)</strong> esegue poi il giro manuale end-to-end (Issue #20) sulle PR.',
          why: 'I test automatici verificano build e contratto, la prova pratica verifica l\'interfaccia dal vivo.'
        }
      ],
      codeBlocks: [
        {
          file: '.github/workflows/ci.yml · estratto dalla PR #10 (non ancora su main)',
          lang: 'yaml',
          code: `- name: Avvia stack completo (database, migrazioni e backend)
  if: steps.presente.outputs.compose == 'true' && steps.presente.outputs.backend == 'true'
  run: docker compose up -d --build --wait backend

- name: Carica i CSV di esempio (controllo contratto schema <-> dati)
  if: steps.presente.outputs.compose == 'true' && steps.presente.outputs.csv == 'true'
  run: docker compose run --rm seed

- name: Crea account di prova e verifica /api/salute
  if: steps.presente.outputs.compose == 'true' && steps.presente.outputs.backend == 'true'
  run: |
    docker compose exec -T backend npm run crea-utenti
    curl --fail --silent --show-error --retry 5 --retry-delay 2 --retry-all-errors http://127.0.0.1:3000/api/salute`,
          note: '<strong>Nota:</strong> estratto da PR #10 (in revisione); si usa <code>--wait backend</code> (non <code>--wait</code> su tutto) perché <code>migrate</code> è un container one-shot che esce con 0.'
        }
      ]
    },

    sprint1: {
      title: 'Piano Sprint 1 · Primo percorso completo (23 nov → 4 dic)',
      subtitle: '<strong>Stato al 25 novembre 2026 · obiettivo SAL 2:</strong> un socio accede con login reale, vede la dashboard con dati veri dal DB e invia una segnalazione classificata dall\'LLM (US-01, US-02, US-05), mentre il team dati prepara i 2 anni completi e Geoffrey (@geoffreyagwasim) realizza l\'endpoint verbali (US-14, PR #28).',
      badges: [
        { cls: 'fatto', text: '#6, #8, #9 su main' },
        { cls: 'revisione', text: 'PR aperte: #10 CI, #23 login JWT, #28 verbali' },
        { cls: 'sprint1', text: '11 Issue aperte (#11–#20, #25)' },
        { cls: 'sprint2', text: 'Scadenza SAL 2: ven 4 dic' }
      ],
      links: [
        { label: 'Milestone Sprint 1 su GitHub ↗', href: 'https://github.com/lufo-336/under-the-sun/milestone/1' },
        { label: 'Storico GitHub →', internal: 'storico', secondary: true }
      ],
      diagrams: [
        { id: 'sprint1', caption: 'Grafo delle dipendenze delle 11 Issue (clicca un blocco per aprire la Issue su GitHub)' }
      ],
      table: {
        title: 'Stato delle 11 Issue al 25 nov',
        headers: ['Issue', 'Responsabile', 'PR collegata', 'Stato'],
        rows: [
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/11" target="_blank" rel="noopener">#11</a> · Merge di base (#6, #8, #9, #10) e check CI su main', 'Luca (@lufo-336)', '<a href="https://github.com/lufo-336/under-the-sun/pull/10" target="_blank" rel="noopener">PR #10</a> (in revisione)', '<span class="badge sprint1">Aperta</span>'],
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/12" target="_blank" rel="noopener">#12</a> · Riunire wireframe e restyling allineati al contratto API', 'Mirko (@mirkodivincenzo)', '<a href="https://github.com/lufo-336/under-the-sun/pull/23" target="_blank" rel="noopener">PR #23</a> (in revisione)', '<span class="badge revisione">Aperta · PR in revisione</span>'],
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/13" target="_blank" rel="noopener">#13</a> · [US-01] Frontend: login reale JWT e gestione errori', 'Mirko (@mirkodivincenzo)', '<a href="https://github.com/lufo-336/under-the-sun/pull/23" target="_blank" rel="noopener">PR #23</a> (in revisione)', '<span class="badge revisione">Aperta · PR in revisione</span>'],
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/14" target="_blank" rel="noopener">#14</a> · [US-02] Backend: endpoint area socio (riepilogo e consumi)', 'Stefano (@stefanospadaccini-888)', '—', '<span class="badge sprint1">Aperta</span>'],
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/15" target="_blank" rel="noopener">#15</a> · [US-02] Frontend: dashboard socio collegata alle API reali', 'Mirko (@mirkodivincenzo)', '—', '<span class="badge sprint1">Aperta</span>'],
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/16" target="_blank" rel="noopener">#16</a> · [US-05] Backend: segnalazioni socio con LLM e fallback', 'Stefano (@stefanospadaccini-888)', '—', '<span class="badge sprint1">Aperta</span>'],
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/17" target="_blank" rel="noopener">#17</a> · [US-05] Frontend: invio e storico segnalazioni socio', 'Mirko (@mirkodivincenzo)', '—', '<span class="badge sprint1">Aperta</span>'],
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/18" target="_blank" rel="noopener">#18</a> · [Dati] Dataset completo di 2 anni (seed fisso e compatibilità)', 'Francesco (@francescocolohan)', '—', '<span class="badge sprint1">Aperta</span>'],
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/19" target="_blank" rel="noopener">#19</a> · [Dati] 200-300 segnalazioni etichettate, prompt LLM e formule', 'Francesco (@francescocolohan)', '—', '<span class="badge sprint1">Aperta</span>'],
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/20" target="_blank" rel="noopener">#20</a> · [QA / DevOps] Review PR #10, prova PR #23 e frontend in Compose', 'Geoffrey (@geoffreyagwasim)', '—', '<span class="badge sprint1">Aperta</span>'],
          ['<a href="https://github.com/lufo-336/under-the-sun/issues/25" target="_blank" rel="noopener">#25</a> · [US-14] Backend: endpoint verbali assemblee', 'Geoffrey (@geoffreyagwasim)', '<a href="https://github.com/lufo-336/under-the-sun/pull/28" target="_blank" rel="noopener">PR #28</a> (in revisione)', '<span class="badge revisione">Aperta · PR in revisione</span>']
        ]
      },
      choicesTitle: 'Regole di lavoro dello Sprint 1',
      choices: [
        {
          title: 'Review entro 48 ore, zero conflitti',
          body: 'Chi apre una PR indica subito il revisore; una PR approvata si unisce lo stesso giorno, senza bypass.',
          why: 'Nello Sprint 0 il collo di bottiglia è stato far entrare il codice su <code>main</code>, non scriverlo.'
        },
        {
          title: 'Un responsabile chiaro per ogni Issue',
          body: 'Backend e frontend delle stesse storie sono separati (#14/#15, #16/#17), e Geoffrey (@geoffreyagwasim) ha compiti autonomi non bloccati (#20, #25).',
          why: 'Così nessuno lavora sugli stessi file di un altro né resta fermo senza sapere da dove partire.'
        },
        {
          title: 'Stato due volte a settimana + mini SAL 27 nov',
          body: 'Lunedì e giovedì 3 righe sul gruppo (<em>fatto · prossimo · bloccato</em>); ven 27 nov mini SAL col cliente con 3–4 domande precise.',
          why: 'Alimenta lo stato settimanale senza riunioni lunghe.'
        }
      ]
    },

    storico: {
      title: 'Storico del repository GitHub',
      subtitle: 'Linea temporale verticale di tutte le <strong>Pull Request</strong> di <code>lufo-336/under-the-sun</code> dal 6 al 25 novembre 2026: <strong>10 PR unite su main</strong>, <strong>4 aperte</strong>, <strong>3 chiuse senza merge</strong>.',
      badges: [
        { cls: 'fatto', text: '10 PR unite su main' },
        { cls: 'revisione', text: '3 PR in revisione (#10, #23, #28)' },
        { cls: 'sprint2', text: '1 proposta team dati (#24) · 3 chiuse (#4, #5, #7)' }
      ],
      links: [
        { label: 'Tutte le PR su GitHub ↗', href: 'https://github.com/lufo-336/under-the-sun/pulls?q=is%3Apr' },
        { label: 'Milestone Sprint 1 (#11–#20, #25) ↗', href: 'https://github.com/lufo-336/under-the-sun/milestone/1', secondary: true }
      ],
      isTimeline: true,
      timeline: [
        {
          id: 'pr28',
          order: 18,
          date: '25 nov',
          pr: 'PR #28',
          status: 'revisione',
          statusLabel: 'In revisione',
          category: 'aperta',
          author: 'Geoffrey (@geoffreyagwasim)',
          title: 'Aggiunge GET /api/verbali e /api/verbali/:id (US-14)',
          desc: 'Nuove rotte per i verbali delle assemblee e relativi test su branch backend/verbali (+75 righe in 3 file, collegata alla Issue #25).',
          files: [
            'backend/src/app.js',
            'backend/src/routes/verbali.js',
            'backend/test/api.test.js'
          ],
          commits: [
            { hash: '971541a', date: '25 nov', who: 'Geoffrey (@geoffreyagwasim)', what: 'Aggiunge GET /api/verbali e /api/verbali/:id (US-14)' }
          ],
          links: [
            { label: 'Apri PR #28 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/28' },
            { label: 'Issue #25 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/25', secondary: true }
          ]
        },
        {
          id: 'pr23',
          order: 17,
          date: '23 → 24 nov',
          pr: 'PR #23',
          status: 'revisione',
          statusLabel: 'In revisione',
          category: 'aperta',
          author: 'Mirko (@mirkodivincenzo)',
          title: 'Frontend: collegare login JWT e protezione ruoli (US-01)',
          desc: 'Include la base di #4, #5 e #7 più proxy /api, ApiError, AuthContext, ProtectedRoute e logout su branch frontend/login-jwt (+4059 righe in 34 file, chiude #12 e #13). Verifiche eseguite: npm ci, oxlint e vite build verdi.',
          files: [
            'frontend/src/App.jsx',
            'frontend/src/components/ProtectedRoute.jsx',
            'frontend/src/components/UserBar.jsx',
            'frontend/src/context/AuthContext.jsx',
            'frontend/src/services/apiClient.js',
            'frontend/src/services/authService.js'
          ],
          commits: [
            { hash: '6710a4c', date: '15 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Inizializza progetto React + Vite con Router e Recharts' },
            { hash: '32f346c', date: '15 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Bozza wireframe interattivo delle 8 viste per ruolo' },
            { hash: '9d83256', date: '16 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Allinea mock al contratto API e sistema feedback' },
            { hash: '71811fd', date: '16 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Allinea ID numerici grafico impianti e score anomalie' },
            { hash: '3cbe968', date: '17 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Applica nuova UI responsive con Tailwind' },
            { hash: 'd5c537e', date: '23 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Integra restyling frontend e allinea contratto API' },
            { hash: '74c0096', date: '23 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Collega login JWT e protezione ruoli' },
            { hash: '450364e', date: '24 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Allinea credenziali demo e aggiunge logout (US-01)' }
          ],
          links: [
            { label: 'Apri PR #23 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/23' },
            { label: 'Issue #12 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/12', secondary: true },
            { label: 'Issue #13 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/13', secondary: true }
          ]
        },
        {
          id: 'pr5',
          order: 16,
          date: '15 → 24 nov',
          pr: 'PR #5',
          status: 'sprint2',
          statusLabel: 'Chiusa (inglobata in #23)',
          category: 'chiusa',
          author: 'Mirko (@mirkodivincenzo)',
          title: 'Bozza wireframe interattivo delle 8 viste per ruolo',
          desc: 'Branch frontend/wireframe (+3796 righe in 29 file) con le 8 viste per ruolo e il restyling integrato. Tutti i commit sono confluiti nella PR #23; chiusa il 24 novembre senza merge.',
          files: [
            'frontend/src/App.jsx',
            'frontend/src/components/AppLayout.jsx',
            'frontend/src/pages/auth/LoginPage.jsx',
            'frontend/src/pages/socio/SocioDashboardPage.jsx',
            'frontend/src/services/apiClient.js',
            'frontend/src/mocks/mockData.js'
          ],
          commits: [
            { hash: '6710a4c', date: '15 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Inizializza progetto React + Vite con Router e Recharts' },
            { hash: '32f346c', date: '15 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Bozza wireframe interattivo delle 8 viste per ruolo' },
            { hash: '9d83256', date: '16 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Allinea mock al contratto API e sistema feedback' },
            { hash: '71811fd', date: '16 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Allinea ID numerici grafico impianti e score anomalie' },
            { hash: '3cbe968', date: '17 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Applica nuova UI responsive con Tailwind' },
            { hash: 'd5c537e', date: '23 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Integra restyling frontend e allinea contratto API' }
          ],
          links: [
            { label: 'Apri PR #5 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/5' }
          ]
        },
        {
          id: 'pr27',
          order: 15,
          date: '23 nov',
          pr: 'PR #27',
          status: 'fatto',
          statusLabel: 'Unita su main',
          category: 'unita',
          author: 'Luca (@lufo-336)',
          title: 'Pubblica la mappa D2 su GitHub Pages',
          desc: 'Workflow .github/workflows/pages.yml con deploy automatico di docs/mappa/out/index/ su lufo-336.github.io/under-the-sun/ e link online in README e docs (merge ac7e13b, +41/-2 in 4 file).',
          files: [
            '.github/workflows/pages.yml',
            'README.md',
            'docs/architettura.md',
            'docs/mappa/README.md'
          ],
          commits: [
            { hash: '3718fef', date: '23 nov', who: 'Luca (@lufo-336)', what: 'Pubblica la mappa architettura D2 su GitHub Pages e aggiunge i link' }
          ],
          links: [
            { label: 'Apri PR #27 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/27' },
            { label: 'Sito live ↗', href: 'https://lufo-336.github.io/under-the-sun/', secondary: true }
          ]
        },
        {
          id: 'pr26',
          order: 14,
          date: '23 nov',
          pr: 'PR #26',
          status: 'fatto',
          statusLabel: 'Unita su main',
          category: 'unita',
          author: 'Luca (@lufo-336)',
          title: 'Piano Sprint 1 e mappa D2: compiti Geoffrey (#20, #25) e barra accesso rapido',
          desc: 'Assegnati a Geoffrey (@geoffreyagwasim) i compiti sulle Issue #20 e #25 e aggiunta barra 2×4 in cima a index.svg (merge 9396126, +563/-403 in 10 file).',
          files: [
            'README.md',
            'docs/piano-di-progetto.md',
            'docs/piano-di-progetto.pdf',
            'docs/mappa/README.md',
            'docs/mappa/architettura.d2',
            'docs/mappa/out/index/sprint1.svg'
          ],
          commits: [
            { hash: 'c5e4836', date: '23 nov', who: 'Luca (@lufo-336)', what: 'Aggiorna piano e mappa D2: task Geoffrey (#20, #25) e barra accesso rapido' }
          ],
          links: [
            { label: 'Apri PR #26 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/26' },
            { label: 'Issue #25 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/25', secondary: true }
          ]
        },
        {
          id: 'pr24',
          order: 13,
          date: '23 nov',
          pr: 'PR #24',
          status: 'sprint2',
          statusLabel: 'Aperta · proposta del team dati',
          category: 'aperta',
          author: 'Giuseppe (@ASTROBLAST25)',
          title: 'Design relazionale del database: riferimenti, storico e indici (proposta)',
          desc: 'Proposta su branch dati/database-relazionale (+1041 righe in 4 file) di una seconda migrazione con tabelle di riferimento, tabelle storico/interventi, trigger, indici e script di prova SQL/Python.',
          files: [
            'db/migrations/20261124090000_design_relazionale.sql',
            'db/prove/prova_design_relazionale.sql',
            'db/prove/verifica_riferimenti.py',
            'docs/database-relazionale.md'
          ],
          commits: [
            { hash: '1d11dde', date: '23 nov', who: 'Giuseppe (@ASTROBLAST25)', what: 'Aggiunge la migrazione relazionale e le prove dei vincoli' },
            { hash: '5e27421', date: '23 nov', who: 'Giuseppe (@ASTROBLAST25)', what: 'Documenta il design relazionale del database' }
          ],
          links: [
            { label: 'Apri PR #24 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/24' }
          ]
        },
        {
          id: 'pr22',
          order: 12,
          date: '23 nov',
          pr: 'PR #22',
          status: 'fatto',
          statusLabel: 'Unita su main',
          category: 'unita',
          author: 'Luca (@lufo-336)',
          title: 'Documentazione aggiornata dopo il SAL 1: calendario, piano v0.2 e rimandi alla mappa',
          desc: 'Calendario aggiornato, piano v0.2, nota seed + down -v nel README, aggiornamento api.md/architettura.md e riallineamento mappa D2 ai merge #6, #8, #9 (merge cd20551, +1082/-492 in 16 file).',
          files: [
            'README.md',
            'docs/api.md',
            'docs/architettura.md',
            'docs/piano-di-progetto.md',
            'docs/team-dati.md',
            'docs/mappa/architettura.d2'
          ],
          commits: [
            { hash: 'd6dcdb9', date: '23 nov', who: 'Luca (@lufo-336)', what: 'Aggiorna documentazione: calendario dopo il SAL 1 e rimandi alla mappa' },
            { hash: '85487b1', date: '23 nov', who: 'Luca (@lufo-336)', what: 'Allinea branch docs/mappa-architettura con origin/main' },
            { hash: '9315c32', date: '23 nov', who: 'Luca (@lufo-336)', what: 'Riallinea docs e mappa D2 ai merge #6, #8, #9 e aggiunge la pagina storico' }
          ],
          links: [
            { label: 'Apri PR #22 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/22' }
          ]
        },
        {
          id: 'pr21',
          order: 11,
          date: '23 nov',
          pr: 'PR #21',
          status: 'fatto',
          statusLabel: 'Unita su main',
          category: 'unita',
          author: 'Luca (@lufo-336)',
          title: 'Mappa interattiva dell\'architettura (D2) fino allo Sprint 1',
          desc: 'Prima versione di docs/mappa/ su main: tema scuro ardesia, motore ELK a 90°, script compila.sh e 8 pagine navigabili (merge ed9bb77, +4252 righe in 12 file).',
          files: [
            'docs/mappa/README.md',
            'docs/mappa/architettura.d2',
            'docs/mappa/compila.sh',
            'docs/mappa/out/index/index.html',
            'docs/mappa/out/index/index.svg',
            'docs/mappa/out/index/sprint1.svg'
          ],
          commits: [
            { hash: '69363c1', date: '23 nov', who: 'Luca (@lufo-336)', what: 'Aggiunge la mappa interattiva dell\'architettura (D2) fino allo Sprint 1' }
          ],
          links: [
            { label: 'Apri PR #21 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/21' }
          ]
        },
        {
          id: 'pr10',
          order: 10,
          date: '23 nov',
          pr: 'PR #10',
          status: 'revisione',
          statusLabel: 'In revisione',
          category: 'aperta',
          author: 'Luca (@lufo-336)',
          title: 'CI di base con GitHub Actions: backend, frontend, Compose e seed',
          desc: 'Workflow .github/workflows/ci.yml con 3 job condizionali e concurrency su branch devops/ci (+126 righe in 1 file).',
          files: [
            '.github/workflows/ci.yml'
          ],
          commits: [
            { hash: '46d1803', date: '23 nov', who: 'Luca (@lufo-336)', what: 'Aggiunge la CI di base con GitHub Actions (backend, frontend, Compose)' }
          ],
          links: [
            { label: 'Apri PR #10 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/10' },
            { label: 'Issue #11 ↗', href: 'https://github.com/lufo-336/under-the-sun/issues/11', secondary: true }
          ]
        },
        {
          id: 'pr9',
          order: 9,
          date: '23 nov',
          pr: 'PR #9',
          status: 'fatto',
          statusLabel: 'Unita su main',
          category: 'unita',
          hasReview: true,
          author: 'Stefano (@stefanospadaccini-888)',
          title: 'Scheletro del backend: login JWT, ruoli e /api/impianti',
          desc: 'Node 22 + Express 5 + pg: /api/salute, /api/auth/login, /api/auth/me, /api/impianti, script crea-utenti, 7 test automatici e servizio backend in compose.yaml (merge c0adefd, +1988/-4 in 19 file).',
          review: '<strong>Approvazioni e prove:</strong> approvata da Luca (@lufo-336) il 23 nov; verificati npm test (7/7), build su Podman Fedora, script crea-utenti e risposte di /api/impianti (200 operatore, 403 socio).',
          files: [
            'backend/src/app.js',
            'backend/src/auth.js',
            'backend/src/routes/auth.js',
            'backend/src/routes/impianti.js',
            'backend/test/api.test.js',
            'compose.yaml'
          ],
          commits: [
            { hash: '4b53d84', date: '23 nov', who: 'Stefano (@stefanospadaccini-888)', what: 'Aggiunge lo scheletro del backend: login JWT, ruoli e /api/impianti' }
          ],
          links: [
            { label: 'Apri PR #9 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/9' }
          ]
        },
        {
          id: 'pr8',
          order: 8,
          date: '19 → 23 nov',
          pr: 'PR #8',
          status: 'fatto',
          statusLabel: 'Unita su main',
          category: 'unita',
          hasReview: true,
          author: 'Francesco (@francescocolohan)',
          title: 'Campione dati SAL 1 (giugno 2026 · 15 CSV · 123 controlli)',
          desc: 'Pipeline Python unica con seed fisso 42, fonti reali (Open-Meteo, PVGIS, ARERA, ISPRA, GSE), 123 controlli automatici e data dictionary v1 (merge e0d80d0, +37915 righe in 32 file).',
          review: '<strong>Approvazioni e prove:</strong> approvata da Mirko (@mirkodivincenzo) il 20 nov e da Luca (@lufo-336) il 23 nov; caricamento dei 13 CSV in Postgres eseguito senza errori.',
          files: [
            'data/GUIDA-DATASET.md',
            'data/data-dictionary.md',
            'data/generazione/genera.py',
            'data/generazione/config.py',
            'data/generazione/controlli.py',
            'data/esempi/impianto.csv'
          ],
          commits: [
            { hash: '44ab791', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Aggiunge la guida al dataset v1.1, il data dictionary e le istruzioni' },
            { hash: '6080a00', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Prepara la pipeline dati e le intestazioni dei CSV del campione SAL 1' },
            { hash: 'b63bb2b', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Aggiunge le 15 segnalazioni del campione SAL 1' },
            { hash: '58c545a', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Aggiunge .gitattributes (CSV con fine riga LF) e .gitignore' },
            { hash: 'e9f662e', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Aggiorna la guida alla v1.3 e il profilo bar nel data dictionary' },
            { hash: '1f99c57', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Genera anagrafiche, meteo e produzione del campione SAL 1' },
            { hash: '10f2f4b', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Guida v1.5, data dictionary e segnalazione 2 coerente' },
            { hash: '1c6ec36', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Genera i consumi del campione SAL 1: volumi provvisori' },
            { hash: '024e1d9', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Guida v1.6, data dictionary e verbale del 9 luglio 2026' },
            { hash: '93c43b4', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Genera bolletta e tabelle provvisorie del campione SAL 1; guida v1.7' },
            { hash: '70c4e29', date: '19 nov', who: 'Francesco (@francescocolohan)', what: 'Aggiunge controlli.py e i grafici di controllo; guida v1.8 e verbale' }
          ],
          links: [
            { label: 'Apri PR #8 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/8' }
          ]
        },
        {
          id: 'pr6',
          order: 7,
          date: '16 → 23 nov',
          pr: 'PR #6',
          status: 'fatto',
          statusLabel: 'Unita su main',
          category: 'unita',
          hasReview: true,
          author: 'Luca (@lufo-336)',
          title: 'Database in Docker: schema (14 tabelle), dbmate e caricamento CSV (US-10, US-13)',
          desc: 'Postgres 17, migrazioni dbmate, carica.sql con HEADER match in transazione unica e allineamento al data dictionary v1 (merge 31dfa21, +278/-7 in 8 file).',
          review: '<strong>Approvazioni e prove:</strong> approvata da Mirko (@mirkodivincenzo) il 17 nov; provata con i 13 CSV della PR #8 su Docker Desktop Windows 11 (Stefano @stefanospadaccini-888) e su Podman Fedora (Luca @lufo-336).',
          files: [
            'compose.yaml',
            'db/migrations/20261116090000_schema_iniziale.sql',
            'db/seed/carica.sql',
            '.env.example',
            'docs/api.md',
            'docs/architettura.md'
          ],
          commits: [
            { hash: '542728c', date: '16 nov', who: 'Luca (@lufo-336)', what: 'Aggiunge database in Docker: schema, migrazioni e caricamento dei CSV' },
            { hash: '5f1ec52', date: '22 nov', who: 'Luca (@lufo-336)', what: 'Allinea lo schema al data dictionary v1 del team dati (SAL 1)' }
          ],
          links: [
            { label: 'Apri PR #6 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/6' }
          ]
        },
        {
          id: 'pr7',
          order: 6,
          date: '17 → 23 nov',
          pr: 'PR #7',
          status: 'sprint2',
          statusLabel: 'Chiusa (integrata in #23)',
          category: 'chiusa',
          author: 'Mirko (@mirkodivincenzo)',
          title: 'Restyling UI responsive con Tailwind',
          desc: 'Branch frontend/restyling-ui (+3891 righe in 33 file). Il commit 3cbe968 è confluito nei branch #5 e #23; PR chiusa il 23 novembre senza merge.',
          files: [
            'frontend/src/App.jsx',
            'frontend/src/components/AppLayout.jsx',
            'frontend/src/pages/auth/LoginPage.jsx',
            'frontend/src/pages/socio/SocioDashboardPage.jsx',
            'frontend/src/services/apiClient.js',
            'frontend/src/mocks/mockData.js'
          ],
          commits: [
            { hash: '6710a4c', date: '15 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Inizializza progetto React + Vite con Router e Recharts' },
            { hash: '32f346c', date: '15 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Bozza wireframe interattivo delle 8 viste per ruolo' },
            { hash: '3cbe968', date: '17 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Applica nuova UI responsive con Tailwind' }
          ],
          links: [
            { label: 'Apri PR #7 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/7' }
          ]
        },
        {
          id: 'pr4',
          order: 5,
          date: '15 → 23 nov',
          pr: 'PR #4',
          status: 'sprint2',
          statusLabel: 'Chiusa (già in #23)',
          category: 'chiusa',
          author: 'Mirko (@mirkodivincenzo)',
          title: 'Setup iniziale React + Vite con Router e Recharts',
          desc: 'Branch frontend/setup (+2419 righe in 16 file). Il commit 6710a4c è confluito nei branch #5 e #23; PR chiusa il 23 novembre senza merge.',
          files: [
            'frontend/package.json',
            'frontend/vite.config.js',
            'frontend/index.html',
            'frontend/src/main.jsx',
            'frontend/src/App.jsx',
            'frontend/src/index.css'
          ],
          commits: [
            { hash: '6710a4c', date: '15 nov', who: 'Mirko (@mirkodivincenzo)', what: 'Inizializza progetto React + Vite con Router e Recharts' }
          ],
          links: [
            { label: 'Apri PR #4 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/4' }
          ]
        },
        {
          id: 'pr3',
          order: 4,
          date: '13 nov',
          pr: 'PR #3',
          status: 'fatto',
          statusLabel: 'Unita su main',
          category: 'unita',
          author: 'Luca (@lufo-336)',
          title: 'Allinea README e brief del team dati ai ruoli del piano',
          desc: 'Allineamento dei ruoli tra README e docs/team-dati.md rispetto al piano di progetto (branch docs/allinea-ruoli, +10/-4 in 2 file, merge fec58a7).',
          files: [
            'README.md',
            'docs/team-dati.md'
          ],
          commits: [
            { hash: '7f8b9a7', date: '13 nov', who: 'Luca (@lufo-336)', what: 'Allinea README e brief del team dati ai ruoli del piano' }
          ],
          links: [
            { label: 'Apri PR #3 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/3' }
          ]
        },
        {
          id: 'pr2',
          order: 3,
          date: '9 → 13 nov',
          pr: 'PR #2',
          status: 'fatto',
          statusLabel: 'Unita su main',
          category: 'unita',
          author: 'Luca (@lufo-336)',
          title: 'Modello dati corretto e piano di progetto v0.1',
          desc: 'Inseriti il piano di progetto v0.1 (md e PDF), il calendario e le correzioni al modello ER (previsioni, stato anomalie, correzioni operatore) (merge ffc236a, +272/-25 in 10 file).',
          files: [
            'README.md',
            'docs/api.md',
            'docs/architettura.md',
            'docs/piano-di-progetto.md',
            'docs/piano-di-progetto.pdf',
            'docs/team-dati.md'
          ],
          commits: [
            { hash: 'b2319a5', date: '9 nov', who: 'Luca (@lufo-336)', what: 'Corregge il modello dati: previsioni, stato anomalie, correzioni operatore' },
            { hash: '924681c', date: '13 nov', who: 'Luca (@lufo-336)', what: 'Aggiunge il piano di progetto v0.1 e allinea il calendario' }
          ],
          links: [
            { label: 'Apri PR #2 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/2' }
          ]
        },
        {
          id: 'pr1',
          order: 2,
          date: '6 → 9 nov',
          pr: 'PR #1',
          status: 'fatto',
          statusLabel: 'Unita su main',
          category: 'unita',
          author: 'Luca (@lufo-336)',
          title: 'Guida rapida a Git per il team (docs/git.md)',
          desc: 'Prima PR del repository (branch docs/guida-git, +142 righe in 2 file, merge b7abef3): guida pratica per branch e Pull Request.',
          files: [
            'README.md',
            'docs/git.md'
          ],
          commits: [
            { hash: '422a61c', date: '6 nov', who: 'Luca (@lufo-336)', what: 'Aggiunge guida rapida a Git per il team' },
            { hash: '6ef6b06', date: '9 nov', who: 'Luca (@lufo-336)', what: 'Guida Git: aggiorna il nome del repo in under-the-sun' }
          ],
          links: [
            { label: 'Apri PR #1 ↗', href: 'https://github.com/lufo-336/under-the-sun/pull/1' }
          ]
        },
        {
          id: 'kickoff',
          order: 1,
          date: '6 nov',
          pr: 'Avvio · 6 nov',
          status: 'fatto',
          statusLabel: 'Avvio progetto',
          category: 'avvio',
          author: 'Luca (@lufo-336)',
          title: 'Kickoff e bozza iniziale · 6 nov',
          desc: 'Kickoff sul brief Buby Green e nascita del repository con la prima bozza di README, architettura, contratto API, brief per il team dati e guida Git.',
          files: [
            'README.md',
            'docs/architettura.md',
            'docs/api.md',
            'docs/team-dati.md',
            'docs/git.md'
          ],
          commits: [
            { hash: '29c89c6', date: '6 nov', who: 'Luca (@lufo-336)', what: 'Bozza iniziale README, architettura, contratto API e brief team dati' },
            { hash: '422a61c', date: '6 nov', who: 'Luca (@lufo-336)', what: 'Aggiunge guida rapida a Git per il team' }
          ],
          links: [
            { label: 'Commit 29c89c6 ↗', href: 'https://github.com/lufo-336/under-the-sun/commit/29c89c6' }
          ]
        }
      ]
    }
  }
};
