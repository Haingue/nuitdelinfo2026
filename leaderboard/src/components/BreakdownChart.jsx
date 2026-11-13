const SEGMENTS = [
  { key: 'qualite', label: 'Qualité', max: 60, color: 'bg-[var(--color-fill-success-default)]' },
  { key: 'pente', label: 'Kaizen', max: 20, color: 'bg-[var(--color-fill-info-subtle)]' },
  { key: 'resilience', label: 'Résilience', max: 10, color: 'bg-[var(--color-fill-warning-default)]' },
  { key: 'heijunka', label: 'Heijunka', max: 10, color: 'bg-[var(--color-core-indigo-400)]' },
]

const SCALE = 108 // total max affichable (100 + bonus)

export default function BreakdownChart({ breakdown }) {
  if (!breakdown) return null
  const bonus = breakdown.bonus_malus || 0

  return (
    <div className="w-full">
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-[var(--color-component-surface-muted)]">
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
            className="bg-[var(--color-fill-error-default)] transition-all duration-700"
            style={{ width: `${(Math.abs(bonus) / SCALE) * 100}%` }}
          />
        )}
      </div>
      <div className="mt-1 flex flex-wrap gap-x-3 gap-y-0.5 text-[10px] text-[var(--color-foreground-secondary)]">
        {SEGMENTS.map((s) => (
          <span key={s.key} className="flex items-center gap-1">
            <span className={`inline-block h-2 w-2 rounded-full ${s.color}`} />
            {s.label}{' '}
            <span className="text-[var(--color-foreground-primary)]">{breakdown[s.key] ?? 0}</span>
          </span>
        ))}
        {bonus !== 0 && (
          <span
            className={`flex items-center gap-1 ${bonus > 0 ? 'text-[var(--color-foreground-success-default)]' : 'text-[var(--color-foreground-error-default)]'}`}
          >
            {bonus > 0 ? 'Bonus' : 'Malus'} <span>{bonus}</span>
          </span>
        )}
      </div>
    </div>
  )
}
