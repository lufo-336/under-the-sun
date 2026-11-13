# UnderTheSun

Portale della Comunità Energetica Rinnovabile (CER) di **Buby Green** — progetto del Laboratorio Integrato ITS (Data Analyst / AI Specialist + Web Solutions Architect), team **PlusUltra**.

> Stato: **bozza pre-SAL 1**. Schema dati e contratto API si congelano al SAL 1 (ven 20 nov 2026).

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
```

## Documentazione

- [Piano di progetto](docs/piano-di-progetto.md) ([PDF](docs/piano-di-progetto.pdf)): storie, ruoli, sprint ← **tutti: partite da qui**
- [Architettura e modello dati](docs/architettura.md)
- [Bozza contratto API](docs/api.md)
- [Brief per il team dati](docs/team-dati.md) ← **data analyst: partite da qui**
- [Guida rapida a Git](docs/git.md) ← **mai usato Git? leggi qui**

## Stack (proposta)

React · Node + Express · PostgreSQL · Python (pandas, scikit-learn) · LLM via API · Docker Compose

## Calendario

| Periodo | Obiettivo |
|---|---|
| 12–20 nov · sprint 0 | Docker e DB per tutti, wireframe, schema + data dictionary + contratto API, CSV di esempio. **SAL 1 ven 20 nov** |
| 23 nov – 4 dic · sprint 1 | Primo percorso completo (login, dashboard socio, segnalazioni); dataset completo. **SAL 2 ven 4 dic** |
| 4–14 dic · sprint 2 | Tutte le pagine, batch e classificazione collegati al portale |
| 14–21 dic · sprint 3 | Solo correzioni, prova generale ven 18 dic. **Consegna finale lun 21 dic** |

Dettagli, ruoli e chi fa cosa: [docs/piano-di-progetto.md](docs/piano-di-progetto.md) ([PDF](docs/piano-di-progetto.pdf)).

## Regole di lavoro

- Niente push diretti su `main`: branch + Pull Request + almeno una review.
- Mai committare chiavi API o file `.env`.
- Mai committare dataset completi: si committano gli script (con seed fisso) e i CSV di esempio.
- Non usi Git? Metti i file nella cartella Drive del team dati: Geoffrey li porta nel repo con una Pull Request.
