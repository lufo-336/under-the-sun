import { useMemo, useState } from 'react'
import { impianti, segnalazioni } from '../../mocks/mockData'
import { formatDateTime } from '../../utils/formatters'
import StatusBadge from '../../components/StatusBadge'

const initialSegnalazioni = segnalazioni.filter((item) => item.id === 'SEG-101' || item.id === 'SEG-102' || item.id === 'SEG-103')

export default function SocioSegnalazioniPage() {
  const [form, setForm] = useState({ testo: '', impianto_id: impianti[0]?.id || '' })
  const [items, setItems] = useState(initialSegnalazioni)

  const handleSubmit = (event) => {
    event.preventDefault()

    if (!form.testo.trim()) return

    const newItem = {
      id: `SEG-${Date.now()}`,
      ts: new Date().toISOString(),
      canale: 'web',
      testo: form.testo.trim(),
      impianto_id: form.impianto_id || null,
      categoria: 'generale',
      urgenza: 'media',
      stato: 'aperta'
    }

    setItems((prev) => [newItem, ...prev])
    setForm({ testo: '', impianto_id: impianti[0]?.id || '' })
  }

  const list = useMemo(() => [...items].sort((a, b) => new Date(b.ts) - new Date(a.ts)), [items])

  return (
    <div className="page-stack">
      <section className="panel-section">
        <div className="panel-header">
          <div>
            <p className="section-kicker">Segnalazioni</p>
            <h3>Invia una nuova comunicazione</h3>
          </div>
        </div>

        <form className="ticket-form" onSubmit={handleSubmit}>
          <label>
            <span>Dettaglio segnalazione</span>
            <textarea
              value={form.testo}
              onChange={(event) => setForm((prev) => ({ ...prev, testo: event.target.value }))}
              rows={4}
              placeholder="Descrivi il problema o la richiesta..."
            />
          </label>

          <label>
            <span>Impianto collegato</span>
            <select
              value={form.impianto_id}
              onChange={(event) => setForm((prev) => ({ ...prev, impianto_id: event.target.value }))}
            >
              <option value="">Nessun impianto</option>
              {impianti.map((impianto) => (
                <option key={impianto.id} value={impianto.id}>
                  {impianto.nome}
                </option>
              ))}
            </select>
          </label>

          <button type="submit" className="primary-button">
            Invia segnalazione
          </button>
        </form>
      </section>

      <section className="panel-section">
        <div className="panel-header">
          <div>
            <p className="section-kicker">Storico</p>
            <h3>Le tue segnalazioni</h3>
          </div>
        </div>

        <div className="ticket-list">
          {list.map((item) => (
            <article key={item.id} className="ticket-card">
              <div className="ticket-meta-row">
                <span>{formatDateTime(item.ts)}</span>
                <StatusBadge status={item.stato} />
              </div>

              <p className="ticket-text">{item.testo}</p>

              <div className="ticket-foot">
                <span>
                  {item.impianto_id
                    ? `Impianto: ${impianti.find((impianto) => impianto.id === item.impianto_id)?.nome || item.impianto_id}`
                    : 'Segnalazione generale'}
                </span>
                <span className="muted-text">{item.canale?.toUpperCase()}</span>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
