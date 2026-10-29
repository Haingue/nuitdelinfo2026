import { useEffect, useState } from 'react'
import LeaderboardHeader from './components/LeaderboardHeader.jsx'
import ScoreComparison from './components/ScoreComparison.jsx'
import TeamDetail from './components/TeamDetail.jsx'
import TeamPodium from './components/TeamPodium.jsx'
import TeamRow from './components/TeamRow.jsx'
import { loadLeaderboard, loadHistory } from './lib/data.js'

const REFRESH_MS = 60_000 // rafraîchissement toutes les 60 s en local

export default function App() {
  const [teams, setTeams] = useState([])
  const [history, setHistory] = useState({})
  const [prevRanks, setPrevRanks] = useState(null)
  const [lastUpdate, setLastUpdate] = useState(null)
  const [selected, setSelected] = useState(null)

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
      <LeaderboardHeader lastUpdate={lastUpdate} />

      {/* Podium */}
      {podium.length > 0 && (
        <TeamPodium teams={podium} onSelect={setSelected} />
      )}

      {/* Liste */}
      <main className="mx-auto mt-8 max-w-5xl px-6 pb-16">
        <ScoreComparison history={history} />
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
