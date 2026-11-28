// Riepilogo annuale di un socio: consumi, energia condivisa, incentivo e CO2,
// mese per mese. Lo usa /api/me/riepilogo (il socio) e lo userà
// /api/soci/:id/riepilogo (l'admin): stessa forma di risposta per entrambi.
//
// - kwh_consumati: somma di consumo_orario nel mese (mesi in UTC, come tutto il contratto).
// - kwh_condivisi, incentivo_eur, co2_evitata_kg: da ripartizione_mensile, scritta dal batch.
//   Se il batch non ha ancora calcolato un mese valgono null (non 0: "non calcolato" ≠ "zero").
// - Un mese compare se ha consumi o ripartizione.

const SQL_MESI = `
  WITH consumi AS (
    SELECT date_trunc('month', ts AT TIME ZONE 'UTC')::date AS mese, sum(kwh) AS kwh_consumati
    FROM consumo_orario
    WHERE socio_id = $1
      AND ts >= make_timestamptz($2::int, 1, 1, 0, 0, 0, 'UTC')
      AND ts <  make_timestamptz($2::int + 1, 1, 1, 0, 0, 0, 'UTC')
    GROUP BY 1
  ),
  ripartizione AS (
    SELECT mese, kwh_condivisi, incentivo_eur, co2_evitata_kg
    FROM ripartizione_mensile
    WHERE socio_id = $1 AND extract(year FROM mese)::int = $2::int
  )
  SELECT to_char(coalesce(c.mese, r.mese), 'YYYY-MM') AS mese,
         coalesce(c.kwh_consumati, 0) AS kwh_consumati,
         r.kwh_condivisi, r.incentivo_eur, r.co2_evitata_kg
  FROM consumi c
  FULL JOIN ripartizione r ON r.mese = c.mese
  ORDER BY 1`;

const arrotonda = (valore, cifre) =>
  valore == null ? null : Math.round(valore * 10 ** cifre) / 10 ** cifre;

// Somma ignorando i null; null se nessun mese ha il valore.
function totale(mesi, campo) {
  const valori = mesi.map((m) => m[campo]).filter((v) => v != null);
  return valori.length ? valori.reduce((a, b) => a + b, 0) : null;
}

export async function riepilogoSocio(db, socioId, anno) {
  const { rows } = await db.query(SQL_MESI, [socioId, anno]);

  const formatta = (r) => ({
    kwh_consumati: arrotonda(r.kwh_consumati, 1),
    kwh_condivisi: arrotonda(r.kwh_condivisi, 1),
    incentivo_eur: arrotonda(r.incentivo_eur, 2),
    co2_evitata_kg: arrotonda(r.co2_evitata_kg, 1),
  });

  // I totali si calcolano sui valori non arrotondati, poi si arrotondano.
  return {
    anno,
    ...formatta({
      kwh_consumati: totale(rows, 'kwh_consumati') ?? 0,
      kwh_condivisi: totale(rows, 'kwh_condivisi'),
      incentivo_eur: totale(rows, 'incentivo_eur'),
      co2_evitata_kg: totale(rows, 'co2_evitata_kg'),
    }),
    mesi: rows.map((r) => ({ mese: r.mese, ...formatta(r) })),
  };
}
