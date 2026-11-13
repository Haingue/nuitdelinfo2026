import { toSeries } from '../lib/data.js'

export default function Sparkline({ points, width = 140, height = 36 }) {
  const series = toSeries(points)
  if (series.length < 2) return null

  const values = series.map((s) => s.total)
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  const stepX = width / (values.length - 1)

  const coords = values.map((v, i) => {
    const x = i * stepX
    const y = height - ((v - min) / span) * (height - 4) - 2
    return [x, y]
  })

  const path = coords.map(([x, y]) => `${x},${y}`).join(' ')
  const last = coords[coords.length - 1]

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      className="overflow-visible"
    >
      <polyline
        points={path}
        fill="none"
        stroke="var(--color-fill-primary-default)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx={last[0]} cy={last[1]} r="3" fill="var(--color-fill-primary-default)">
        <animate
          attributeName="r"
          values="3;5;3"
          dur="1.6s"
          repeatCount="indefinite"
        />
      </circle>
    </svg>
  )
}
