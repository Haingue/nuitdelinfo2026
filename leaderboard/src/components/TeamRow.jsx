import Sparkline from './Sparkline.jsx'
import BreakdownChart from './BreakdownChart.jsx'
import useCountUp from '../hooks/useCountUp.js'

function RankDelta({ delta }) {
  if (delta > 0)
    return (
      <span className="animate-fade-in text-xs font-semibold text-[var(--color-foreground-success-default)]">
        ▲ {delta}
      </span>
    )
  if (delta < 0)
    return (
      <span className="animate-fade-in text-xs font-semibold text-[var(--color-foreground-error-default)]">
        ▼ {Math.abs(delta)}
      </span>
    )
  return <span className="text-xs text-[var(--color-foreground-secondary)]">—</span>
}

export default function TeamRow({ team, history, prevRank, onSelect }) {
  const score = useCountUp(team.score ?? 0)
  const delta = prevRank != null ? prevRank - team.rank : 0

  return (
    <li>
      <button
        onClick={onSelect}
        className="animate-slide-up grid w-full grid-cols-[2rem_minmax(0,1fr)_auto] cursor-pointer items-center gap-3 rounded-md sm:grid-cols-[3rem_minmax(0,1fr)_9rem_6rem] sm:gap-4
          border border-[var(--color-border-subtle)] bg-[var(--color-component-surface)] p-4 text-left transition-colors
          hover:border-[var(--color-border-primary-emphasis)] hover:bg-[var(--color-component-surface-subtle)]"
      >
        <div className="flex flex-col items-center justify-center">
          <span className="text-xl font-black text-[var(--color-foreground-primary)]">{team.rank}</span>
          <RankDelta delta={delta} />
        </div>
        <div className="min-w-0">
          <span className="truncate font-semibold text-[var(--color-foreground-primary)]">
            {team.team}
          </span>
          <div className="mt-1 pointer-events-none">
            <BreakdownChart breakdown={team.breakdown} />
          </div>
        </div>
        <div className="hidden sm:block">
          <Sparkline points={history[team.team]} />
        </div>
        <div className="text-right">
          <div className="font-mono text-2xl font-semibold text-[var(--color-foreground-primary-on-neutral-default)]">
            {score.toFixed(1)}
          </div>
          {team.eligible ? (
            <span className="text-[10px] uppercase tracking-wide text-[var(--color-foreground-secondary)]">
              éligible
            </span>
          ) : (
            <span className="text-[10px] uppercase tracking-wide text-[var(--color-foreground-error-default)]">
              non éligible
            </span>
          )}
        </div>
      </button>
    </li>
  )
}
