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
import { CheckCircle2, MapPin, Sun, TriangleAlert } from 'lucide-react'
import Panel from '../../components/Panel'
import StatusBadge from '../../components/StatusBadge'
import { anomalie, impiantoProductionSeries, impianti } from '../../mocks/mockData'
import { formatDateTime, formatShortDate } from '../../utils/formatters'

function health(openCount) {
  if (openCount === 0) return { label: 'Ottimo', style: 'bg-success-soft text-primary' }
  if (openCount <= 2) return { label: 'Attenzione', style: 'bg-accent-soft text-accent-strong' }
  return { label: 'Critico', style: 'bg-destructive-soft text-destructive-foreground' }
}

export default function OperatoreImpiantiPage() {
  const [selectedImpiantoId, setSelectedImpiantoId] = useState(impianti[0]?.id ?? '')
  const [anomalieState, setAnomalieState] = useState(anomalie)

  const selectedImpianto = impianti.find((impianto) => Number(impianto.id) === Number(selectedImpiantoId)) ?? impianti[0]
  const chartData = impiantoProductionSeries[Number(selectedImpiantoId)] ?? []

  const impiantoAnomalie = useMemo(
    () => anomalieState
      .filter((item) => Number(item.impianto_id) === Number(selectedImpiantoId))
      .sort((a, b) => {
        const order = { aperta: 0, in_corso: 1, chiusa: 2 }
        return (order[a.stato] ?? 3) - (order[b.stato] ?? 3)
      }),
    [anomalieState, selectedImpiantoId]
  )

  const handleCloseAnomalia = (id) => {
    setAnomalieState((prev) =>
      prev.map((item) => (item.id === id ? { ...item, stato: 'chiusa' } : item))
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {impianti.map((impianto) => {
          const openCount = anomalieState.filter((item) => Number(item.impianto_id) === Number(impianto.id) && item.stato === 'aperta').length
          const state = health(openCount)
          return (
            <button
              key={impianto.id}
              type="button"
              onClick={() => setSelectedImpiantoId(Number(impianto.id))}
              className={`rounded-2xl border bg-card p-5 text-left shadow-soft transition hover:-translate-y-0.5 ${Number(selectedImpiantoId) === Number(impianto.id) ? 'border-primary ring-2 ring-primary/20' : 'border-border'}`}
            >
              <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-2">
                <p className="truncate font-bold text-foreground">{impianto.nome}</p>
                <span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${state.style}`}>{state.label}</span>
              </div>
              <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground"><MapPin className="h-3 w-3" aria-hidden="true" />{impianto.comune}</p>
              <div className="mt-4 flex flex-wrap gap-4 text-sm tabular-nums">
                <span className="flex items-center gap-1.5 font-semibold text-foreground"><Sun className="h-4 w-4 text-accent" aria-hidden="true" />{impianto.kwp} kWp</span>
                <span className="flex items-center gap-1.5 text-muted-foreground"><TriangleAlert className="h-4 w-4" aria-hidden="true" />{openCount} anomalie aperte</span>
              </div>
            </button>
          )
        })}
      </div>

      {selectedImpianto && (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
          <Panel eyebrow="Produzione" title={selectedImpianto.nome}>
            <div className="-ml-2 h-[300px] w-full">
              <ResponsiveContainer>
                <LineChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid stroke="var(--border)" strokeDasharray="4 4" vertical={false} />
                  <XAxis dataKey="ts" tickFormatter={formatShortDate} tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} minTickGap={20} />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--muted-foreground)' }} axisLine={false} tickLine={false} width={48} />
                  <Tooltip
                    formatter={(value, name) => [`${value} kWh`, name === 'kwh' ? 'Reale' : 'Prevista']}
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

          <Panel eyebrow="Anomalie" title="Segnalazioni impianto">
            <ul className="space-y-3">
              {impiantoAnomalie.map((item) => (
                <li key={item.id} className={`rounded-xl border border-border p-4 ${item.stato === 'chiusa' ? 'bg-muted/50' : ''}`}>
                  <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-2">
                    <p className="font-semibold text-foreground">{item.tipo || 'Tipo non identificato'}</p>
                    <StatusBadge status={item.stato} />
                  </div>
                  <div className="mt-3 flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
                      <div className="h-full rounded-full bg-gradient-sun" style={{ width: `${Math.min(100, Math.max(0, Number(item.score ?? 0) * 100))}%` }} />
                    </div>
                    <span className="text-xs font-bold text-foreground tabular-nums">Score {Number(item.score ?? 0).toFixed(2)}</span>
                  </div>
                  <p className="mt-2 text-xs text-muted-foreground tabular-nums">Inizio {formatDateTime(item.inizio)}{item.fine && ` · Chiusura ${formatDateTime(item.fine)}`}</p>
                  {item.stato === 'aperta' && (
                    <button
                      type="button"
                      onClick={() => handleCloseAnomalia(item.id)}
                      className="mt-3 inline-flex h-9 w-full items-center justify-center gap-2 rounded-lg bg-secondary px-3 text-sm font-semibold text-secondary-foreground transition hover:bg-secondary/80"
                    >
                      <CheckCircle2 className="h-4 w-4" aria-hidden="true" /> Chiudi anomalia
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </Panel>
        </div>
      )}
    </div>
  )
}
