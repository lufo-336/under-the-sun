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
import { Euro, Leaf, PlugZap, Zap } from 'lucide-react'
import KpiCard from '../../components/KpiCard'
import Panel from '../../components/Panel'
import { consumoSerie, socioSummary } from '../../mocks/mockData'
import { formatShortDate } from '../../utils/formatters'

const granularities = ['ora', 'giorno', 'mese']

export default function SocioDashboardPage() {
  const [selectedYear, setSelectedYear] = useState(socioSummary.anno)
  const [granularity, setGranularity] = useState('giorno')

  const chartData = useMemo(() => {
    const ratio = granularity === 'ora' ? 1 : granularity === 'giorno' ? 2 : 4
    return consumoSerie.filter((_, index) => index % ratio === 0)
  }, [granularity])

  const kpis = [
    { label: 'kWh condivisi', value: socioSummary.kwh_condivisi, helper: 'Quota CER attiva', tone: 'green', icon: Zap },
    { label: 'Incentivo maturato (€)', value: socioSummary.incentivo_eur, helper: `Anno ${selectedYear}`, tone: 'sun', icon: Euro, format: 'eur' },
    { label: 'CO2 evitata (kg)', value: socioSummary.co2_evitata_kg, helper: 'Riduzione stimata', tone: 'green', icon: Leaf },
    { label: 'Totale kWh consumati', value: socioSummary.kwh_consumati, helper: "Consumi dell'anno", tone: 'slate', icon: PlugZap }
  ]

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <label className="grid min-w-32 gap-1.5 text-xs font-semibold text-muted-foreground">
          Anno
          <select
            value={selectedYear}
            onChange={(event) => setSelectedYear(Number(event.target.value))}
            className="h-10 rounded-xl border border-input bg-card px-3 text-sm text-foreground"
          >
            <option value={2026}>2026</option>
            <option value={2025}>2025</option>
          </select>
        </label>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {kpis.map((item) => <KpiCard key={item.label} {...item} />)}
      </div>

      <Panel
        eyebrow={`Andamento consumo ${selectedYear}`}
        title="Consumo reale vs previsto"
        action={
          <div className="flex rounded-full bg-muted p-1">
            {granularities.map((value) => (
              <button
                key={value}
                type="button"
                onClick={() => setGranularity(value)}
                className={`rounded-full px-3 py-1 text-xs font-semibold capitalize transition ${granularity === value ? 'bg-card text-foreground shadow-soft' : 'text-muted-foreground hover:text-foreground'}`}
              >
                {value}
              </button>
            ))}
          </div>
        }
      >
        {granularity === 'giorno' && (
          <p className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-accent-soft px-3 py-1 text-xs font-semibold text-accent-strong">
            Picco anomalo rilevato il 15/10
          </p>
        )}

        <div className="-ml-2 h-[320px] w-full">
          <ResponsiveContainer>
            <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="var(--border)" strokeDasharray="4 4" vertical={false} />
              <XAxis dataKey="ts" tickFormatter={formatShortDate} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} minTickGap={20} />
              <YAxis tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} width={48} />
              <Tooltip
                formatter={(value, name) => [`${value} kWh`, name === 'kwh' ? 'Reale' : 'Previsto']}
                labelFormatter={formatShortDate}
                contentStyle={{ border: '1px solid var(--border)', borderRadius: 12, boxShadow: 'var(--shadow-soft)' }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Line type="monotone" dataKey="kwh" stroke="var(--chart-1)" strokeWidth={2.5} dot={false} name="kWh reali" />
              <Line type="monotone" dataKey="kwh_previsti" stroke="var(--chart-2)" strokeWidth={2.5} dot={false} name="kWh previsti" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </div>
  )
}
