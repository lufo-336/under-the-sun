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
import KpiCard from '../../components/KpiCard'
import { consumoSerie, socioSummary } from '../../mocks/mockData'
import { formatShortDate } from '../../utils/formatters'

export default function SocioDashboardPage() {
  const [selectedYear, setSelectedYear] = useState(socioSummary.anno)
  const [granularity, setGranularity] = useState('giorno')

  const chartData = useMemo(() => {
    const ratio = granularity === 'ora' ? 1 : granularity === 'giorno' ? 2 : 4
    return consumoSerie.filter((_, index) => index % ratio === 0)
  }, [granularity])

  const kpis = [
    { label: 'kWh condivisi', value: socioSummary.kwh_condivisi, helper: 'Quota CER attiva', tone: 'emerald' },
    { label: 'Incentivo maturato (€)', value: socioSummary.incentivo_eur, helper: 'Anno 2026', tone: 'amber', format: 'eur' },
    { label: 'CO2 evitata (kg)', value: socioSummary.co2_evitata_kg, helper: 'Riduzione stimata', tone: 'green' },
    { label: 'Totale kWh consumati', value: socioSummary.kwh_consumati, helper: 'Consumi dell’anno', tone: 'slate' }
  ]

  return (
    <div className="page-stack">
      <div className="toolbar-panel">
        <div className="field-group">
          <label htmlFor="anno-socio">Anno</label>
          <select id="anno-socio" value={selectedYear} onChange={(event) => setSelectedYear(Number(event.target.value))}>
            <option value={2026}>2026</option>
            <option value={2025}>2025</option>
          </select>
        </div>

        <div className="field-group">
          <label htmlFor="granularity-socio">Granularità</label>
          <select id="granularity-socio" value={granularity} onChange={(event) => setGranularity(event.target.value)}>
            <option value="ora">Ora</option>
            <option value="giorno">Giorno</option>
            <option value="mese">Mese</option>
          </select>
        </div>
      </div>

      <div className="kpi-grid four-columns">
        {kpis.map((item) => (
          <KpiCard
            key={item.label}
            label={item.label}
            value={item.value}
            helper={item.helper}
            tone={item.tone}
            format={item.format}
          />
        ))}
      </div>

      <section className="panel-section chart-panel">
        <div className="panel-header">
          <div>
            <p className="section-kicker">Andamento consumo 2026</p>
            <h3>Confronto consumo reale vs previsto</h3>
          </div>
          <span className="muted-text">Picco anomalo rilevato il 15/10</span>
        </div>

        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={chartData}>
              <CartesianGrid stroke="#dfe7e5" strokeDasharray="4 4" />
              <XAxis dataKey="ts" tickFormatter={(value) => formatShortDate(value)} minTickGap={20} />
              <YAxis tickFormatter={(value) => `${value} kWh`} />
              <Tooltip
                formatter={(value, name) => [`${value} kWh`, name === 'kwh' ? 'Consumo reale' : 'Previsto']}
                labelFormatter={(value) => formatShortDate(value)}
              />
              <Legend />
              <Line type="monotone" dataKey="kwh" stroke="#10b981" strokeWidth={3} name="kwh reale" />
              <Line type="monotone" dataKey="kwh_previsti" stroke="#f59e0b" strokeWidth={2} name="kwh previsti" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  )
}
