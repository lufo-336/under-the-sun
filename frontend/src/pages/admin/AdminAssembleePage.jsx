import { useState } from 'react'
import { CalendarDays, ChevronDown, Sparkles } from 'lucide-react'
import { verbali } from '../../mocks/mockData'
import { formatShortDate } from '../../utils/formatters'

export default function AdminAssembleePage() {
  const [expandedIds, setExpandedIds] = useState([])

  const handleToggle = (id) => {
    setExpandedIds((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]))
  }

  return (
    <div className="space-y-5">
      {verbali.map((verbale) => {
        const isExpanded = expandedIds.includes(verbale.id)
        return (
          <article key={verbale.id} className="rounded-2xl border border-border bg-card p-5 shadow-soft sm:p-6">
            <h2 className="text-lg font-bold text-foreground">{verbale.id}</h2>
            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground tabular-nums">
              <span className="flex items-center gap-1"><CalendarDays className="h-3.5 w-3.5" aria-hidden="true" />{formatShortDate(verbale.data_assemblea)}</span>
              <span className="text-muted-foreground">Verbale assemblea</span>
            </div>

            <div className="mt-4 rounded-xl border border-accent/40 bg-accent-soft p-4">
              <p className="mb-1.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide text-accent-strong">
                <Sparkles className="h-4 w-4" aria-hidden="true" /> Sintesi automatica LLM
              </p>
              <p className="text-sm leading-relaxed text-foreground">{verbale.sintesi}</p>
            </div>

            <button
              type="button"
              onClick={() => handleToggle(verbale.id)}
              aria-expanded={isExpanded}
              className="mt-3 inline-flex items-center gap-1.5 text-sm font-semibold text-primary hover:underline"
            >
              {isExpanded ? 'Chiudi verbale' : 'Leggi il verbale completo'}
              <ChevronDown className={`h-4 w-4 transition-transform ${isExpanded ? 'rotate-180' : ''}`} aria-hidden="true" />
            </button>
            {isExpanded && <p className="mt-3 border-t border-border pt-3 text-sm leading-relaxed text-muted-foreground">{verbale.testo_completo}</p>}
          </article>
        )
      })}
    </div>
  )
}
