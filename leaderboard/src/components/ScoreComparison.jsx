import { useState } from 'react'
import MascotCrossing from './MascotCrossing.jsx'
import TeamsHistoryChart, { METRICS } from './TeamsHistoryChart.jsx'

export default function ScoreComparison({ history }) {
  const [isVisible, setIsVisible] = useState(false)
  const [selectedMetric, setSelectedMetric] = useState('total')

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-[var(--color-foreground-secondary)]">
          Cliquez sur une équipe pour voir sa progression détaillée.
        </p>
        <button
          type="button"
          onClick={() => setIsVisible((visible) => !visible)}
          aria-expanded={isVisible}
          className="inline-flex items-center gap-2 rounded-md border border-[var(--color-border-default)] bg-[var(--color-component-surface)] px-4 py-2 text-sm font-semibold text-[var(--color-foreground-primary)] transition-colors hover:border-[var(--color-border-primary-emphasis)] hover:bg-[var(--color-component-surface-subtle)]"
        >
          <span aria-hidden="true">{isVisible ? '▾' : '↗'}</span>
          {isVisible
            ? 'Masquer la comparaison'
            : 'Comparer les scores dans le temps'}
        </button>
      </div>
      {isVisible && (
        <section
          className="relative mb-8 rounded-md border border-[var(--color-border-subtle)] bg-[var(--color-component-surface-subtle)] p-5"
          aria-label="Comparaison des équipes par type de score"
        >
          <MascotCrossing />
          <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
            <div>
              <h2 className="text-lg font-bold text-[var(--color-foreground-primary)]">
                Progression par type de score
              </h2>
              <p className="mt-1 text-xs text-[var(--color-foreground-secondary)]">
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
                  className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${selectedMetric === metric.key ? 'bg-[var(--color-fill-primary-default)] text-[var(--color-foreground-contrast-emphasis)]' : 'text-[var(--color-foreground-secondary)] hover:bg-[var(--color-component-surface-muted)] hover:text-[var(--color-foreground-primary)]'}`}
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
