import pg from 'pg';

// numeric (es. importo_eur, incentivo_eur) arriva da pg come stringa per non
// perdere precisione. Per i nostri importi in euro un number basta, e il
// contratto API li vuole numerici.
pg.types.setTypeParser(pg.types.builtins.NUMERIC, (valore) => Number(valore));

export function creaDb(databaseUrl) {
  return new pg.Pool({ connectionString: databaseUrl, max: 10 });
}
