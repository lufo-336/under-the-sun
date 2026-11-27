import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts'
import { BatteryCharging, Euro, Factory, Leaf, TriangleAlert, Users, Zap, Sun } from 'lucide-react'
import KpiCard from '../../components/KpiCard'
import Panel from '../../components/Panel'
import { communityEnergySeries, communityKpi } from '../../mocks/mockData'
import { formatNumber, formatShortDate } from '../../utils/formatters'

const metrics = [
  { label: 'Soci', value: communityKpi.soci, helper: 'Totale iscritti', tone: 'slate', icon: Users },
  { label: 'Impianti', value: communityKpi.impianti, helper: 'Strutture attive', tone: 'slate', icon: Factory },
  { label: 'kWp totali', value: communityKpi.kwp_totali, helper: 'Potenza installata', tone: 'sun', icon: Sun },
  { label: 'kWh prodotti', value: communityKpi.kwh_prodotti, helper: 'Produzione annuale', tone: 'green', icon: BatteryCharging },
  { label: 'kWh condivisi', value: communityKpi.kwh_condivisi, helper: 'Quota condivisa', tone: 'green', icon: Zap },
  { label: 'Incentivo €', value: communityKpi.incentivo_eur, helper: 'Bonus erogati', tone: 'sun', icon: Euro, format: 'eur' },
  { label: 'CO2 evitata (kg)', value: communityKpi.co2_evitata_kg, helper: 'Riduzione ambientale', tone: 'green', icon: Leaf },
  { label: 'Anomalie aperte', value: communityKpi.anomalie_aperte, helper: 'Monitoraggio tecnico', tone: 'sun', icon: TriangleAlert },
  { label: 'Segnalazioni aperte', value: communityKpi.segnalazioni_aperte, helper: 'Supporto ai soci', tone: 'slate', icon: TriangleAlert }
]

const series = [
  { key: 'kwh_immessi', label: 'kWh immessi', color: 'var(--chart-2)' },
  { key: 'kwh_prelevati', label: 'kWh prelevati', color: 'var(--chart-3)' },
  { key: 'kwh_condivisi', label: 'kWh condivisi', color: 'var(--chart-1)' }
]

export default function AdminKpiPage() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metrics.map((item) => <KpiCard key={item.label} {...item} />)}
      </div>

      <Panel eyebrow="Energia comunità" title="Andamento dei flussi energetici">
        <div className="-ml-2 h-[320px] w-full">
          <ResponsiveContainer>
            <AreaChart data={communityEnergySeries} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <defs>
                {series.map((item) => (
                  <linearGradient key={item.key} id={`gradient-${item.key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={item.color} stopOpacity={0.28} />
                    <stop offset="100%" stopColor={item.color} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid stroke="var(--border)" strokeDasharray="4 4" vertical={false} />
              <XAxis dataKey="ts" tickFormatter={formatShortDate} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} minTickGap={20} />
              <YAxis tickFormatter={(value) => formatNumber(value, 0)} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} width={56} />
              <Tooltip
                formatter={(value, name) => [`${formatNumber(value, 0)} kWh`, name]}
                labelFormatter={formatShortDate}
                contentStyle={{ border: '1px solid var(--border)', borderRadius: 12, boxShadow: 'var(--shadow-soft)' }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              {series.map((item) => (
                <Area key={item.key} type="monotone" dataKey={item.key} name={item.label} stroke={item.color} strokeWidth={2.5} fill={`url(#gradient-${item.key})`} dot={false} />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </div>
  )
}
