import { Router } from 'express';
import { autentica, richiediRuolo } from '../auth.js';
import { datiNonValidi } from '../errori.js';
import { riepilogoSocio } from '../servizi/riepilogo.js';

// Area socio: /api/me/... Tutti gli endpoint usano il socio_id del token,
// mai un id che arriva dalla richiesta: così un socio vede solo i suoi dati.
export function rotteMe({ db, config }) {
  const router = Router();
  router.use(autentica(config), richiediRuolo('socio'));

  // GET /api/me/riepilogo?anno=2026 (senza anno: l'anno in corso, in UTC)
  router.get('/riepilogo', async (req, res) => {
    const anno = leggiAnno(req.query.anno);
    res.json(await riepilogoSocio(db, req.utente.socio_id, anno));
  });

  return router;
}

function leggiAnno(valore) {
  if (valore === undefined) return new Date().getUTCFullYear();
  if (typeof valore !== 'string' || !/^\d{4}$/.test(valore) || valore < '2000' || valore > '2100') {
    throw datiNonValidi('anno deve essere un anno tra 2000 e 2100, es. ?anno=2026');
  }
  return Number(valore);
}
