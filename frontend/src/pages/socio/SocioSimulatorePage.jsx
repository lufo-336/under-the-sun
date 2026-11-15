import { useMemo, useState } from 'react'
import { socioSummary } from '../../mocks/mockData'
import { formatCurrency, formatKg, formatNumber } from '../../utils/formatters'

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

  return (
    <div className="page-stack simulator-page">
      <section className="panel-section">
        <div className="panel-header">
          <div>
            <p className="section-kicker">Simulazione CER</p>
            <h3>Nuovo scenario di condivisione</h3>
          </div>
        </div>

        <div className="simulator-grid">
          <div className="input-panel">
            <label>
              <span>Consumo annuo (kWh)</span>
              <input
                type="number"
                name="consumo_annuo_kwh"
                value={form.consumo_annuo_kwh}
                onChange={handleChange}
                min={0}
                max={20000}
              />
            </label>

            <label>
              <span>Quota spostata nelle ore diurne (%)</span>
              <input
                type="range"
                name="quota_spostata_ore_diurne_pct"
                min={0}
                max={100}
                value={form.quota_spostata_ore_diurne_pct}
                onChange={handleChange}
              />
              <strong>{form.quota_spostata_ore_diurne_pct}%</strong>
            </label>
          </div>

          <div className="result-panel">
            <div className="comparison-box">
              <div>
                <span>Situazione attuale</span>
                <strong>{formatNumber(socioSummary.kwh_condivisi)} kWh</strong>
                <small>{formatCurrency(socioSummary.incentivo_eur)}/anno</small>
              </div>
              <div className="comparison-arrow">→</div>
              <div>
                <span>Stimato</span>
                <strong>{formatNumber(result.kwh_condivisi_stimati)} kWh</strong>
                <small>{formatCurrency(result.incentivo_eur_stimato)}/anno</small>
              </div>
            </div>

            <div className="result-grid">
              <div className="mini-stat">
                <label>kWh condivisi stimati</label>
                <strong>{formatNumber(result.kwh_condivisi_stimati)} kWh</strong>
              </div>
              <div className="mini-stat">
                <label>Incentivo stimato</label>
                <strong>{formatCurrency(result.incentivo_eur_stimato)}</strong>
              </div>
              <div className="mini-stat">
                <label>CO2 evitata stimata</label>
                <strong>{formatKg(result.co2_evitata_kg_stimata)}</strong>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  )
}
