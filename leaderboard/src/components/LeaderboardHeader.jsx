export default function LeaderboardHeader({ lastUpdate }) {
  return (
    <header className="app-header">
      <div className="header-inner flex-wrap">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            🏭
          </span>
          <div>
            <span className="eyebrow">TPS CHALLENGE</span>
            <h1 className="text-2xl font-semibold tracking-tight text-[var(--color-foreground-primary)]">
              Leaderboard
            </h1>
            <p className="mt-1 text-sm text-[var(--color-foreground-secondary)]">
              La qualité n'est pas contrôlée. Elle est construite.
            </p>
          </div>
        </div>
        {lastUpdate && (
          <div className="flex items-center gap-2 text-xs text-[var(--color-foreground-secondary)]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[var(--color-fill-success-default)] opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[var(--color-fill-success-default)]" />
            </span>
            maj {lastUpdate.toLocaleTimeString('fr-FR')}
          </div>
        )}
      </div>
    </header>
  )
}
