import { useEffect, useRef, useState } from 'react'
import Sparkline from './components/Sparkline.jsx'
import BreakdownChart from './components/BreakdownChart.jsx'
import HistoryChart from './components/HistoryChart.jsx'
import TeamsHistoryChart, { METRICS } from './components/TeamsHistoryChart.jsx'
import { loadLeaderboard, loadHistory } from './lib/data.js'

const REFRESH_MS = 60_000 // rafraîchissement toutes les 60 s en local

const MEDALS = ['🥇', '🥈', '🥉']
const PODIUM_GLOW = ['glow-gold', 'glow-silver', 'glow-bronze']
const PODIUM_ORDER = [1, 0, 2] // 2e | 1er | 3e

function useCountUp(target, duration = 800) {
  const [value, setValue] = useState(0)
  const rafRef = useRef(null)
  useEffect(() => {
    const start = performance.now()
    const from = 0
    const tick = (now) => {
      const t = Math.min((now - start) / duration, 1)
      const eased = 1 - Math.pow(1 - t, 3) // ease-out cubic
      setValue(from + (target - from) * eased)
      if (t < 1) rafRef.current = requestAnimationFrame(tick)
    }
    rafRef.current = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(rafRef.current)
  }, [target, duration])
  return value
}

// ---- Modal : suivi de progression détaillé d'une équipe ----------------
function TeamDetail({ team, history, onClose }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const snapshots = history[team.team] || []

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm animate-fade-in" />
      <div
        className="animate-slide-up relative max-h-[90vh] w-full max-w-3xl overflow-y-auto
        rounded-2xl border border-slate-700 bg-slate-900 p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-black text-slate-100">{team.team}</h2>
            {/* <a
              href={`https://github.com/${team.repo}`}
              target="_blank"
              rel="noreferrer"
              className="text-sm text-sky-400 hover:text-sky-300 transition-colors"
            >
              {team.repo} ↗
            </a> */}
          </div>
          <div className="text-right">
            <div className="font-mono text-3xl font-black text-emerald-400">
              {(team.score ?? 0).toFixed(1)}
            </div>
            <div className="text-xs text-slate-500">points · #{team.rank}</div>
          </div>
        </div>

        <div className="mt-6">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
            📈 Progression des scores dans la nuit
          </h3>
          <HistoryChart snapshots={snapshots} />
        </div>

        <div className="mt-6">
          <h3 className="mb-2 text-sm font-semibold uppercase tracking-wide text-slate-400">
            📊 Détail actuel par type de score
          </h3>
          <BreakdownChart breakdown={team.breakdown} />
        </div>

        <button
          onClick={onClose}
          className="mt-6 w-full rounded-lg border border-slate-700 py-2 text-sm
            text-slate-300 transition-colors hover:border-slate-500 hover:bg-slate-800"
        >
          Fermer (Échap)
        </button>
      </div>
    </div>
  )
}

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

function TeamRow({ team, history, prevRank, onSelect }) {
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

export default function App() {
  const [teams, setTeams] = useState([])
  const [history, setHistory] = useState({})
  const [prevRanks, setPrevRanks] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [selected, setSelected] = useState(null)
  const [showComparison, setShowComparison] = useState(false)
  const [selectedMetric, setSelectedMetric] = useState('total')

  useEffect(() => {
    let cancelled = false

    async function refresh() {
      const [lb, h] = await Promise.all([loadLeaderboard(), loadHistory()])
      if (cancelled) return
      setPrevRanks(Object.fromEntries(teams.map((t) => [t.team, t.rank])))
      setTeams(lb)
      setHistory(h)
      setLastUpdate(new Date())
    }

    refresh()
    const id = setInterval(refresh, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const podium = teams.slice(0, 3)
  const rest = teams.slice(3)

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200">
      {/* Header */}
      <header className="mx-auto max-w-5xl px-6 pt-10">
        <div className="flex items-end justify-between">
          <div>
            <h1
              className="bg-gradient-to-r from-sky-400 via-emerald-400 to-sky-400 bg-clip-text text-3xl
              font-black tracking-tight text-transparent"
            >
              🏭 TPS Challenge — Leaderboard
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              La qualité n'est pas contrôlée. Elle est construite.
            </p>
          </div>
          {lastUpdate && (
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              maj {lastUpdate.toLocaleTimeString('fr-FR')}
            </div>
          )}
        </div>
      </header>

      {/* Podium */}
      {podium.length > 0 && (
        <section className="mx-auto mt-8 grid max-w-5xl grid-cols-1 gap-4 px-6 md:grid-cols-3">
          {PODIUM_ORDER.map((placeIdx) =>
            podium[placeIdx] ? (
              <PodiumCard
                key={podium[placeIdx].team}
                team={podium[placeIdx]}
                place={placeIdx}
                onSelect={() => setSelected(podium[placeIdx])}
              />
            ) : null,
          )}
        </section>
      )}

      {/* Liste */}
      <main className="mx-auto mt-8 max-w-5xl px-6 pb-16">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <p className="text-xs text-slate-500">
            Cliquez sur une équipe pour voir sa progression détaillée.
          </p>
          <button
            type="button"
            onClick={() => setShowComparison((visible) => !visible)}
            aria-expanded={showComparison}
            className="inline-flex items-center gap-2 rounded-md border border-sky-700/70 bg-sky-950/60 px-4 py-2 text-sm font-semibold text-sky-200 transition-colors hover:border-sky-500 hover:bg-sky-900/60"
          >
            <span aria-hidden="true">{showComparison ? '▾' : '↗'}</span>
            {showComparison ? 'Masquer la comparaison' : 'Comparer les scores dans le temps'}
          </button>
        </div>
        {showComparison && (
          <section className="mb-8 border-y border-slate-800 bg-slate-900/40 py-5" aria-label="Comparaison des équipes par type de score">
            <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
              <div>
                <h2 className="text-lg font-bold text-slate-100">Progression par type de score</h2>
                <p className="mt-1 text-xs text-slate-500">Chaque courbe représente une équipe.</p>
              </div>
              <div className="flex flex-wrap gap-1" role="group" aria-label="Type de score">
                {METRICS.map((metric) => (
                  <button
                    key={metric.key}
                    type="button"
                    onClick={() => setSelectedMetric(metric.key)}
                    aria-pressed={selectedMetric === metric.key}
                    className={`rounded px-3 py-1.5 text-xs font-medium transition-colors ${selectedMetric === metric.key ? 'bg-emerald-500 text-slate-950' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'}`}
                  >
                    {metric.label}
                  </button>
                ))}
              </div>
            </div>
            <TeamsHistoryChart history={history} metric={selectedMetric} />
          </section>
        )}
        {rest.length === 0 && podium.length === 0 && (
          <p className="animate-pulse text-center text-slate-500">
            Chargement des usines…
          </p>
        )}
        <ul className="space-y-2">
          {rest.map((t) => (
            <TeamRow
              key={t.team}
              team={t}
              history={history}
              prevRank={prevRanks?.[t.team]}
              onSelect={() => setSelected(t)}
            />
          ))}
        </ul>
      </main>

      {/* Modal détail équipe */}
      {selected && (
        <TeamDetail
          team={selected}
          history={history}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}
