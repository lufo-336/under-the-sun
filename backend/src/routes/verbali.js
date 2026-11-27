import { Router } from 'express';
import { autentica, richiediRuolo } from '../auth.js';
import { datiNonValidi, ErroreApi } from '../errori.js';

// US-14: l'admin legge i verbali delle assemblee con la sintesi dell'LLM.
// GET /api/verbali      → elenco (id, data_assemblea, sintesi)
// GET /api/verbali/:id  → testo completo + sintesi
export function rotteVerbali({ db, config }) {
  const router = Router();
  router.use(autentica(config), richiediRuolo('admin'));

  router.get('/', async (req, res) => {
    const { rows } = await db.query(`
      SELECT id, to_char(data_assemblea, 'YYYY-MM-DD') AS data_assemblea, sintesi
      FROM verbale
      ORDER BY data_assemblea DESC`);
    res.json(rows);
  });

  router.get('/:id', async (req, res) => {
    const id = Number(req.params.id);
if (!Number.isInteger(id) || id < 1 || id > 2147483647) {
      throw datiNonValidi('Id del verbale non valido');
    }
    const { rows } = await db.query(
      `SELECT id, to_char(data_assemblea, 'YYYY-MM-DD') AS data_assemblea, testo, sintesi
       FROM verbale WHERE id = $1`,
      [id],
    );
    if (!rows[0]) {
      throw new ErroreApi(404, 'NON_TROVATO', 'Verbale non trovato');
    }
    res.json(rows[0]);
  });

  return router;
}