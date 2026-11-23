// Test senza Postgres: l'app riceve un database finto che risponde alle query
// con dati in memoria. Si lanciano con `npm test`.

import { test } from 'node:test';
import assert from 'node:assert/strict';
import bcrypt from 'bcryptjs';
import request from 'supertest';
import { creaApp } from '../src/app.js';

const config = { jwtSegreto: 'segreto-di-test', jwtScadenza: '1h' };
const hash = bcrypt.hashSync('prova1234', 4);

const utenti = [
  { id: 1, email: 'admin@example.com', password_hash: hash, ruolo: 'admin', socio_id: null },
  { id: 2, email: 'operatore@example.com', password_hash: hash, ruolo: 'operatore', socio_id: null },
  { id: 3, email: 'socio1@example.com', password_hash: hash, ruolo: 'socio', socio_id: 1 },
];
const impianti = [
  { id: 1, nome: 'Tetto municipio', comune: 'Alba', lat: 44.7, lon: 8.03, kwp: 45.6,
    data_attivazione: '2023-04-01', anomalie_aperte: 0 },
];

function dbFinto({ giu = false } = {}) {
  return {
    async query(sql, params = []) {
      if (giu) throw new Error('connessione rifiutata');
      if (sql.includes('FROM utente WHERE lower(email)')) {
        return { rows: utenti.filter((u) => u.email === params[0].toLowerCase()) };
      }
      if (sql.includes('FROM utente WHERE id')) {
        return { rows: utenti.filter((u) => u.id === params[0]) };
      }
      if (sql.includes('FROM impianto')) return { rows: impianti };
      return { rows: [{ '?column?': 1 }] };
    },
  };
}

const app = creaApp({ db: dbFinto(), config });

async function tokenDi(email) {
  const res = await request(app).post('/api/auth/login').send({ email, password: 'prova1234' });
  return res.body.token;
}

test('salute: ok se il DB risponde, 503 se no', async () => {
  const ok = await request(app).get('/api/salute');
  assert.equal(ok.status, 200);
  assert.deepEqual(ok.body, { stato: 'ok', database: 'ok' });

  const giu = await request(creaApp({ db: dbFinto({ giu: true }), config })).get('/api/salute');
  assert.equal(giu.status, 503);
});

test('login riuscito: token + utente senza hash della password', async () => {
  const res = await request(app)
    .post('/api/auth/login')
    .send({ email: 'Socio1@Example.com', password: 'prova1234' });
  assert.equal(res.status, 200);
  assert.ok(res.body.token);
  assert.deepEqual(res.body.utente, { id: 3, email: 'socio1@example.com', ruolo: 'socio', socio_id: 1 });
});

test('login fallito: stessa risposta per password sbagliata ed email inesistente', async () => {
  for (const credenziali of [
    { email: 'socio1@example.com', password: 'sbagliata' },
    { email: 'nessuno@example.com', password: 'prova1234' },
  ]) {
    const res = await request(app).post('/api/auth/login').send(credenziali);
    assert.equal(res.status, 401);
    assert.equal(res.body.errore.codice, 'CREDENZIALI_ERRATE');
  }
});

test('login senza campi o con JSON rotto: 400', async () => {
  const vuoto = await request(app).post('/api/auth/login').send({});
  assert.equal(vuoto.status, 400);
  assert.equal(vuoto.body.errore.codice, 'DATI_NON_VALIDI');

  const rotto = await request(app)
    .post('/api/auth/login')
    .set('Content-Type', 'application/json')
    .send('{email:');
  assert.equal(rotto.status, 400);
});

test('/api/auth/me: 401 senza token o con token falso, 200 con token valido', async () => {
  assert.equal((await request(app).get('/api/auth/me')).status, 401);

  const falso = await request(app).get('/api/auth/me').set('Authorization', 'Bearer non.un.token');
  assert.equal(falso.status, 401);

  const token = await tokenDi('operatore@example.com');
  const res = await request(app).get('/api/auth/me').set('Authorization', `Bearer ${token}`);
  assert.equal(res.status, 200);
  assert.equal(res.body.ruolo, 'operatore');
});

test('/api/impianti: 403 al socio, 200 a operatore e admin', async () => {
  const socio = await tokenDi('socio1@example.com');
  const vietato = await request(app).get('/api/impianti').set('Authorization', `Bearer ${socio}`);
  assert.equal(vietato.status, 403);
  assert.equal(vietato.body.errore.codice, 'VIETATO');

  for (const email of ['operatore@example.com', 'admin@example.com']) {
    const token = await tokenDi(email);
    const res = await request(app).get('/api/impianti').set('Authorization', `Bearer ${token}`);
    assert.equal(res.status, 200);
    assert.equal(res.body[0].nome, 'Tetto municipio');
  }
});

test('endpoint inesistente: 404 nel formato del contratto', async () => {
  const res = await request(app).get('/api/non-esiste');
  assert.equal(res.status, 404);
  assert.equal(res.body.errore.codice, 'NON_TROVATO');
});
