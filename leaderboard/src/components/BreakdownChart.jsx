const SEGMENTS = [
  { key: 'qualite', label: 'Qualité', max: 60, color: 'bg-emerald-500' },
  { key: 'pente', label: 'Kaizen', max: 20, color: 'bg-sky-500' },
  { key: 'resilience', label: 'Résilience', max: 10, color: 'bg-amber-400' },
  { key: 'heijunka', label: 'Heijunka', max: 10, color: 'bg-violet-500' },
]

const SCALE = 108 // total max affichable (100 + bonus)

export default function BreakdownChart({ breakdown }) {
  if (!breakdown) return null
  const bonus = breakdown.bonus_malus || 0

  return (
    <div className="w-full">
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-slate-800">
        {SEGMENTS.map((s) => {
          const w = ((breakdown[s.key] || 0) / SCALE) * 100
          return (
            <div
              key={s.key}
              title={`${s.label} : ${breakdown[s.key]}/${s.max} pts`}
              className={`${s.color} transition-all duration-700 ease-out`}
              style={{ width: `${w}%` }}
            />
          )
        })}
        {bonus < 0 && (
          <div
            title={`Malus : ${bonus} pts`}
            className="bg-rose-600 transition-all duration-700"
            style={{ width: `${(Math.abs(bonus) / SCALE) * 100}%` }}
          />
        )}
      </div>
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-slate-400">
        {SEGMENTS.map((s) => (
          <span key={s.key} className="flex items-center gap-1">
            <span className={`inline-block h-2 w-2 rounded-full ${s.color}`} />
            {s.label}{' '}
            <span className="text-slate-200">{breakdown[s.key] ?? 0}</span>
          </span>
        ))}
        {bonus !== 0 && (
          <span
            className={`flex items-center gap-1 ${bonus > 0 ? 'text-emerald-400' : 'text-rose-400'}`}
          >
            {bonus > 0 ? 'Bonus' : 'Malus'} <span>{bonus}</span>
          </span>
        )}
      </div>
    </div>
  )
}
