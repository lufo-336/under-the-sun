// Formato degli errori fissato in docs/api.md:
// status HTTP corretto + { "errore": { "codice": "NON_TROVATO", "messaggio": "..." } }

export class ErroreApi extends Error {
  constructor(status, codice, messaggio) {
    super(messaggio);
    this.status = status;
    this.codice = codice;
  }
}

export const nonAutenticato = (messaggio = 'Serve il login') =>
  new ErroreApi(401, 'NON_AUTENTICATO', messaggio);

export const vietato = (messaggio = 'Non hai i permessi per questa risorsa') =>
  new ErroreApi(403, 'VIETATO', messaggio);

export const datiNonValidi = (messaggio) => new ErroreApi(400, 'DATI_NON_VALIDI', messaggio);

export function percorsoNonTrovato(req, res, next) {
  next(new ErroreApi(404, 'NON_TROVATO', `Nessun endpoint ${req.method} ${req.path}`));
}

// Ultimo middleware di Express: trasforma qualunque errore nel formato del contratto.
// eslint-disable-next-line no-unused-vars
export function gestoreErrori(err, req, res, next) {
  if (err instanceof ErroreApi) {
    return res.status(err.status).json({ errore: { codice: err.codice, messaggio: err.message } });
  }
  // JSON malformato nel corpo della richiesta (lo segnala express.json)
  if (err.type === 'entity.parse.failed') {
    return res
      .status(400)
      .json({ errore: { codice: 'DATI_NON_VALIDI', messaggio: 'Il corpo non è JSON valido' } });
  }
  console.error(err);
  res.status(500).json({ errore: { codice: 'ERRORE_INTERNO', messaggio: 'Errore interno del server' } });
}
