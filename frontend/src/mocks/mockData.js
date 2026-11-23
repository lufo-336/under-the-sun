export const socioSummary = {
  anno: 2026,
  kwh_consumati: 6420,
  kwh_condivisi: 1480,
  incentivo_eur: 432.8,
  co2_evitata_kg: 2785,
  mesi: [
    { mese: '2026-01', kwh_consumati: 460, kwh_condivisi: 95, incentivo_eur: 32.5, co2_evitata_kg: 180 },
    { mese: '2026-02', kwh_consumati: 510, kwh_condivisi: 110, incentivo_eur: 35.7, co2_evitata_kg: 205 },
    { mese: '2026-03', kwh_consumati: 540, kwh_condivisi: 124, incentivo_eur: 38.9, co2_evitata_kg: 230 },
    { mese: '2026-04', kwh_consumati: 570, kwh_condivisi: 136, incentivo_eur: 41.2, co2_evitata_kg: 250 },
    { mese: '2026-05', kwh_consumati: 590, kwh_condivisi: 142, incentivo_eur: 44.1, co2_evitata_kg: 270 },
    { mese: '2026-06', kwh_consumati: 610, kwh_condivisi: 149, incentivo_eur: 46.4, co2_evitata_kg: 285 },
    { mese: '2026-07', kwh_consumati: 620, kwh_condivisi: 152, incentivo_eur: 48.0, co2_evitata_kg: 295 },
    { mese: '2026-08', kwh_consumati: 585, kwh_condivisi: 145, incentivo_eur: 45.7, co2_evitata_kg: 282 },
    { mese: '2026-09', kwh_consumati: 600, kwh_condivisi: 149, incentivo_eur: 46.8, co2_evitata_kg: 287 },
    { mese: '2026-10', kwh_consumati: 630, kwh_condivisi: 168, incentivo_eur: 52.2, co2_evitata_kg: 316 },
    { mese: '2026-11', kwh_consumati: 615, kwh_condivisi: 156, incentivo_eur: 49.1, co2_evitata_kg: 303 },
    { mese: '2026-12', kwh_consumati: 690, kwh_condivisi: 174, incentivo_eur: 54.9, co2_evitata_kg: 332 }
  ]
}

export const consumoSerie = [
  { ts: '2026-10-01T10:00:00Z', kwh: 121, kwh_previsti: 129 },
  { ts: '2026-10-02T10:00:00Z', kwh: 118, kwh_previsti: 125 },
  { ts: '2026-10-03T10:00:00Z', kwh: 126, kwh_previsti: 131 },
  { ts: '2026-10-04T10:00:00Z', kwh: 133, kwh_previsti: 137 },
  { ts: '2026-10-05T10:00:00Z', kwh: 139, kwh_previsti: 142 },
  { ts: '2026-10-06T10:00:00Z', kwh: 118, kwh_previsti: 128 },
  { ts: '2026-10-07T10:00:00Z', kwh: 124, kwh_previsti: 130 },
  { ts: '2026-10-08T10:00:00Z', kwh: 140, kwh_previsti: 135 },
  { ts: '2026-10-09T10:00:00Z', kwh: 148, kwh_previsti: 138 },
  { ts: '2026-10-10T10:00:00Z', kwh: 151, kwh_previsti: 140 },
  { ts: '2026-10-11T10:00:00Z', kwh: 165, kwh_previsti: 145 },
  { ts: '2026-10-12T10:00:00Z', kwh: 170, kwh_previsti: 150 },
  { ts: '2026-10-13T10:00:00Z', kwh: 176, kwh_previsti: 148 },
  { ts: '2026-10-14T10:00:00Z', kwh: 184, kwh_previsti: 152 },
  { ts: '2026-10-15T10:00:00Z', kwh: 211, kwh_previsti: 154 },
  { ts: '2026-10-16T10:00:00Z', kwh: 198, kwh_previsti: 158 },
  { ts: '2026-10-17T10:00:00Z', kwh: 172, kwh_previsti: 149 },
  { ts: '2026-10-18T10:00:00Z', kwh: 160, kwh_previsti: 147 },
  { ts: '2026-10-19T10:00:00Z', kwh: 158, kwh_previsti: 143 },
  { ts: '2026-10-20T10:00:00Z', kwh: 149, kwh_previsti: 141 },
  { ts: '2026-10-21T10:00:00Z', kwh: 142, kwh_previsti: 138 },
  { ts: '2026-10-22T10:00:00Z', kwh: 136, kwh_previsti: 134 },
  { ts: '2026-10-23T10:00:00Z', kwh: 132, kwh_previsti: 130 },
  { ts: '2026-10-24T10:00:00Z', kwh: 127, kwh_previsti: 129 },
  { ts: '2026-10-25T10:00:00Z', kwh: 129, kwh_previsti: 130 },
  { ts: '2026-10-26T10:00:00Z', kwh: 136, kwh_previsti: 132 },
  { ts: '2026-10-27T10:00:00Z', kwh: 144, kwh_previsti: 136 },
  { ts: '2026-10-28T10:00:00Z', kwh: 147, kwh_previsti: 141 },
  { ts: '2026-10-29T10:00:00Z', kwh: 151, kwh_previsti: 144 },
  { ts: '2026-10-30T10:00:00Z', kwh: 156, kwh_previsti: 146 },
  { ts: '2026-10-31T10:00:00Z', kwh: 161, kwh_previsti: 149 }
]

export const simulatore = {
  consumo_annuo_kwh: 3200,
  quota_spostata_ore_diurne_pct: 20,
  kwh_condivisi_stimati: 665,
  incentivo_eur_stimato: 207.80,
  co2_evitata_kg_stimata: 1187,
  confronto_attuale: {
    kwh_condivisi: 1480,
    incentivo_eur: 432.80
  }
}

export const impianti = [
  { id: 1, nome: 'Tetto Scuola Pinerolo', comune: 'Pinerolo', lat: 44.886, lon: 7.332, kwp: 180, data_attivazione: '2024-04-05T00:00:00Z', anomalie_aperte: 2 },
  { id: 2, nome: 'Pensilina Municipio', comune: 'Bobbio Pellice', lat: 44.802, lon: 7.196, kwp: 120, data_attivazione: '2023-09-12T00:00:00Z', anomalie_aperte: 1 },
  { id: 3, nome: 'Capannone Zona Industriale', comune: 'Pinerolo', lat: 44.879, lon: 7.355, kwp: 260, data_attivazione: '2025-01-18T00:00:00Z', anomalie_aperte: 3 }
]

export const anomalie = [
  { id: 101, impianto_id: 1, inizio: '2026-10-15T08:00:00Z', fine: null, tipo: 'guasto', score: 0.77, stato: 'aperta' },
  { id: 102, impianto_id: 1, inizio: '2026-10-18T10:00:00Z', fine: '2026-10-20T12:00:00Z', tipo: 'stringa', score: 0.58, stato: 'chiusa' },
  { id: 201, impianto_id: 2, inizio: '2026-10-17T09:15:00Z', fine: null, tipo: null, score: 0.63, stato: 'in_corso' },
  { id: 301, impianto_id: 3, inizio: '2026-10-16T11:30:00Z', fine: null, tipo: 'guasto', score: 0.81, stato: 'aperta' },
  { id: 302, impianto_id: 3, inizio: '2026-10-14T14:00:00Z', fine: '2026-10-15T09:00:00Z', tipo: 'neve', score: 0.65, stato: 'chiusa' }
]

export const segnalazioni = [
  { id: 101, ts: '2026-10-28T09:10:00Z', canale: 'portale', testo: 'Il contatore del tetto scolastico segnala un calo anomalo nelle ore pomeridiane, potrebbe essere un guasto al sensore.', impianto_id: 1, categoria_llm: 'guasto_impianto', urgenza_llm: 'alta', categoria: 'guasto_impianto', urgenza: 'alta', stato: 'aperta' },
  { id: 102, ts: '2026-10-27T15:20:00Z', canale: 'email', testo: 'Ho notato che il riepilogo mensile non corrisponde alle spese medie di casa.', impianto_id: null, categoria_llm: 'bolletta_pagamenti', urgenza_llm: 'media', categoria: 'bolletta_pagamenti', urgenza: 'media', stato: 'in_corso' },
  { id: 103, ts: '2026-10-26T12:00:00Z', canale: 'interno', testo: 'Vorrei ricevere un chiarimento sull’andamento dei kWh condivisi nelle ultime settimane.', impianto_id: 2, categoria_llm: 'informazioni', urgenza_llm: 'bassa', categoria: 'informazioni', urgenza: 'bassa', stato: 'chiusa' },
  { id: 104, ts: '2026-10-23T18:45:00Z', canale: 'email', testo: 'Il pannello del capannone mostra un forte calo di generazione rispetto alla media giornaliera.', impianto_id: 3, categoria_llm: null, urgenza_llm: null, categoria: null, urgenza: null, stato: 'aperta' }
]

export const communityKpi = {
  anno: 2026,
  soci: 128,
  impianti: 12,
  kwp_totali: 1420,
  kwh_prodotti: 942000,
  kwh_condivisi: 185600,
  incentivo_eur: 742500,
  co2_evitata_kg: 184500,
  anomalie_aperte: 9,
  segnalazioni_aperte: 14
}

export const communityEnergySeries = [
  { ts: '2026-01-01T00:00:00Z', kwh_immessi: 56000, kwh_prelevati: 43000, kwh_condivisi: 12400 },
  { ts: '2026-02-01T00:00:00Z', kwh_immessi: 58700, kwh_prelevati: 44100, kwh_condivisi: 13700 },
  { ts: '2026-03-01T00:00:00Z', kwh_immessi: 63400, kwh_prelevati: 46200, kwh_condivisi: 15300 },
  { ts: '2026-04-01T00:00:00Z', kwh_immessi: 65900, kwh_prelevati: 47100, kwh_condivisi: 16200 },
  { ts: '2026-05-01T00:00:00Z', kwh_immessi: 68100, kwh_prelevati: 48300, kwh_condivisi: 17050 },
  { ts: '2026-06-01T00:00:00Z', kwh_immessi: 70500, kwh_prelevati: 50100, kwh_condivisi: 17750 },
  { ts: '2026-07-01T00:00:00Z', kwh_immessi: 72900, kwh_prelevati: 51800, kwh_condivisi: 18480 },
  { ts: '2026-08-01T00:00:00Z', kwh_immessi: 71600, kwh_prelevati: 52400, kwh_condivisi: 18890 },
  { ts: '2026-09-01T00:00:00Z', kwh_immessi: 74200, kwh_prelevati: 53100, kwh_condivisi: 19280 },
  { ts: '2026-10-01T00:00:00Z', kwh_immessi: 77200, kwh_prelevati: 55100, kwh_condivisi: 20340 },
  { ts: '2026-11-01T00:00:00Z', kwh_immessi: 78900, kwh_prelevati: 57000, kwh_condivisi: 21620 },
  { ts: '2026-12-01T00:00:00Z', kwh_immessi: 81300, kwh_prelevati: 59200, kwh_condivisi: 22870 }
]

export const verbali = [
  { id: 1, data_assemblea: '2026-10-15', sintesi: 'La comunità ha approvato il piano di riequilibrio tra produzione e prelievo nei mesi estivi, con riduzione delle anomalie del 18%.', testo_completo: 'Durante l’assemblea straordinaria del 15 ottobre, i soci hanno approvato la nuova configurazione del sistema di allocazione dei kWh condivisi. È stato confermato l’aumento di efficienza dell’impianto del tetto scolastico e il piano di manutenzione preventiva dei sensori, con priorità alle zone a maggior carico nel mese di ottobre.' },
  { id: 2, data_assemblea: '2026-09-12', sintesi: 'Rinnovato il programma di incentivazione per le utenze domestiche e introdotto il supporto ai soci con consumo elevato durante le ore diurne.', testo_completo: 'L’assemblea di settembre ha dedicato ampio spazio alla revisione dei criteri per la partecipazione ai bonus energetici e all’allocazione più equa delle quote di scambio. Sono stati presentati i primi risultati del monitoraggio delle utenze ad alto consumo e si è deciso di allargare il piano d’assistenza a 18 famiglie.' },
  { id: 3, data_assemblea: '2026-08-20', sintesi: 'Consolidato il nuovo modello di gestione delle segnalazioni e definita la road map del semestre successivo.', testo_completo: 'Con il verbale del 20 agosto si è definita la governance delle segnalazioni e delle anomalie. I membri del comitato hanno approvato la roadmap per le prossime 6 settimane, con azioni prioritarie su manutenzione impianti, supporto agli utenti e digitalizzazione delle comunicazioni tra soci e operatori.' }
]

export const impiantoProductionSeries = {
  1: [
    { ts: '2026-10-01T00:00:00Z', kwh: 168, kwh_previsti: 170 },
    { ts: '2026-10-03T00:00:00Z', kwh: 181, kwh_previsti: 176 },
    { ts: '2026-10-05T00:00:00Z', kwh: 196, kwh_previsti: 181 },
    { ts: '2026-10-07T00:00:00Z', kwh: 205, kwh_previsti: 188 },
    { ts: '2026-10-09T00:00:00Z', kwh: 218, kwh_previsti: 195 },
    { ts: '2026-10-11T00:00:00Z', kwh: 226, kwh_previsti: 198 },
    { ts: '2026-10-13T00:00:00Z', kwh: 230, kwh_previsti: 201 },
    { ts: '2026-10-15T00:00:00Z', kwh: 185, kwh_previsti: 209 },
    { ts: '2026-10-17T00:00:00Z', kwh: 194, kwh_previsti: 196 },
    { ts: '2026-10-19T00:00:00Z', kwh: 201, kwh_previsti: 191 },
    { ts: '2026-10-21T00:00:00Z', kwh: 214, kwh_previsti: 188 },
    { ts: '2026-10-23T00:00:00Z', kwh: 219, kwh_previsti: 200 }
  ],
  2: [
    { ts: '2026-10-01T00:00:00Z', kwh: 120, kwh_previsti: 122 },
    { ts: '2026-10-03T00:00:00Z', kwh: 128, kwh_previsti: 126 },
    { ts: '2026-10-05T00:00:00Z', kwh: 138, kwh_previsti: 131 },
    { ts: '2026-10-07T00:00:00Z', kwh: 141, kwh_previsti: 136 },
    { ts: '2026-10-09T00:00:00Z', kwh: 149, kwh_previsti: 142 },
    { ts: '2026-10-11T00:00:00Z', kwh: 155, kwh_previsti: 146 },
    { ts: '2026-10-13T00:00:00Z', kwh: 162, kwh_previsti: 148 },
    { ts: '2026-10-15T00:00:00Z', kwh: 166, kwh_previsti: 150 },
    { ts: '2026-10-17T00:00:00Z', kwh: 159, kwh_previsti: 148 },
    { ts: '2026-10-19T00:00:00Z', kwh: 145, kwh_previsti: 146 },
    { ts: '2026-10-21T00:00:00Z', kwh: 142, kwh_previsti: 140 },
    { ts: '2026-10-23T00:00:00Z', kwh: 136, kwh_previsti: 138 }
  ],
  3: [
    { ts: '2026-10-01T00:00:00Z', kwh: 205, kwh_previsti: 189 },
    { ts: '2026-10-03T00:00:00Z', kwh: 214, kwh_previsti: 196 },
    { ts: '2026-10-05T00:00:00Z', kwh: 221, kwh_previsti: 203 },
    { ts: '2026-10-07T00:00:00Z', kwh: 230, kwh_previsti: 209 },
    { ts: '2026-10-09T00:00:00Z', kwh: 238, kwh_previsti: 214 },
    { ts: '2026-10-11T00:00:00Z', kwh: 245, kwh_previsti: 220 },
    { ts: '2026-10-13T00:00:00Z', kwh: 251, kwh_previsti: 224 },
    { ts: '2026-10-15T00:00:00Z', kwh: 194, kwh_previsti: 233 },
    { ts: '2026-10-17T00:00:00Z', kwh: 205, kwh_previsti: 228 },
    { ts: '2026-10-19T00:00:00Z', kwh: 210, kwh_previsti: 220 },
    { ts: '2026-10-21T00:00:00Z', kwh: 217, kwh_previsti: 214 },
    { ts: '2026-10-23T00:00:00Z', kwh: 222, kwh_previsti: 208 }
  ]
}

export const demoUsers = {
  socio: { nome: 'Socio prova', email: 'socio1@example.com', password: 'demo123', home: '/socio/dashboard' },
  operatore: { nome: 'Operatore prova', email: 'operatore@example.com', password: 'demo123', home: '/operatore/impianti' },
  admin: { nome: 'Admin prova', email: 'admin@example.com', password: 'demo123', home: '/admin/kpi' }
}
