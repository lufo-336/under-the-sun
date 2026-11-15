import { useMemo, useState } from 'react'
import { impianti, segnalazioni } from '../../mocks/mockData'
import { formatDateTime } from '../../utils/formatters'
import StatusBadge from '../../components/StatusBadge'
import UrgencyBadge from '../../components/UrgencyBadge'

const urgencyOrder = { alta: 3, media: 2, bassa: 1 }

export default function OperatoreSegnalazioniPage() {
  const [filters, setFilters] = useState({ stato: 'tutte', urgenza: 'tutte', categoria: 'tutte' })
  const [items, setItems] = useState(segnalazioni)

  const filteredItems = useMemo(() => {
    return [...items]
      .filter((item) => (filters.stato === 'tutte' ? true : item.stato === filters.stato))
      .filter((item) => (filters.urgenza === 'tutte' ? true : item.urgenza === filters.urgenza))
      .filter((item) => (filters.categoria === 'tutte' ? true : item.categoria === filters.categoria))
      .sort((a, b) => urgencyOrder[b.urgenza] - urgencyOrder[a.urgenza])
  }, [items, filters])

  const handleFieldChange = (id, field, value) => {
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, [field]: value } : item)))
  }

  const handleClose = (id) => {
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, stato: 'chiusa' } : item)))
  }

  return (
    <div className="page-stack">
      <section className="panel-section">
        <div className="panel-header">
          <div>
            <p className="section-kicker">Queue segnalazioni</p>
            <h3>Gestione custodia e priorità</h3>
          </div>
        </div>

        <div className="filters-row">
          <label>
            <span>Stato</span>
            <select value={filters.stato} onChange={(event) => setFilters((prev) => ({ ...prev, stato: event.target.value }))}>
              <option value="tutte">Tutte</option>
              <option value="aperta">Aperte</option>
              <option value="chiusa">Chiuse</option>
            </select>
          </label>

          <label>
            <span>Urgenza</span>
            <select value={filters.urgenza} onChange={(event) => setFilters((prev) => ({ ...prev, urgenza: event.target.value }))}>
              <option value="tutte">Tutte</option>
              <option value="alta">Alta</option>
              <option value="media">Media</option>
              <option value="bassa">Bassa</option>
            </select>
          </label>

          <label>
            <span>Categoria</span>
            <select value={filters.categoria} onChange={(event) => setFilters((prev) => ({ ...prev, categoria: event.target.value }))}>
              <option value="tutte">Tutte</option>
              <option value="impianto">Impianto</option>
              <option value="billing">Billing</option>
              <option value="informazione">Informazione</option>
            </select>
          </label>
        </div>
      </section>

      <section className="panel-section">
        <div className="ticket-list stacked-list">
          {filteredItems.map((item) => (
            <article key={item.id} className="ticket-card operator-ticket">
              <div className="ticket-meta-row">
                <span>{item.id}</span>
                <StatusBadge status={item.stato} />
                <UrgencyBadge urgency={item.urgenza} />
              </div>

              <div className="ticket-grid">
                <div>
                  <p className="small-label">LLM categoria</p>
                  <strong>{item.categoria_llm}</strong>
                </div>
                <div>
                  <p className="small-label">LLM urgenza</p>
                  <strong>{item.urgenza_llm}</strong>
                </div>
                <div>
                  <p className="small-label">Data</p>
                  <strong>{formatDateTime(item.ts)}</strong>
                </div>
              </div>

              <p className="ticket-text">{item.testo}</p>

              <div className="ticket-controls">
                <label>
                  <span>Categoria</span>
                  <select value={item.categoria} onChange={(event) => handleFieldChange(item.id, 'categoria', event.target.value)}>
                    <option value="impianto">Impianto</option>
                    <option value="billing">Billing</option>
                    <option value="informazione">Informazione</option>
                  </select>
                </label>

                <label>
                  <span>Urgenza</span>
                  <select value={item.urgenza} onChange={(event) => handleFieldChange(item.id, 'urgenza', event.target.value)}>
                    <option value="alta">Alta</option>
                    <option value="media">Media</option>
                    <option value="bassa">Bassa</option>
                  </select>
                </label>

                <button type="button" className="secondary-button" onClick={() => handleClose(item.id)}>
                  Segna come chiusa
                </button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </div>
  )
}
