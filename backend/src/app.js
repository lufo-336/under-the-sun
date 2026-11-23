import express from 'express';
import { gestoreErrori, percorsoNonTrovato } from './errori.js';
import { rotteAuth } from './routes/auth.js';
import { rotteImpianti } from './routes/impianti.js';
import { rotteSalute } from './routes/salute.js';

// L'app riceve db e config dall'esterno: così i test le passano un database finto
// e non serve Postgres per farli girare.
export function creaApp({ db, config }) {
  const app = express();
  app.disable('x-powered-by');
  app.use(express.json({ limit: '100kb' }));

  app.use('/api/salute', rotteSalute({ db }));
  app.use('/api/auth', rotteAuth({ db, config }));
  app.use('/api/impianti', rotteImpianti({ db, config }));

  app.use(percorsoNonTrovato);
  app.use(gestoreErrori);
  return app;
}
