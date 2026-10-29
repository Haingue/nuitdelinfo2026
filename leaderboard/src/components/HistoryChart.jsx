import { toSeries } from '../lib/data.js'

const SERIES = [
  { key: 'total', label: 'Total', color: '#e2e8f0', dash: '6 3' },
  { key: 'qualite', label: 'Qualité', color: '#10b981', dash: null },
  { key: 'pente', label: 'Kaizen', color: '#0ea5e9', dash: null },
  { key: 'resilience', label: 'Résilience', color: '#fbbf24', dash: null },
  { key: 'heijunka', label: 'Heijunka', color: '#a78bfa', dash: null },
  { key: 'bonus_malus', label: 'Bonus/Malus', color: '#f43f5e', dash: null },
]

const W = 720,
  H = 300,
  PAD = { t: 16, r: 16, b: 34, l: 40 }

export default function HistoryChart({ snapshots }) {
  const series = toSeries(snapshots)
  if (series.length < 2)
    return (
      <p className="text-sm text-slate-500">
        Pas encore assez de mesures — revenez après le prochain batch (15 min).
      </p>
    )

  const values = series.flatMap((s) => SERIES.map((c) => s[c.key] ?? 0))
  const min = Math.min(0, ...values)
  const max = Math.max(...values, 10) * 1.1

  const innerW = W - PAD.l - PAD.r
  const innerH = H - PAD.t - PAD.b
  const stepX = innerW / (series.length - 1)
  const y = (v) => PAD.t + innerH - ((v - min) / (max - min)) * innerH
  const x = (i) => PAD.l + i * stepX

  const gridVals = [0, max / 2, max]

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="min-w-[560px]">
        {/* grille horizontale + labels */}
        {gridVals.map((v, gi) => (
          <g key={gi}>
            <line
              x1={PAD.l}
              x2={W - PAD.r}
              y1={y(v)}
              y2={y(v)}
              stroke="#1e293b"
              strokeWidth="1"
            />
            <text
              x={PAD.l - 6}
              y={y(v) + 4}
              textAnchor="end"
              fontSize="10"
              fill="#64748b"
            >
              {Math.round(v)}
            </text>
          </g>
        ))}

        {/* axe temporel */}
        {series.map((s, i) =>
          s.ts ? (
            <text
              key={i}
              x={x(i)}
              y={H - 10}
              textAnchor="middle"
              fontSize="10"
              fill="#64748b"
            >
              {String(s.ts).slice(5, 16)}
            </text>
          ) : null,
        )}

        {/* courbes */}
        {SERIES.map((c) => {
          const pts = series
            .map((s, i) => `${x(i)},${y(s[c.key] ?? 0)}`)
            .join(' ')
          return (
            <g key={c.key}>
              {c.dash ? (
                <polyline
                  points={pts}
                  fill="none"
                  stroke={c.color}
                  strokeWidth="2"
                  strokeDasharray={c.dash}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              ) : (
                <polyline
                  points={pts}
                  fill="none"
                  stroke={c.color}
                  strokeWidth="1.6"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              )}
              {series.map((s, i) => (
                <circle
                  key={i}
                  cx={x(i)}
                  cy={y(s[c.key] ?? 0)}
                  r="2.5"
                  fill={c.color}
                >
                  <title>{`${c.label} — ${s.ts ?? ''} : ${s[c.key] ?? 0} pts`}</title>
                </circle>
              ))}
            </g>
          )
        })}
      </svg>

      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs">
        {SERIES.map((c) => (
          <span
            key={c.key}
            className="flex items-center gap-1.5 text-slate-400"
          >
            <span
              className="inline-block h-2 w-4 rounded"
              style={{ background: c.color }}
            />
            {c.label}
            <span className="text-slate-200">
              {series[series.length - 1][c.key] ?? 0}
            </span>
          </span>
        ))}
      </div>
    </div>
  )
}
