// Test dell'area socio (/api/me/...) con database finto: npm test.
// File separato da api.test.js così chi lavora su endpoint diversi non va in conflitto.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import request from 'supertest';
import { creaApp } from '../src/app.js';
import { firmaToken } from '../src/auth.js';

const config = { jwtSegreto: 'segreto-di-test', jwtScadenza: '1h' };
const token = (utente) => `Bearer ${firmaToken(utente, config)}`;
const SOCIO = token({ id: 3, ruolo: 'socio', socio_id: 1 });
const OPERATORE = token({ id: 2, ruolo: 'operatore', socio_id: null });

// Righe come le restituisce Postgres: giugno con ripartizione, luglio senza.
const mesi = [
  { mese: '2026-06', kwh_consumati: 250.04, kwh_condivisi: 101.973, incentivo_eur: 14.07, co2_evitata_kg: 42.145 },
  { mese: '2026-07', kwh_consumati: 180.06, kwh_condivisi: null, incentivo_eur: null, co2_evitata_kg: null },
];

// Ricorda i parametri dell'ultima query, così il test vede quale socio e anno sono stati chiesti.
function dbFinto(righe = mesi) {
  const db = {
    ultimiParametri: null,
    async query(sql, params = []) {
      if (sql.includes('FROM consumo_orario')) {
        db.ultimiParametri = params;
        return { rows: righe };
      }
      throw new Error(`query inattesa: ${sql}`);
    },
  };
  return db;
}

test('riepilogo: 401 senza token, 403 a chi non è socio', async () => {
  const app = creaApp({ db: dbFinto(), config });
  assert.equal((await request(app).get('/api/me/riepilogo')).status, 401);

  const res = await request(app).get('/api/me/riepilogo').set('Authorization', OPERATORE);
  assert.equal(res.status, 403);
  assert.equal(res.body.errore.codice, 'VIETATO');
});

test('riepilogo: usa il socio del token, ignora un socio_id passato nella richiesta', async () => {
  const db = dbFinto();
  const app = creaApp({ db, config });
  const res = await request(app).get('/api/me/riepilogo?anno=2026&socio_id=99').set('Authorization', SOCIO);
  assert.equal(res.status, 200);
  assert.deepEqual(db.ultimiParametri, [1, 2026]);
});

test('riepilogo: totali, mesi e null dove il batch non ha ancora calcolato', async () => {
  const app = creaApp({ db: dbFinto(), config });
  const res = await request(app).get('/api/me/riepilogo?anno=2026').set('Authorization', SOCIO);
  assert.deepEqual(res.body, {
    anno: 2026,
    kwh_consumati: 430.1,
    kwh_condivisi: 102.0,
    incentivo_eur: 14.07,
    co2_evitata_kg: 42.1,
    mesi: [
      { mese: '2026-06', kwh_consumati: 250.0, kwh_condivisi: 102.0, incentivo_eur: 14.07, co2_evitata_kg: 42.1 },
      { mese: '2026-07', kwh_consumati: 180.1, kwh_condivisi: null, incentivo_eur: null, co2_evitata_kg: null },
    ],
  });
});

test('riepilogo: anno senza dati → totali a 0/null e nessun mese', async () => {
  const app = creaApp({ db: dbFinto([]), config });
  const res = await request(app).get('/api/me/riepilogo?anno=2030').set('Authorization', SOCIO);
  assert.equal(res.status, 200);
  assert.deepEqual(res.body, {
    anno: 2030, kwh_consumati: 0, kwh_condivisi: null, incentivo_eur: null, co2_evitata_kg: null, mesi: [],
  });
});

test("riepilogo: senza anno usa l'anno in corso, anno non valido → 400", async () => {
  const db = dbFinto();
  const app = creaApp({ db, config });
  await request(app).get('/api/me/riepilogo').set('Authorization', SOCIO);
  assert.equal(db.ultimiParametri[1], new Date().getUTCFullYear());

  for (const anno of ['abc', '26', '1999', '2101', '2026.5']) {
    const res = await request(app).get(`/api/me/riepilogo?anno=${anno}`).set('Authorization', SOCIO);
    assert.equal(res.status, 400, `anno=${anno}`);
    assert.equal(res.body.errore.codice, 'DATI_NON_VALIDI');
  }
});
