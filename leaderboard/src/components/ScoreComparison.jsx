import { useState } from 'react'
import TeamsHistoryChart, { METRICS } from './TeamsHistoryChart.jsx'

export default function ScoreComparison({ history }) {
  const [isVisible, setIsVisible] = useState(false)
  const [selectedMetric, setSelectedMetric] = useState('total')

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-slate-500">
          Cliquez sur une équipe pour voir sa progression détaillée.
        </p>
        <button
          type="button"
          onClick={() => setIsVisible((visible) => !visible)}
          aria-expanded={isVisible}
          className="inline-flex items-center gap-2 rounded-md border border-sky-700/70 bg-sky-950/60 px-4 py-2 text-sm font-semibold text-sky-200 transition-colors hover:border-sky-500 hover:bg-sky-900/60"
        >
          <span aria-hidden="true">{isVisible ? '▾' : '↗'}</span>
          {isVisible
            ? 'Masquer la comparaison'
            : 'Comparer les scores dans le temps'}
        </button>
      </div>
      {isVisible && (
        <section
          className="mb-8 border-y border-slate-800 bg-slate-900/40 py-5"
          aria-label="Comparaison des équipes par type de score"
        >
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-slate-100">
                Progression par type de score
              </h2>
              <p className="mt-1 text-xs text-slate-500">
                Chaque courbe représente une équipe.
              </p>
            </div>
            <div
              className="flex flex-wrap gap-1"
              role="group"
              aria-label="Type de score"
            >
              {METRICS.map((metric) => (
                <button
                  key={metric.key}
                  type="button"
                  onClick={() => setSelectedMetric(metric.key)}
                  aria-pressed={selectedMetric === metric.key}
                  className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${selectedMetric === metric.key ? 'bg-emerald-500 text-slate-950' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'}`}
                >
                  {metric.label}
                </button>
              ))}
            </div>
          </div>
          <TeamsHistoryChart history={history} metric={selectedMetric} />
        </section>
      )}
    </>
  )
}
