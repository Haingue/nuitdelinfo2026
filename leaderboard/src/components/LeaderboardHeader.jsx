import { useState } from 'react'

export default function LeaderboardHeader({ lastUpdate }) {
  const [toyoyoLoaded, setToyoyoLoaded] = useState(false)
  const [toyayaLoaded, setToyayaLoaded] = useState(false)

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
        <div className="header-mascot-actions">
          <div className="header-mascots" aria-hidden="true">
            <img
              className={`mascot mascot-toyoyo${toyoyoLoaded ? ' is-loaded' : 'hidden'}`}
              src={`${import.meta.env.BASE_URL}mascots/mascot_toyoyo.png`}
              alt=""
              draggable="false"
              onLoad={() => setToyoyoLoaded(true)}
            />
            <img
              className={`mascot mascot-toyaya${toyayaLoaded ? ' is-loaded' : 'hidden'}`}
              src={`${import.meta.env.BASE_URL}mascots/mascot_toyaya.png`}
              alt=""
              draggable="false"
              onLoad={() => setToyayaLoaded(true)}
            />
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
      </div>
    </header>
  )
}
