import { Router } from 'express';

// GET /api/salute: endpoint di prova, pubblico. Dice se il backend è vivo e se
// raggiunge il database. Lo usa anche il healthcheck di Docker Compose.
export function rotteSalute({ db }) {
  const router = Router();

  router.get('/', async (req, res) => {
    try {
      await db.query('SELECT 1');
      res.json({ stato: 'ok', database: 'ok' });
    } catch {
      res.status(503).json({ stato: 'degradato', database: 'irraggiungibile' });
    }
  });

  return router;
}
