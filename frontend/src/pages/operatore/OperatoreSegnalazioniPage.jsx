import { useMemo, useState } from 'react'
import { Bot, UserCheck } from 'lucide-react'
import Panel from '../../components/Panel'
import StatusBadge from '../../components/StatusBadge'
import UrgencyBadge from '../../components/UrgencyBadge'
import { segnalazioni } from '../../mocks/mockData'
import { formatDateTime } from '../../utils/formatters'

const urgencyOrder = { alta: 3, media: 2, bassa: 1 }
const stateOptions = [['aperta', 'Aperta'], ['in_corso', 'In corso'], ['chiusa', 'Chiusa']]
const urgencyOptions = [['alta', 'Alta'], ['media', 'Media'], ['bassa', 'Bassa']]
const categoryOptions = [['impianto', 'Impianto'], ['billing', 'Billing'], ['informazione', 'Informazione'], ['altro', 'Altro']]

function FilterChips({ label, value, onChange, options }) {
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-2">
      <span className="shrink-0 text-xs font-semibold text-muted-foreground">{label}</span>
      {[['tutte', 'Tutte'], ...options].map(([key, text]) => (
        <button
          key={key}
          type="button"
          onClick={() => onChange(key)}
          className={`shrink-0 rounded-full border px-3 py-1 text-xs font-semibold transition ${value === key ? 'border-primary bg-primary text-primary-foreground' : 'border-border bg-card text-muted-foreground hover:text-foreground'}`}
        >
          {text}
        </button>
      ))}
    </div>
  )
}

function ReviewSelect({ label, value, options, onChange }) {
  return (
    <label className="grid min-w-0 gap-1.5 text-xs font-semibold text-muted-foreground">
      {label}
      <select value={value ?? ''} onChange={(event) => onChange(event.target.value)} className="h-9 rounded-lg border border-input bg-card px-2.5 text-sm text-foreground">
        {!value && <option value="">Non classificata</option>}
        {options.map(([key, text]) => <option key={key} value={key}>{text}</option>)}
      </select>
    </label>
  )
}

export default function OperatoreSegnalazioniPage() {
  const [filters, setFilters] = useState({ stato: 'tutte', urgenza: 'tutte', categoria: 'tutte' })
  const [items, setItems] = useState(segnalazioni)

  const filteredItems = useMemo(() => [...items]
    .filter((item) => filters.stato === 'tutte' || item.stato === filters.stato)
    .filter((item) => filters.urgenza === 'tutte' || (item.urgenza ?? item.urgenza_llm) === filters.urgenza)
    .filter((item) => filters.categoria === 'tutte' || (item.categoria ?? item.categoria_llm) === filters.categoria)
    .sort((a, b) => (urgencyOrder[b.urgenza ?? b.urgenza_llm] ?? 0) - (urgencyOrder[a.urgenza ?? a.urgenza_llm] ?? 0)),
  [items, filters])

  const handleFieldChange = (id, field, value) => {
    setItems((prev) => prev.map((item) => (item.id === id ? { ...item, [field]: value } : item)))
  }

  const handleClose = (id) => handleFieldChange(id, 'stato', 'chiusa')

  return (
    <div className="space-y-6">
      <Panel className="space-y-3">
        <FilterChips label="Stato" value={filters.stato} onChange={(stato) => setFilters((prev) => ({ ...prev, stato }))} options={stateOptions} />
        <FilterChips label="Urgenza" value={filters.urgenza} onChange={(urgenza) => setFilters((prev) => ({ ...prev, urgenza }))} options={urgencyOptions} />
        <FilterChips label="Categoria" value={filters.categoria} onChange={(categoria) => setFilters((prev) => ({ ...prev, categoria }))} options={categoryOptions} />
      </Panel>

      <div className="space-y-4">
        {filteredItems.length === 0 && <p className="py-10 text-center text-sm text-muted-foreground">Nessuna segnalazione con questi filtri.</p>}
        {filteredItems.map((item) => (
          <article key={item.id} className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <header className="flex flex-wrap items-center gap-2">
              <span className="font-bold text-foreground tabular-nums">#{item.id}</span>
              <span className="text-xs text-muted-foreground">{item.canale} · {formatDateTime(item.ts)}</span>
              <span className="ml-auto flex gap-2"><StatusBadge status={item.stato} /><UrgencyBadge urgency={item.urgenza ?? item.urgenza_llm} /></span>
            </header>
            <p className="mt-3 text-sm leading-relaxed text-foreground">{item.testo}</p>

            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <section className="rounded-xl border border-dashed border-border bg-muted/40 p-4">
                <h3 className="mb-3 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-muted-foreground">
                  <Bot className="h-4 w-4" aria-hidden="true" /> Classificazione AI (LLM)
                </h3>
                <dl className="grid grid-cols-2 gap-2 text-sm">
                  <div><dt className="text-xs text-muted-foreground">categoria_llm</dt><dd className="mt-0.5 font-semibold text-foreground">{item.categoria_llm ?? 'Non classificata'}</dd></div>
                  <div><dt className="text-xs text-muted-foreground">urgenza_llm</dt><dd className="mt-0.5"><UrgencyBadge urgency={item.urgenza_llm} /></dd></div>
                </dl>
              </section>

              <section className="rounded-xl border border-primary/30 bg-secondary p-4">
                <h3 className="mb-3 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-secondary-foreground">
                  <UserCheck className="h-4 w-4" aria-hidden="true" /> Revisione operatore
                </h3>
                <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
                  <ReviewSelect label="Categoria" value={item.categoria} options={categoryOptions} onChange={(value) => handleFieldChange(item.id, 'categoria', value)} />
                  <ReviewSelect label="Urgenza" value={item.urgenza} options={urgencyOptions} onChange={(value) => handleFieldChange(item.id, 'urgenza', value)} />
                  <ReviewSelect label="Stato" value={item.stato} options={stateOptions} onChange={(value) => handleFieldChange(item.id, 'stato', value)} />
                </div>
                {item.stato !== 'chiusa' && (
                  <button type="button" onClick={() => handleClose(item.id)} className="mt-3 rounded-lg bg-primary px-3 py-2 text-xs font-semibold text-primary-foreground transition hover:bg-primary/90">
                    Segna come chiusa
                  </button>
                )}
              </section>
            </div>
          </article>
        ))}
      </div>
    </div>
  )
}
