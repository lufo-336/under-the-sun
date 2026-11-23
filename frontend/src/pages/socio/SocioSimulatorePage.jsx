import { useMemo, useState } from 'react'
import { ArrowRight, Euro, Leaf, Sparkles, Zap } from 'lucide-react'
import Panel from '../../components/Panel'
import { socioSummary } from '../../mocks/mockData'
import { formatCurrency } from '../../utils/formatters'

const formatLocalNumber = (value) => new Intl.NumberFormat('it-IT', {
  useGrouping: 'always',
  maximumFractionDigits: 0
}).format(Number(value ?? 0))

export default function SocioSimulatorePage() {
  const [form, setForm] = useState({
    consumo_annuo_kwh: 3200,
    quota_spostata_ore_diurne_pct: 20
  })

  const result = useMemo(() => {
    const consumo = Number(form.consumo_annuo_kwh || 0)
    const quota = Number(form.quota_spostata_ore_diurne_pct || 0)
    const kwh_condivisi_stimati = Math.round((consumo * quota) / 100 * 0.62)
    const incentivo_eur_stimato = Number((kwh_condivisi_stimati * 0.31).toFixed(2))
    const co2_evitata_kg_stimata = Math.round(kwh_condivisi_stimati * 1.78)

    return {
      kwh_condivisi_stimati,
      incentivo_eur_stimato,
      co2_evitata_kg_stimata,
      confronto_attuale: {
        kwh_condivisi: socioSummary.kwh_condivisi,
        incentivo_eur: socioSummary.incentivo_eur
      }
    }
  }, [form])

  const handleChange = (event) => {
    const { name, value } = event.target
    const numericValue = Number(value)
    setForm((prev) => ({ ...prev, [name]: Number.isFinite(numericValue) ? numericValue : 0 }))
  }

  const rows = [
    { icon: Zap, label: 'kWh condivisi', current: `${formatLocalNumber(result.confronto_attuale.kwh_condivisi)} kWh`, estimated: `${formatLocalNumber(result.kwh_condivisi_stimati)} kWh` },
    { icon: Euro, label: 'Incentivo', current: `${formatCurrency(result.confronto_attuale.incentivo_eur)}/anno`, estimated: `${formatCurrency(result.incentivo_eur_stimato)}/anno` },
    { icon: Leaf, label: 'CO2 evitata', current: `${formatLocalNumber(socioSummary.co2_evitata_kg)} kg`, estimated: `${formatLocalNumber(result.co2_evitata_kg_stimata)} kg` }
  ]

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
      <Panel eyebrow="Parametri" title="Il tuo scenario">
        <div className="space-y-7">
          <label className="grid gap-2 text-sm font-medium text-foreground">
            Consumo annuo (kWh)
            <input
              type="number"
              name="consumo_annuo_kwh"
              min={0}
              max={20000}
              value={form.consumo_annuo_kwh}
              onChange={handleChange}
              className="h-11 rounded-xl border border-input bg-background px-3 text-base tabular-nums"
            />
          </label>
          <div className="space-y-4">
            <div className="flex items-end justify-between gap-3">
              <label htmlFor="quota-spostata" className="text-sm font-medium text-foreground">Quota spostata nelle ore diurne</label>
              <span className="text-2xl font-extrabold text-primary tabular-nums">{form.quota_spostata_ore_diurne_pct}%</span>
            </div>
            <input
              id="quota-spostata"
              type="range"
              name="quota_spostata_ore_diurne_pct"
              min={0}
              max={100}
              value={form.quota_spostata_ore_diurne_pct}
              onChange={handleChange}
              className="h-2 w-full cursor-pointer accent-primary"
            />
            <div className="flex justify-between text-xs text-muted-foreground tabular-nums"><span>0%</span><span>50%</span><span>100%</span></div>
          </div>
        </div>
      </Panel>

      <Panel eyebrow="Confronto" title="Attuale vs stimato">
        <div className="mb-5 flex items-center gap-3 rounded-2xl bg-gradient-sun p-4 text-primary-foreground shadow-glow">
          <Sparkles className="h-6 w-6 shrink-0" aria-hidden="true" />
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase tracking-wide opacity-90">Incentivo annuo stimato</p>
            <p className="text-2xl font-extrabold tabular-nums">{formatCurrency(result.incentivo_eur_stimato)}</p>
          </div>
        </div>
        <div className="space-y-3">
          {rows.map(({ icon: Icon, label, current, estimated }) => (
            <div key={label} className="rounded-2xl border border-border bg-background p-4">
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="flex items-center gap-2 text-sm font-semibold text-foreground"><Icon className="h-4 w-4 text-primary" aria-hidden="true" />{label}</p>
              </div>
              <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] items-center gap-3 tabular-nums">
                <div><p className="text-[11px] uppercase text-muted-foreground">Attuale</p><p className="font-semibold text-muted-foreground">{current}</p></div>
                <ArrowRight className="h-4 w-4 text-accent" aria-hidden="true" />
                <div><p className="text-[11px] uppercase text-muted-foreground">Stimato</p><p className="text-lg font-extrabold text-foreground">{estimated}</p></div>
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </div>
  )
}
