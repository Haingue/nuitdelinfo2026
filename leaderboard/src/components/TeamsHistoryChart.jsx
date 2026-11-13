const METRICS = [
  { key: 'total', label: 'Total' },
  { key: 'qualite', label: 'Qualité' },
  { key: 'pente', label: 'Kaizen' },
  { key: 'resilience', label: 'Résilience' },
  { key: 'heijunka', label: 'Heijunka' },
  { key: 'bonus_malus', label: 'Bonus / malus' },
]

const TEAM_COLORS = [
  'var(--color-core-red-500)',
  'var(--color-core-blue-500)',
  'var(--color-core-green-700)',
  'var(--color-core-copper-500)',
  'var(--color-core-indigo-400)',
  'var(--color-core-teal-1400)',
  'var(--color-core-yellow-700)',
  'var(--color-core-red-700)',
  'var(--color-core-blue-600)',
  'var(--color-core-green-600)',
  'var(--color-core-copper-400)',
  'var(--color-core-indigo-500)',
  'var(--color-core-teal-1200)',
  'var(--color-core-yellow-600)',
  'var(--color-core-red-300)',
  'var(--color-core-blue-400)',
  'var(--color-core-aqua-1100)',
  'var(--color-core-grey-800)',
]

const W = 960
const H = 390
const PAD = { top: 24, right: 24, bottom: 52, left: 56 }

function timestamp(snapshot, index, previous) {
  const parsed = Date.parse(snapshot.ts)
  if (Number.isFinite(parsed)) return parsed

  const timeOnly = /^(\d{1,2}):(\d{2})$/.exec(snapshot.ts ?? '')
  if (!timeOnly) return index

  const minute = Number(timeOnly[1]) * 60 + Number(timeOnly[2])
  const day =
    previous && minute < previous.minute
      ? previous.day + 1
      : (previous?.day ?? 0)
  return { value: day * 1440 + minute, minute, day }
}

function formatTime(value, usesClockMinutes) {
  if (usesClockMinutes) {
    const minutes = value % 1440
    return `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`
  }
  return new Date(value).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function TeamsHistoryChart({ history, metric }) {
  const selectedMetric =
    METRICS.find((item) => item.key === metric) ?? METRICS[0]
  let usesClockMinutes = false

  const teams = Object.entries(history)
    .map(([name, snapshots], teamIndex) => {
      let previous
      const points = snapshots
        .map((snapshot, index) => {
          const time = timestamp(snapshot, index, previous)
          if (typeof time === 'object') {
            previous = time
            usesClockMinutes = true
            return {
              time: time.value,
              value: Number(snapshot[selectedMetric.key] ?? 0),
              label: snapshot.ts,
            }
          }
          return {
            time,
            value: Number(snapshot[selectedMetric.key] ?? 0),
            label: snapshot.ts,
          }
        })
        .filter(
          (point) =>
            Number.isFinite(point.time) && Number.isFinite(point.value),
        )

      return {
        name,
        points,
        color: TEAM_COLORS[teamIndex % TEAM_COLORS.length],
      }
    })
    .filter((team) => team.points.length > 0)

  const allPoints = teams.flatMap((team) => team.points)
  if (allPoints.length === 0) {
    return (
      <p className="py-16 text-center text-sm text-[var(--color-foreground-secondary)]">
        Aucune donnée historique disponible.
      </p>
    )
  }

  const minTime = Math.min(...allPoints.map((point) => point.time))
  const maxTime = Math.max(...allPoints.map((point) => point.time))
  const minValue = Math.min(0, ...allPoints.map((point) => point.value))
  const maxValue = Math.max(1, ...allPoints.map((point) => point.value))
  const valueRange = maxValue - minValue || 1
  const timeRange = maxTime - minTime || 1
  const innerW = W - PAD.left - PAD.right
  const innerH = H - PAD.top - PAD.bottom
  const x = (value) => PAD.left + ((value - minTime) / timeRange) * innerW
  const y = (value) =>
    PAD.top + innerH - ((value - minValue) / valueRange) * innerH
  const yTicks = Array.from(
    { length: 5 },
    (_, index) => minValue + (valueRange * index) / 4,
  )
  const xTicks = Array.from(
    { length: 5 },
    (_, index) => minTime + (timeRange * index) / 4,
  )

  return (
    <div>
      <div className="w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="min-w-[700px]"
          role="img"
          aria-label={`Progression de ${selectedMetric.label} pour toutes les équipes`}
        >
          {yTicks.map((tick) => (
            <g key={tick}>
              <line
                x1={PAD.left}
                x2={W - PAD.right}
                y1={y(tick)}
                y2={y(tick)}
                stroke="var(--color-border-subtle)"
              />
              <text
                x={PAD.left - 10}
                y={y(tick) + 4}
                textAnchor="end"
                fontSize="11"
                fill="var(--color-foreground-secondary)"
              >
                {tick.toFixed(1)}
              </text>
            </g>
          ))}
          {xTicks.map((tick) => (
            <g key={tick}>
              <line
                x1={x(tick)}
                x2={x(tick)}
                y1={PAD.top}
                y2={H - PAD.bottom}
                stroke="var(--color-border-subtle)"
                strokeDasharray="3 6"
              />
              <text
                x={x(tick)}
                y={H - 20}
                textAnchor="middle"
                fontSize="11"
                fill="var(--color-foreground-secondary)"
              >
                {formatTime(tick, usesClockMinutes)}
              </text>
            </g>
          ))}
          {teams.map((team) => (
            <g key={team.name}>
              {team.points.length > 1 && (
                <polyline
                  points={team.points
                    .map((point) => `${x(point.time)},${y(point.value)}`)
                    .join(' ')}
                  fill="none"
                  stroke={team.color}
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  opacity="0.85"
                />
              )}
              {team.points.map((point, index) => (
                <circle
                  key={`${team.name}-${index}`}
                  cx={x(point.time)}
                  cy={y(point.value)}
                  r="3"
                  fill={team.color}
                >
                  <title>{`${team.name} · ${point.label ?? ''} · ${point.value} pts`}</title>
                </circle>
              ))}
            </g>
          ))}
        </svg>
      </div>
      <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 border-t border-[var(--color-border-subtle)] pt-4 sm:grid-cols-3 lg:grid-cols-4">
        {teams.map((team) => (
          <li
            key={team.name}
            className="flex min-w-0 items-center gap-2 text-xs text-[var(--color-foreground-primary)]"
          >
            <span
              className="h-2 w-2 shrink-0 rounded-full"
              style={{ backgroundColor: team.color }}
            />
            <span className="truncate">{team.name}</span>
            <span className="ml-auto font-mono text-[var(--color-foreground-secondary)]">
              {team.points[team.points.length - 1].value}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

export { METRICS }
