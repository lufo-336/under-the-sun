import { Router } from 'express';
import bcrypt from 'bcryptjs';
import { autentica, firmaToken } from '../auth.js';
import { datiNonValidi, nonAutenticato, ErroreApi } from '../errori.js';

// Hash di una password qualunque: se l'email non esiste confrontiamo comunque,
// così la risposta impiega lo stesso tempo e non rivela quali email sono registrate.
const HASH_FITTIZIO = bcrypt.hashSync('nessun-utente', 10);

const utentePubblico = ({ id, email, ruolo, socio_id }) => ({ id, email, ruolo, socio_id });

export function rotteAuth({ db, config }) {
  const router = Router();

  // POST /api/auth/login  { email, password } → { token, utente }
  router.post('/login', async (req, res) => {
    const { email, password } = req.body ?? {};
    if (typeof email !== 'string' || typeof password !== 'string' || !email || !password) {
      throw datiNonValidi('Servono email e password');
    }

    const { rows } = await db.query(
      'SELECT id, email, password_hash, ruolo, socio_id FROM utente WHERE lower(email) = lower($1)',
      [email.trim()],
    );
    const utente = rows[0];
    const passwordGiusta = await bcrypt.compare(password, utente?.password_hash ?? HASH_FITTIZIO);
    if (!utente || !passwordGiusta) {
      throw new ErroreApi(401, 'CREDENZIALI_ERRATE', 'Email o password non corrette');
    }

    res.json({ token: firmaToken(utente, config), utente: utentePubblico(utente) });
  });

  // GET /api/auth/me → l'utente del token, riletto dal DB
  router.get('/me', autentica(config), async (req, res) => {
    const { rows } = await db.query(
      'SELECT id, email, ruolo, socio_id FROM utente WHERE id = $1',
      [req.utente.id],
    );
    if (!rows[0]) {
      throw nonAutenticato('Utente non più esistente');
    }
    res.json(utentePubblico(rows[0]));
  });

  return router;
}
