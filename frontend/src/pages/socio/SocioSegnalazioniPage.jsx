import { useMemo, useState } from 'react'
import { Send } from 'lucide-react'
import Panel from '../../components/Panel'
import StatusBadge from '../../components/StatusBadge'
import { segnalazioni } from '../../mocks/mockData'
import { formatDateTime } from '../../utils/formatters'

const initialSegnalazioni = segnalazioni.filter((item) => [101, 102, 103].includes(item.id))

export default function SocioSegnalazioniPage() {
  const [testo, setTesto] = useState('')
  const [items, setItems] = useState(initialSegnalazioni)

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!testo.trim()) return

    const newItem = {
      id: Date.now(),
      ts: new Date().toISOString(),
      canale: 'portale',
      testo: testo.trim(),
      impianto_id: null,
      categoria: null,
      urgenza: null,
      stato: 'aperta'
    }

    setItems((prev) => [newItem, ...prev])
    setTesto('')
  }

  const list = useMemo(() => [...items].sort((a, b) => new Date(b.ts) - new Date(a.ts)), [items])

  return (
    <div className="space-y-6">
      <Panel eyebrow="Nuova" title="Invia una comunicazione">
        <form onSubmit={handleSubmit} className="space-y-3">
          <label className="grid gap-2 text-sm font-medium text-foreground">
            Dettaglio segnalazione
            <textarea
              value={testo}
              onChange={(event) => setTesto(event.target.value)}
              placeholder="Descrivi il problema o la richiesta…"
              rows={4}
              className="rounded-xl border border-input bg-background px-3 py-2.5 text-sm"
            />
          </label>
          <button type="submit" disabled={!testo.trim()} className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-gradient-primary px-5 font-semibold text-primary-foreground shadow-glow transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto">
            <Send className="h-4 w-4" aria-hidden="true" /> Invia segnalazione
          </button>
        </form>
      </Panel>

      <Panel eyebrow="Storico" title="Le tue segnalazioni">
        <ul className="divide-y divide-border">
          {list.map((item) => (
            <li key={item.id} className="grid grid-cols-[minmax(0,1fr)_auto] gap-3 py-4 first:pt-0 last:pb-0">
              <div className="min-w-0">
                <p className="text-sm text-foreground">{item.testo}</p>
                <p className="mt-1 text-xs text-muted-foreground tabular-nums">#{item.id} · {formatDateTime(item.ts)}</p>
                <p className="mt-1 text-xs text-muted-foreground">Segnalazione generale</p>
              </div>
              <StatusBadge status={item.stato} />
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  )
}
