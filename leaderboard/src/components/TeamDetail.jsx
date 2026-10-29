import { useEffect } from 'react'
import BreakdownChart from './BreakdownChart.jsx'
import HistoryChart from './HistoryChart.jsx'

export default function TeamDetail({ team, history, onClose }) {
  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const snapshots = history[team.team] || []

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm animate-fade-in" />
      <div
        className="animate-slide-up relative max-h-[90vh] w-full max-w-3xl overflow-y-auto
        rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <h2 className="text-2xl font-black text-slate-100">{team.team}</h2>
          <div className="text-right">
            <div className="font-mono text-3xl font-black text-emerald-400">
              {(team.score ?? 0).toFixed(1)}
            </div>
            <div className="text-xs text-slate-500">points · #{team.rank}</div>
          </div>
        </div>

        <div className="mt-6">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
            📈 Progression des scores dans la nuit
          </h3>
          <HistoryChart snapshots={snapshots} />
        </div>

        <div className="mt-6">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
            📊 Détail actuel par type de score
          </h3>
          <BreakdownChart breakdown={team.breakdown} />
        </div>

        <button
          onClick={onClose}
          className="mt-6 w-full rounded-lg border border-slate-700 py-2 text-sm
            text-slate-300 transition-colors hover:border-slate-500 hover:bg-slate-800"
        >
          Fermer (Échap)
        </button>
      </div>
    </div>
  )
}
