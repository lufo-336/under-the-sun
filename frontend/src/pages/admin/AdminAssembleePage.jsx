import { useState } from 'react'
import { verbali } from '../../mocks/mockData'
import { formatShortDate } from '../../utils/formatters'

export default function AdminAssembleePage() {
  const [expandedIds, setExpandedIds] = useState([])

  const handleToggle = (id) => {
    setExpandedIds((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]))
  }

  return (
    <div className="page-stack">
      <section className="panel-section">
        <div className="panel-header">
          <div>
            <p className="section-kicker">Verbali assemblee</p>
            <h3>Documentazione comunitaria</h3>
          </div>
        </div>

        <div className="assembly-list">
          {verbali.map((verbale) => {
            const isExpanded = expandedIds.includes(verbale.id)

            return (
              <article key={verbale.id} className="assembly-card">
                <div className="assembly-head">
                  <div>
                    <span className="assembly-date">{formatShortDate(verbale.data_assemblea)}</span>
                    <h4>{verbale.id}</h4>
                  </div>
                  <button type="button" className="secondary-button" onClick={() => handleToggle(verbale.id)}>
                    {isExpanded ? 'Chiudi verbale' : 'Apri verbale'}
                  </button>
                </div>

                <div className="summary-box">
                  <span>Sintesi automatica LLM</span>
                  <p>{verbale.sintesi}</p>
                </div>

                {isExpanded && <div className="full-text-box">{verbale.testo_completo}</div>}
              </article>
            )
          })}
        </div>
      </section>
    </div>
  )
}
