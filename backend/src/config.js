// Tutta la configurazione arriva dalle variabili d'ambiente (file .env nella
// radice del repo, mai committato). Se manca qualcosa di indispensabile il
// server non parte, così l'errore si vede subito e non al primo login.

function obbligatoria(nome) {
  const valore = process.env[nome];
  if (!valore) {
    throw new Error(`Manca la variabile d'ambiente ${nome}: copia .env.example in .env`);
  }
  return valore;
}

export function leggiConfig() {
  return {
    porta: Number(process.env.PORT ?? 3000),
    databaseUrl: obbligatoria('DATABASE_URL'),
    jwtSegreto: obbligatoria('JWT_SECRET'),
    jwtScadenza: process.env.JWT_SCADENZA ?? '8h',
  };
}
