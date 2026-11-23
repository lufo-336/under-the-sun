import { Router } from 'express';
import { autentica, richiediRuolo } from '../auth.js';

// Primo endpoint "vero" del contratto, usato come prova di login + ruoli:
// GET /api/impianti → solo operatore e admin (un socio riceve 403).
export function rotteImpianti({ db, config }) {
  const router = Router();
  router.use(autentica(config), richiediRuolo('operatore', 'admin'));

  router.get('/', async (req, res) => {
    const { rows } = await db.query(`
      SELECT i.id, i.nome, i.comune, i.lat, i.lon, i.kwp,
             to_char(i.data_attivazione, 'YYYY-MM-DD') AS data_attivazione,
             count(a.id)::int AS anomalie_aperte
      FROM impianto i
      LEFT JOIN anomalia a ON a.impianto_id = i.id AND a.stato = 'aperta'
      GROUP BY i.id
      ORDER BY i.id`);
    res.json(rows);
  });

  return router;
}
