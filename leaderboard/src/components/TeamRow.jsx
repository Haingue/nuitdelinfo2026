import Sparkline from './Sparkline.jsx'
import BreakdownChart from './BreakdownChart.jsx'
import useCountUp from '../hooks/useCountUp.js'

function RankDelta({ delta }) {
  if (delta > 0)
    return (
      <span className="animate-fade-in text-xs font-semibold text-emerald-400">
        ▲ {delta}
      </span>
    )
  if (delta < 0)
    return (
      <span className="animate-fade-in text-xs font-semibold text-rose-400">
        ▼ {Math.abs(delta)}
      </span>
    )
  return <span className="text-xs text-slate-600">—</span>
}

export default function TeamRow({ team, history, prevRank, onSelect }) {
  const score = useCountUp(team.score ?? 0)
  const delta = prevRank != null ? prevRank - team.rank : 0

  return (
    <li>
      <button
        onClick={onSelect}
        className="animate-slide-up grid w-full grid-cols-[3rem_1fr_9rem_10rem] cursor-pointer items-center gap-4 rounded-xl
          border border-slate-800 bg-slate-900/60 p-4 text-left transition-colors
          hover:border-sky-600/50 hover:bg-slate-900"
      >
        <div className="flex flex-col items-center justify-center">
          <span className="text-xl font-black text-slate-300">{team.rank}</span>
          <RankDelta delta={delta} />
        </div>
        <div className="min-w-0">
          <span className="truncate font-semibold text-slate-100">
            {team.team}
          </span>
          <div className="mt-1 pointer-events-none">
            <BreakdownChart breakdown={team.breakdown} />
          </div>
        </div>
        <Sparkline points={history[team.team]} />
        <div className="text-right">
          <div className="font-mono text-2xl font-black text-emerald-400">
            {score.toFixed(1)}
          </div>
          {team.eligible ? (
            <span className="text-[10px] uppercase tracking-wide text-slate-500">
              éligible
            </span>
          ) : (
            <span className="text-[10px] uppercase tracking-wide text-rose-400">
              non éligible
            </span>
          )}
        </div>
      </button>
    </li>
  )
}
