import jwt from 'jsonwebtoken';
import { nonAutenticato, vietato } from './errori.js';

// Nel token mettiamo solo quello che serve a decidere i permessi.
// Il ruolo lo controlla sempre il server: il frontend lo usa solo per la navigazione.
export function firmaToken(utente, config) {
  return jwt.sign(
    { ruolo: utente.ruolo, socio_id: utente.socio_id },
    config.jwtSegreto,
    { subject: String(utente.id), expiresIn: config.jwtScadenza, algorithm: 'HS256' },
  );
}

// Legge "Authorization: Bearer <token>" e mette l'utente in req.utente.
export function autentica(config) {
  return (req, res, next) => {
    const [schema, token] = (req.get('authorization') ?? '').split(' ');
    if (schema !== 'Bearer' || !token) {
      return next(nonAutenticato());
    }
    try {
      const dati = jwt.verify(token, config.jwtSegreto, { algorithms: ['HS256'] });
      req.utente = { id: Number(dati.sub), ruolo: dati.ruolo, socio_id: dati.socio_id ?? null };
      next();
    } catch {
      next(nonAutenticato('Token non valido o scaduto'));
    }
  };
}

// Da mettere DOPO autentica: richiediRuolo('operatore', 'admin')
export function richiediRuolo(...ruoli) {
  return (req, res, next) => {
    if (!ruoli.includes(req.utente?.ruolo)) {
      return next(vietato());
    }
    next();
  };
}
