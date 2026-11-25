# Backend UnderTheSun

API REST del portale: Node 22+, Express 5, PostgreSQL (`pg`), login con JWT. Il contratto degli endpoint è in [docs/api.md](../docs/api.md).

## Avvio

### Con Docker (consigliato)

Dalla radice del repo:

```bash
cp .env.example .env                          # una volta sola
docker compose up -d --build db migrate backend
docker compose run --rm seed                  # carica i CSV di esempio
docker compose exec backend npm run crea-utenti
```

Le API rispondono su `http://localhost:3000/api`.

### Senza Docker per il backend (sviluppo con riavvio automatico)

Serve comunque il database: `docker compose up -d db migrate` e poi `docker compose run --rm seed`.

```bash
cd backend
npm install
npm run crea-utenti   # account di prova
npm run dev           # legge ../.env e si riavvia a ogni modifica
```

## Account di prova

`npm run crea-utenti` crea questi account, tutti con la password `PASSWORD_PROVA` del file `.env`:

| Email | Ruolo |
|---|---|
| `admin@example.com` | admin |
| `operatore@example.com` | operatore |
| `socio<id>@example.com` (es. `socio1@example.com`) | socio, uno per ogni socio caricato dai CSV |

Si può rilanciare: non crea doppioni. Va rilanciato dopo ogni `docker compose down -v` e dopo aver caricato soci nuovi.

## Provarlo a mano

```bash
curl http://localhost:3000/api/salute

curl -X POST http://localhost:3000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"operatore@example.com","password":"prova1234"}'

curl http://localhost:3000/api/impianti -H "Authorization: Bearer <token>"
```

## Endpoint pronti

| Metodo | Percorso | Chi | Note |
|---|---|---|---|
| GET | `/api/salute` | pubblico | backend vivo + database raggiungibile (503 se il DB non risponde) |
| POST | `/api/auth/login` | pubblico | `{ email, password }` → `{ token, utente }`; 401 `CREDENZIALI_ERRATE` |
| GET | `/api/auth/me` | tutti i loggati | utente corrente |
| GET | `/api/impianti` | operatore, admin | elenco con `anomalie_aperte`; il socio riceve 403 |
| GET | `/api/me/riepilogo?anno=` | socio | totali e mesi dell'anno; `null` dove il batch non ha ancora calcolato la ripartizione |

## Struttura

```
src/
  server.js        avvio (legge la config, apre il pool, ascolta sulla porta)
  app.js           crea l'app Express e monta le rotte
  config.js        variabili d'ambiente (si ferma se manca DATABASE_URL o JWT_SECRET)
  db.js            pool PostgreSQL
  auth.js          token JWT, middleware autentica e richiediRuolo
  errori.js        errori nel formato del contratto { errore: { codice, messaggio } }
  routes/          un file per gruppo di endpoint
scripts/
  crea-utenti-prova.js
test/              test con database finto: npm test (non serve Postgres)
```

### Aggiungere un endpoint

1. Crea `src/routes/<gruppo>.js` che esporta `rotte<Gruppo>({ db, config })` e restituisce un `Router`.
2. Proteggilo con `autentica(config)` e, se serve, `richiediRuolo('operatore', 'admin')`.
3. Per l'area socio usa sempre `req.utente.socio_id` dal token, mai un id che arriva dalla richiesta: così un socio vede solo i suoi dati.
4. Montalo in `src/app.js` e aggiungi un test in `test/`.

Con Express 5 gli errori lanciati nelle funzioni `async` arrivano da soli al gestore degli errori: basta `throw datiNonValidi('...')`.

## Variabili d'ambiente

| Nome | Obbligatoria | Default | A cosa serve |
|---|---|---|---|
| `DATABASE_URL` | sì | | connessione a Postgres |
| `JWT_SECRET` | sì | | chiave per firmare i token |
| `JWT_SCADENZA` | no | `8h` | durata del login |
| `PORT` | no | `3000` | porta del server |
| `PASSWORD_PROVA` | solo per `crea-utenti` | | password degli account di prova |
