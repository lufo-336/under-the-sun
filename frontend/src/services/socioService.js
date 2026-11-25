import apiClient from './apiClient'
import { consumoSerie, socioSummary } from '../mocks/mockData'

// L'area socio (/api/me/*) non è ancora esposta dal backend: la issue #14
// aggiunge /api/me/riepilogo e /api/me/consumi. Finché la rotta manca
// rispondiamo con i mock e `demo: true`, così la pagina lo può dire
// all'utente. Un 404 NON_TROVATO significa "endpoint non ancora implementato";
// tutti gli altri errori (401, 403, 500) restano errori veri.
const endpointNonDisponibile = (errore) =>
  !errore?.status || (errore.status === 404 && errore.codice === 'NON_TROVATO')

const conFallback = async (richiesta, datiDemo, valido = () => true) => {
  try {
    const dati = await richiesta()

    if (!valido(dati)) {
      return { dati: datiDemo, demo: true }
    }

    return { dati, demo: false }
  } catch (errore) {
    if (endpointNonDisponibile(errore)) {
      return { dati: datiDemo, demo: true }
    }
    throw errore
  }
}

const isOggetto = (dati) => dati !== null && typeof dati === 'object' && !Array.isArray(dati)

export const socioService = {
  riepilogo: (anno) => conFallback(
    () => apiClient.get(`/me/riepilogo?anno=${anno}`),
    { ...socioSummary, anno },
    isOggetto
  ),
  consumi: ({ da, a, granularita }) => conFallback(
    () => apiClient.get(`/me/consumi?${new URLSearchParams({ da, a, granularita })}`),
    consumoSerie,
    Array.isArray
  )
}

export default socioService
