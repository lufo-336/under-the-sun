import { useMemo, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts'
import { anomalie, impiantoProductionSeries, impianti } from '../../mocks/mockData'
import { formatDateTime, formatShortDate } from '../../utils/formatters'
import StatusBadge from '../../components/StatusBadge'

export default function OperatoreImpiantiPage() {
  const [selectedImpiantoId, setSelectedImpiantoId] = useState(impianti[0]?.id ?? '')
  const [anomalieState, setAnomalieState] = useState(anomalie)

  const selectedImpianto = impianti.find((impianto) => impianto.id === selectedImpiantoId) ?? impianti[0]
  const chartData = impiantoProductionSeries[selectedImpiantoId] ?? []

  const impiantoAnomalie = useMemo(
    () => anomalieState.filter((item) => item.impianto_id === selectedImpiantoId),
    [anomalieState, selectedImpiantoId]
  )

  const handleCloseAnomalia = (id) => {
    setAnomalieState((prev) =>
      prev.map((item) => (item.id === id ? { ...item, stato: 'chiusa', fine: new Date().toISOString() } : item))
    )
  }

  return (
    <div className="page-stack">
      <section className="panel-section">
        <div className="panel-header">
          <div>
            <p className="section-kicker">Impianti comunitari</p>
            <h3>Panoramica operativa</h3>
          </div>
        </div>

        <div className="plant-grid">
          {impianti.map((impianto) => (
            <button
              key={impianto.id}
              type="button"
              className={`plant-card ${selectedImpiantoId === impianto.id ? 'selected' : ''}`}
              onClick={() => setSelectedImpiantoId(impianto.id)}
            >
              <div className="plant-card-top">
                <strong>{impianto.nome}</strong>
                <StatusBadge status={impianto.anomalie_aperte > 0 ? 'aperta' : 'chiusa'} />
              </div>
              <span>{impianto.comune}</span>
              <small>{impianto.kwp} kWp</small>
              <small>{impianto.anomalie_aperte} anomalie aperte</small>
            </button>
          ))}
        </div>
      </section>

      {selectedImpianto && (
        <>
          <section className="panel-section chart-panel">
            <div className="panel-header">
              <div>
                <p className="section-kicker">Produzione</p>
                <h3>{selectedImpianto.nome}</h3>
              </div>
              <span className="muted-text">{selectedImpianto.comune}</span>
            </div>

            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid stroke="#dfe7e5" strokeDasharray="4 4" />
                  <XAxis dataKey="ts" tickFormatter={(value) => formatShortDate(value)} minTickGap={15} />
                  <YAxis />
                  <Tooltip formatter={(value, name) => [`${value} kWh`, name === 'kwh' ? 'Reale' : 'Prevista']} labelFormatter={(value) => formatShortDate(value)} />
                  <Legend />
                  <Line type="monotone" dataKey="kwh" stroke="#10b981" strokeWidth={3} name="kwh reale" />
                  <Line type="monotone" dataKey="kwh_previsti" stroke="#f59e0b" strokeWidth={2} name="kwh previsti" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="panel-section">
            <div className="panel-header">
              <div>
                <p className="section-kicker">Anomalie</p>
                <h3>Segnalazioni impianto</h3>
              </div>
            </div>

            <div className="anomaly-list">
              {impiantoAnomalie.map((item) => (
                <article key={item.id} className="anomaly-card">
                  <div className="ticket-meta-row">
                    <strong>{item.tipo}</strong>
                    <StatusBadge status={item.stato} />
                  </div>
                  <div className="anomaly-meta">
                    <span>Score: {item.score}</span>
                    <span>Inizio: {formatDateTime(item.inizio)}</span>
                    {item.fine && <span>Chiusura: {formatDateTime(item.fine)}</span>}
                  </div>
                  {item.stato === 'aperta' && (
                    <button type="button" className="secondary-button" onClick={() => handleCloseAnomalia(item.id)}>
                      Chiudi anomalia
                    </button>
                  )}
                </article>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  )
}
