import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts'
import KpiCard from '../../components/KpiCard'
import { communityEnergySeries, communityKpi } from '../../mocks/mockData'
import { formatNumber, formatShortDate } from '../../utils/formatters'

const metrics = [
  { label: 'Soci', value: communityKpi.soci, helper: 'Totale iscritti', tone: 'emerald' },
  { label: 'Impianti', value: communityKpi.impianti, helper: 'Strutture attive', tone: 'slate' },
  { label: 'kWp totali', value: communityKpi.kwp_totali, helper: 'Potenza installata', tone: 'amber' },
  { label: 'kWh prodotti', value: communityKpi.kwh_prodotti, helper: 'Produzione annuale', tone: 'green' },
  { label: 'kWh condivisi', value: communityKpi.kwh_condivisi, helper: 'Quota condivisa', tone: 'emerald' },
  { label: 'Incentivo €', value: communityKpi.incentivo_eur, helper: 'Bonus erogati', tone: 'amber', format: 'eur' },
  { label: 'CO2 evitata (kg)', value: communityKpi.co2_evitata_kg, helper: 'Riduzione ambientale', tone: 'green' },
  { label: 'Anomalie aperte', value: communityKpi.anomalie_aperte, helper: 'Monitoraggio tecnico', tone: 'slate' },
  { label: 'Segnalazioni aperte', value: communityKpi.segnalazioni_aperte, helper: 'Supporto ai soci', tone: 'amber' }
]

export default function AdminKpiPage() {
  return (
    <div className="page-stack">
      <div className="kpi-grid admin-grid">
        {metrics.map((item) => (
          <KpiCard key={item.label} label={item.label} value={item.value} helper={item.helper} tone={item.tone} format={item.format} />
        ))}
      </div>

      <section className="panel-section chart-panel">
        <div className="panel-header">
          <div>
            <p className="section-kicker">Energia comunità</p>
            <h3>Andamento dei flussi energetici</h3>
          </div>
        </div>

        <div className="chart-wrap">
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={communityEnergySeries}>
              <CartesianGrid stroke="#dfe7e5" strokeDasharray="4 4" />
              <XAxis dataKey="ts" tickFormatter={(value) => formatShortDate(value)} minTickGap={20} />
              <YAxis />
              <Tooltip formatter={(value, name) => [`${formatNumber(value, 0)} kWh`, name]} labelFormatter={(value) => formatShortDate(value)} />
              <Legend />
              <Bar dataKey="kwh_immessi" fill="#10b981" name="kWh immessi" radius={[8, 8, 0, 0]} />
              <Bar dataKey="kwh_prelevati" fill="#f59e0b" name="kWh prelevati" radius={[8, 8, 0, 0]} />
              <Bar dataKey="kwh_condivisi" fill="#047857" name="kWh condivisi" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  )
}
