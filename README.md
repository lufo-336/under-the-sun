# UnderTheSun

Portale della Comunità Energetica Rinnovabile (CER) di **Buby Green** — progetto del Laboratorio Integrato ITS (Data Analyst / AI Specialist + Web Solutions Architect), team **PlusUltra**.

> Stato: **Sprint 1** (23 nov → 4 dic 2026). Schema dati e contratto API sono quelli del SAL 1 (lun 23 nov); cosa è fatto e cosa manca è nella [mappa dell'architettura](docs/mappa/README.md).

## Cosa fa

- **Soci** (famiglie, imprese, enti): vedono consumi, energia condivisa, incentivo CER e CO2 evitata; simulano il risparmio; aprono segnalazioni.
- **Operatori**: monitorano gli impianti (produzione vs previsione, anomalie) e gestiscono le segnalazioni, classificate automaticamente.
- **Admin**: KPI della comunità, soci, verbali delle assemblee con sintesi.

## Team

| Persona | Ruolo |
|---|---|
| Luca Foglia | Team leader, architettura, DevOps (WSA) |
| Mirko Di Vincenzo | Frontend, vice team leader (WSA) |
| Stefano Spadaccini | Backend, vice team leader (WSA) |
| Geoffrey JR Etinosa | Jolly: dove serve nello sprint, ponte Git per il team dati, prove dell'app (WSA) |
| Francesco Colohan | Data Analyst / AI, riferimento del team dati |
| Giuseppe Tommasi | Data Analyst / AI |
| Cecilia Montebello | Data Analyst / AI |

## Struttura del repo

```
data/        script di generazione, notebook, batch (previsioni, anomalie, ripartizione CER) — team dati
backend/     API Node + Express — WSA
frontend/    React — WSA
docs/        architettura, contratto API, brief per il team dati
db/          migrazioni dello schema (dbmate) e caricamento dei CSV — WSA
compose.yaml servizi Docker
```

## Documentazione

- [Piano di progetto](docs/piano-di-progetto.md) ([PDF](docs/piano-di-progetto.pdf)): storie, ruoli, sprint ← **tutti: partite da qui**
- [Architettura e modello dati](docs/architettura.md)
- [Bozza contratto API](docs/api.md)
- [Brief per il team dati](docs/team-dati.md) ← **data analyst: partite da qui**
- [Guida rapida a Git](docs/git.md) ← **mai usato Git? leggi qui**
- [Mappa interattiva dell'architettura](docs/mappa/README.md): schema cliccabile con lo stato fino allo Sprint 1; dopo il clone apri `docs/mappa/out/index/index.html`

## Stack (proposta)

React · Node + Express · PostgreSQL · Python (pandas, scikit-learn) · LLM via API · Docker Compose

## Calendario

| Periodo | Obiettivo |
|---|---|
| 12–23 nov · sprint 0 | Docker e DB per tutti, wireframe, schema + data dictionary + contratto API, campione di dati. **SAL 1 lun 23 nov** |
| 23 nov – 4 dic · sprint 1 | Primo percorso completo (login, dashboard socio, segnalazioni); dataset completo. **Mini SAL col cliente ven 27 nov**, **SAL 2 ven 4 dic** |
| 4–14 dic · sprint 2 | Tutte le pagine, batch e classificazione collegati al portale |
| 14 dic → gennaio · sprint 3 | Solo correzioni. **SAL finale col cliente ven 18 dic**; a gennaio rifiniture e **presentazione finale** nell'ultima lezione |

Ogni SAL segue la stessa scaletta: come siamo organizzati, chi ha fatto cosa, cosa si farà poi, scelte operate sull'architettura.

Dettagli, ruoli e chi fa cosa: [docs/piano-di-progetto.md](docs/piano-di-progetto.md) ([PDF](docs/piano-di-progetto.pdf)).

## Avvio (database e backend)

Serve Docker Desktop (o Docker con Compose).

```bash
cp .env.example .env             # una volta sola
docker compose up -d --build     # Postgres + schema (localhost:5433) + backend (localhost:3000)
docker compose run --rm seed     # carica i CSV di data/esempi
docker compose exec backend npm run crea-utenti   # account di prova
docker compose down -v           # ripartire da zero (cancella i dati)
```

Account di prova ed endpoint pronti: [backend/README.md](backend/README.md).

Lo schema sta in `db/migrations/`, il caricamento in `db/seed/carica.sql`. I CSV devono avere le intestazioni uguali alle colonne della tabella, nello stesso ordine: se no il caricamento si ferma e non carica niente.

## Regole di lavoro

- Niente push diretti su `main`: branch + Pull Request + almeno una review.
- Mai committare chiavi API o file `.env`.
- Mai committare dataset completi: si committano gli script (con seed fisso) e i CSV di esempio.
- Non usi Git? Metti i file nella cartella Drive del team dati: Geoffrey li porta nel repo con una Pull Request.
