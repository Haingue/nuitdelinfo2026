import BreakdownChart from './BreakdownChart.jsx'
import useCountUp from '../hooks/useCountUp.js'

const MEDALS = ['🥇', '🥈', '🥉']
const PODIUM_ORDER = ['md:order-2', 'md:order-1', 'md:order-3']

function PodiumCard({ team, place, onSelect }) {
  const score = useCountUp(team.score ?? 0)
  const sizes = ['text-2xl', 'text-xl', 'text-lg']

  return (
    <button
      onClick={onSelect}
      className={`animate-slide-up flex cursor-pointer flex-col items-center rounded-md border border-[var(--color-border-subtle)]
        bg-[var(--color-component-surface)] p-5 text-center transition-colors hover:border-[var(--color-border-primary-emphasis)] hover:bg-[var(--color-component-surface-subtle)]
        ${PODIUM_ORDER[place]} ${place === 0 ? 'border-t-4 border-t-[var(--color-border-primary-emphasis)]' : ''}`}
      style={{ animationDelay: `${place * 120}ms` }}
    >
      <div className="text-4xl">{MEDALS[place]}</div>
      <span className={`mt-2 ${sizes[place]} font-bold text-[var(--color-foreground-primary)]`}>
        {team.team}
      </span>
      <div className="mt-1 font-mono text-3xl font-semibold text-[var(--color-foreground-primary-on-neutral-default)]">
        {score.toFixed(1)}
      </div>
      <div className="mt-1 text-xs text-[var(--color-foreground-secondary)]">points</div>
      <div className="mt-3 w-full pointer-events-none">
        <BreakdownChart breakdown={team.breakdown} />
      </div>
    </button>
  )
}

export default function TeamPodium({ teams, onSelect }) {
  return (
    <section className="mx-auto mt-8 grid max-w-5xl grid-cols-1 gap-4 px-6 md:grid-cols-3">
      {teams.map((team, placeIdx) =>
        team ? (
          <PodiumCard
            key={team.team}
            team={team}
            place={placeIdx}
            onSelect={() => onSelect(team)}
          />
        ) : null,
      )}
    </section>
  )
}
