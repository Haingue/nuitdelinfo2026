export default function LeaderboardHeader({ lastUpdate }) {
  return (
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
  )
}
