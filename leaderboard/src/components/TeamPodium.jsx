import BreakdownChart from './BreakdownChart.jsx'
import useCountUp from '../hooks/useCountUp.js'

const MEDALS = ['🥇', '🥈', '🥉']
const PODIUM_GLOW = ['glow-gold', 'glow-silver', 'glow-bronze']
const PODIUM_ORDER = [1, 0, 2]

function PodiumCard({ team, place, onSelect }) {
  const score = useCountUp(team.score ?? 0)
  const sizes = ['text-2xl', 'text-xl', 'text-lg']

  return (
    <button
      onClick={onSelect}
      className={`animate-slide-up flex cursor-pointer flex-col items-center rounded-2xl border border-slate-700/60
        bg-slate-900/80 p-5 text-center transition-transform hover:scale-[1.02]
        ${PODIUM_GLOW[place]} ${place === 0 ? 'md:-translate-y-4' : ''}`}
      style={{ animationDelay: `${place * 120}ms` }}
    >
      <div className="text-4xl">{MEDALS[place]}</div>
      <span className={`mt-2 ${sizes[place]} font-bold text-slate-100`}>
        {team.team}
      </span>
      <div className="mt-1 font-mono text-3xl font-black text-emerald-400">
        {score.toFixed(1)}
      </div>
      <div className="mt-1 text-xs text-slate-500">points</div>
      <div className="mt-3 w-full pointer-events-none">
        <BreakdownChart breakdown={team.breakdown} />
      </div>
    </button>
  )
}

export default function TeamPodium({ teams, onSelect }) {
  return (
    <section className="mx-auto mt-8 grid max-w-5xl grid-cols-1 gap-4 px-6 md:grid-cols-3">
      {PODIUM_ORDER.map((placeIdx) =>
        teams[placeIdx] ? (
          <PodiumCard
            key={teams[placeIdx].team}
            team={teams[placeIdx]}
            place={placeIdx}
            onSelect={() => onSelect(teams[placeIdx])}
          />
        ) : null,
      )}
    </section>
  )
}
