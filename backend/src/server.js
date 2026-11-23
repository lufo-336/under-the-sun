import { creaApp } from './app.js';
import { leggiConfig } from './config.js';
import { creaDb } from './db.js';

const config = leggiConfig();
const db = creaDb(config.databaseUrl);
const app = creaApp({ db, config });

const server = app.listen(config.porta, () => {
  console.log(`Backend UnderTheSun su http://localhost:${config.porta}/api`);
});

// docker compose stop manda SIGTERM: chiudiamo le connessioni in ordine.
for (const segnale of ['SIGTERM', 'SIGINT']) {
  process.on(segnale, () => {
    server.close(() => db.end().then(() => process.exit(0)));
  });
}
