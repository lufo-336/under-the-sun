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
import { Euro, Leaf, PlugZap, Zap } from 'lucide-react'
import KpiCard from '../../components/KpiCard'
import Panel from '../../components/Panel'
import socioService from '../../services/socioService'
import { formatShortDate } from '../../utils/formatters'

const granularities = ['ora', 'giorno', 'mese']

const messaggioErrore = (errore) => {
  if (errore?.status === 403) return 'Non hai i permessi per vedere questi dati.'
  return errore?.message || 'Impossibile caricare i dati della dashboard.'
}

export default function SocioDashboardPage() {
  const [selectedYear, setSelectedYear] = useState(2026)
  const [granularity, setGranularity] = useState('giorno')
  const [riepilogo, setRiepilogo] = useState(null)
  const [consumi, setConsumi] = useState([])
  const [riepilogoDemo, setRiepilogoDemo] = useState(false)
  const [consumiDemo, setConsumiDemo] = useState(false)
  const [caricamento, setCaricamento] = useState(true)
  const [errore, setErrore] = useState('')
  const [tentativo, setTentativo] = useState(0)

  useEffect(() => {
    let attivo = true
    const da = `${selectedYear}-01-01`
    const a = `${selectedYear + 1}-01-01`

    Promise.all([
      socioService.riepilogo(selectedYear),
      socioService.consumi({ da, a, granularita: granularity })
    ])
      .then(([rispostaRiepilogo, rispostaConsumi]) => {
        if (!attivo) return
        setRiepilogo(rispostaRiepilogo.dati)
        setConsumi(rispostaConsumi.dati)
        setRiepilogoDemo(Boolean(rispostaRiepilogo.demo))
        setConsumiDemo(Boolean(rispostaConsumi.demo))
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
  }, [selectedYear, granularity, tentativo])

  const ricarica = () => {
    setCaricamento(true)
    setErrore('')
    setTentativo((corrente) => corrente + 1)
  }

  const cambiaAnno = (anno) => {
    setCaricamento(true)
    setErrore('')
    setSelectedYear(anno)
  }

  const cambiaGranularita = (valore) => {
    if (valore === granularity) return
    setCaricamento(true)
    setErrore('')
    setGranularity(valore)
  }

  // Con i dati veri la granularità la calcola il backend; sui mock, che sono
  // una serie giornaliera, la ricampioniamo per far vedere le tre viste.
  const chartData = useMemo(() => {
    if (!consumiDemo) return consumi
    const ratio = granularity === 'ora' ? 1 : granularity === 'giorno' ? 2 : 4
    return consumi.filter((_, index) => index % ratio === 0)
  }, [consumi, consumiDemo, granularity])

  const kpis = riepilogo
    ? [
        { label: 'kWh condivisi', value: riepilogo.kwh_condivisi, helper: 'Quota CER attiva', tone: 'green', icon: Zap },
        { label: 'Incentivo maturato (€)', value: riepilogo.incentivo_eur, helper: `Anno ${riepilogo.anno ?? selectedYear}`, tone: 'sun', icon: Euro, format: 'eur' },
        { label: 'CO2 evitata (kg)', value: riepilogo.co2_evitata_kg, helper: 'Riduzione stimata', tone: 'green', icon: Leaf },
        { label: 'Totale kWh consumati', value: riepilogo.kwh_consumati, helper: "Consumi dell'anno", tone: 'slate', icon: PlugZap }
      ]
    : []

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <label className="grid min-w-32 gap-1.5 text-xs font-semibold text-muted-foreground">
          Anno
          <select
            value={selectedYear}
            onChange={(event) => cambiaAnno(Number(event.target.value))}
            disabled={caricamento}
            className="h-10 rounded-xl border border-input bg-card px-3 text-sm text-foreground disabled:opacity-60"
          >
            <option value={2026}>2026</option>
            <option value={2025}>2025</option>
          </select>
        </label>
      </div>

      {riepilogoDemo && !caricamento && !errore && (
        <p role="status" className="rounded-xl bg-accent-soft px-3 py-2 text-sm font-semibold text-accent-strong">
          Dati di esempio: il backend non espone ancora gli endpoint dell'area socio.
        </p>
      )}

      {errore && (
        <div className="rounded-2xl border border-border bg-card p-6 shadow-soft">
          <p role="alert" className="rounded-xl bg-destructive-soft px-3 py-2 text-sm font-semibold text-destructive-foreground">{errore}</p>
          <button
            type="button"
            onClick={ricarica}
            className="mt-4 h-10 rounded-xl bg-secondary px-4 text-sm font-semibold text-secondary-foreground transition hover:bg-secondary/80"
          >
            Riprova
          </button>
        </div>
      )}

      {caricamento && (
        <div role="status" className="rounded-2xl border border-border bg-card p-6 text-sm text-muted-foreground shadow-soft">
          Caricamento dati…
        </div>
      )}

      {!caricamento && !errore && riepilogo && (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {kpis.map((item) => <KpiCard key={item.label} {...item} />)}
          </div>

          <Panel
            eyebrow={`Andamento consumo ${selectedYear}`}
            title="Consumo reale vs previsto"
            action={
              <div className="flex flex-wrap items-center justify-end gap-2">
                {consumiDemo && (
                  <span className="rounded-full bg-muted px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-muted-foreground">Dati di esempio</span>
                )}
                <div className="flex rounded-full bg-muted p-1">
                  {granularities.map((value) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => cambiaGranularita(value)}
                      className={`rounded-full px-3 py-1 text-xs font-semibold capitalize transition ${granularity === value ? 'bg-card text-foreground shadow-soft' : 'text-muted-foreground hover:text-foreground'}`}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>
            }
          >
            {chartData.length === 0 && (
              <p className="text-sm text-muted-foreground">Nessun consumo disponibile per questo periodo.</p>
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
        </>
      )}
    </div>
  )
}
