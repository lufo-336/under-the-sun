import apiClient from './apiClient'
import { impianti as impiantiDemo } from '../mocks/mockData'

// GET /api/impianti è l'unico endpoint "dati" già esposto dal backend.
// Se la risposta non è un elenco (es. modalità demo senza backend) torniamo
// ai mock segnalandolo con `demo: true`, così la pagina non mostra dati falsi
// spacciandoli per reali. Gli errori veri dell'API (401, 403, 500) restano
// errori: non vanno nascosti dietro ai mock.
export const impiantiService = {
  elenco: async () => {
    try {
      const dati = await apiClient.get('/impianti')

      if (!Array.isArray(dati)) {
        return { dati: impiantiDemo, demo: true }
      }

      return { dati, demo: false }
    } catch (errore) {
      if (errore?.status) throw errore
      return { dati: impiantiDemo, demo: true }
    }
  }
}

export default impiantiService
