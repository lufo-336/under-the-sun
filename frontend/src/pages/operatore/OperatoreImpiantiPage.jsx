import { useEffect, useMemo, useState } from 'react'
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
import { anomalie, impiantoProductionSeries } from '../../mocks/mockData'
import impiantiService from '../../services/impiantiService'
import { formatDateTime, formatShortDate } from '../../utils/formatters'

const badgeDatiEsempio = (
  <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-muted-foreground">Dati di esempio</span>
)

const messaggioErrore = (errore) => {
  if (errore?.status === 403) return 'Non hai i permessi per vedere gli impianti.'
  if (errore?.status === 401) return 'Sessione scaduta: accedi di nuovo.'
  return errore?.message || 'Impossibile caricare gli impianti.'
}

function health(openCount) {
  if (openCount === 0) return { label: 'Ottimo', style: 'bg-success-soft text-primary' }
  if (openCount <= 2) return { label: 'Attenzione', style: 'bg-accent-soft text-accent-strong' }
  return { label: 'Critico', style: 'bg-destructive-soft text-destructive-foreground' }
}

export default function OperatoreImpiantiPage() {
  const [impianti, setImpianti] = useState([])
  const [selectedImpiantoId, setSelectedImpiantoId] = useState('')
  const [anomalieState, setAnomalieState] = useState(anomalie)
  const [caricamento, setCaricamento] = useState(true)
  const [errore, setErrore] = useState('')
  const [datiDemo, setDatiDemo] = useState(false)
  const [tentativo, setTentativo] = useState(0)

  useEffect(() => {
    let attivo = true

    impiantiService.elenco()
      .then(({ dati, demo }) => {
        if (!attivo) return
        setImpianti(dati)
        setDatiDemo(demo)
        setSelectedImpiantoId((corrente) => (
          dati.some((impianto) => Number(impianto.id) === Number(corrente))
            ? corrente
            : dati[0]?.id ?? ''
        ))
        setCaricamento(false)
      })
      .catch((requestError) => {
        if (!attivo) return
        setErrore(messaggioErrore(requestError))
        setCaricamento(false)
      })

    return () => {
      attivo = false
    }
  }, [tentativo])

  const ricaricaImpianti = () => {
    setCaricamento(true)
    setErrore('')
    setTentativo((corrente) => corrente + 1)
  }

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

  if (caricamento) {
    return (
      <div role="status" className="rounded-2xl border border-border bg-card p-6 text-sm text-muted-foreground shadow-soft">
        Caricamento impianti…
      </div>
    )
  }

  if (errore) {
    return (
      <div className="rounded-2xl border border-border bg-card p-6 shadow-soft">
        <p role="alert" className="rounded-xl bg-destructive-soft px-3 py-2 text-sm font-semibold text-destructive-foreground">{errore}</p>
        <button
          type="button"
          onClick={ricaricaImpianti}
          className="mt-4 h-10 rounded-xl bg-secondary px-4 text-sm font-semibold text-secondary-foreground transition hover:bg-secondary/80"
        >
          Riprova
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {datiDemo && (
        <p role="status" className="rounded-xl bg-accent-soft px-3 py-2 text-sm font-semibold text-accent-strong">
          Elenco impianti di esempio: il backend non ha risposto.
        </p>
      )}

      {impianti.length === 0 && (
        <p className="rounded-2xl border border-border bg-card p-6 text-sm text-muted-foreground shadow-soft">
          Nessun impianto disponibile.
        </p>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {impianti.map((impianto) => {
          const openCount = datiDemo
            ? anomalieState.filter((item) => Number(item.impianto_id) === Number(impianto.id) && item.stato === 'aperta').length
            : Number(impianto.anomalie_aperte ?? 0)
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
          <Panel eyebrow="Produzione" title={selectedImpianto.nome} action={badgeDatiEsempio}>
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

          <Panel eyebrow="Anomalie" title="Segnalazioni impianto" action={badgeDatiEsempio}>
            {impiantoAnomalie.length === 0 && (
              <p className="text-sm text-muted-foreground">Nessuna anomalia registrata per questo impianto.</p>
            )}
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
