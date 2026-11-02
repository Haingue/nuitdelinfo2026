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
  const testStatusLabels = {
    passed: 'réussis',
    failed: 'échec',
    not_found: 'aucune suite détectée',
    unavailable: 'indisponible',
  }
  const quality = team.details?.quality_breakdown
  const qualityRows = quality
    ? [
        ['Quality Gate SonarCloud', quality.gate, 20],
        [
          `Maintenabilité Sonar (${quality.maintainability_rating ?? 'N/D'})`,
          quality.maintainability,
          15,
        ],
        [
          `Sécurité Sonar (${quality.security_rating ?? 'N/D'})`,
          quality.security,
          10,
        ],
        [
          `Couverture Sonar (${quality.coverage_percent ?? 'N/D'}%)`,
          quality.coverage,
          10,
        ],
        [
          'Dépendances sans vulnérabilité HIGH/CRITICAL',
          quality.supply_chain,
          5,
        ],
      ]
    : []

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
          {quality && (
            <div className="mt-4 border-t border-slate-800 pt-3">
              <h4 className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-400">
                Détail qualité · {quality.total}/60
              </h4>
              <dl className="space-y-1 text-sm">
                {qualityRows.map(([label, points, max]) => (
                  <div
                    key={label}
                    className="flex items-center justify-between gap-4"
                  >
                    <dt className="text-slate-400">{label}</dt>
                    <dd className="text-right tabular-nums text-slate-200">
                      {points}/{max}
                    </dd>
                  </div>
                ))}
              </dl>
              {(quality.technical_debt_minutes != null ||
                quality.technical_debt_ratio_percent != null) && (
                <p className="mt-2 text-xs text-slate-500">
                  Dette technique Sonar :{' '}
                  {quality.technical_debt_minutes ?? 'N/D'} min
                  {quality.technical_debt_ratio_percent != null &&
                    ` · ratio ${quality.technical_debt_ratio_percent}%`}
                  {quality.code_smells != null &&
                    ` · ${quality.code_smells} code smells`}
                </p>
              )}
            </div>
          )}
          {team.details?.tests && (
            <p className="mt-3 text-sm text-slate-400">
              Tests CI :{' '}
              <span className="text-slate-200">
                {testStatusLabels[team.details.tests.status] ??
                  team.details.tests.status}
              </span>
              {team.details.tests.failed_tests > 0 &&
                ` · ${team.details.tests.failed_tests} test(s) en échec`}
              {team.details.tests.frameworks &&
                ` · ${team.details.tests.frameworks}`}
            </p>
          )}
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
