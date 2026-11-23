// Crea gli account di prova (seed.sql non carica la tabella utente: le password
// vanno salvate come hash, e l'hash lo fa il backend).
//
//   admin@example.com       ruolo admin
//   operatore@example.com   ruolo operatore
//   socio<id>@example.com   un account per ogni socio che non ne ha ancora uno
//
// Tutti con la password PASSWORD_PROVA del file .env. Si può rilanciare quante
// volte si vuole: gli account esistenti vengono aggiornati, non duplicati.
// Uso: npm run crea-utenti   (oppure: docker compose exec backend npm run crea-utenti)

import bcrypt from 'bcryptjs';
import { creaDb } from '../src/db.js';

const { DATABASE_URL, PASSWORD_PROVA } = process.env;
if (!DATABASE_URL || !PASSWORD_PROVA) {
  console.error('Servono DATABASE_URL e PASSWORD_PROVA: copia .env.example in .env');
  process.exit(1);
}

const db = creaDb(DATABASE_URL);
try {
  const hash = await bcrypt.hash(PASSWORD_PROVA, 10);
  const client = await db.connect();
  try {
    await client.query('BEGIN');

    for (const ruolo of ['admin', 'operatore']) {
      await client.query(
        `INSERT INTO utente (email, password_hash, ruolo) VALUES ($1, $2, $3)
         ON CONFLICT (email) DO UPDATE SET password_hash = EXCLUDED.password_hash`,
        [`${ruolo}@example.com`, hash, ruolo],
      );
    }

    const { rowCount: nuoviSoci } = await client.query(
      `INSERT INTO utente (email, password_hash, ruolo, socio_id)
       SELECT 'socio' || s.id || '@example.com', $1, 'socio', s.id
       FROM socio s
       WHERE NOT EXISTS (SELECT 1 FROM utente u WHERE u.socio_id = s.id)
       ON CONFLICT (email) DO NOTHING`,
      [hash],
    );

    await client.query('COMMIT');
    console.log(`Account pronti: admin, operatore e ${nuoviSoci} nuovi soci (socio<id>@example.com).`);
  } catch (err) {
    await client.query('ROLLBACK');
    throw err;
  } finally {
    client.release();
  }
} finally {
  await db.end();
}
