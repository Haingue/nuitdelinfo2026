import { useEffect, useRef } from 'react'
import Phaser from 'phaser'
import { KartScene, GAME_WIDTH, GAME_HEIGHT } from './Game' // exporte la scène et les constantes

export default function KartGame({onClose}) {
  const containerRef = useRef<HTMLDivElement>(null)
  const gameRef = useRef<Phaser.Game | null>(null)

  useEffect(() => {
    const onKey = (event) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    if (!containerRef.current || gameRef.current) return

    gameRef.current = new Phaser.Game({
      type: Phaser.AUTO,
      width: GAME_WIDTH,
      height: GAME_HEIGHT,
      parent: containerRef.current,
      backgroundColor: '#111111',
      scene: KartScene,
      scale: { mode: Phaser.Scale.FIT, autoCenter: Phaser.Scale.CENTER_BOTH },
    })

    return () => {
      gameRef.current?.destroy(true)
      gameRef.current = null
    }
  }, [])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="animate-slide-up relative max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-2xl border border-[var(--color-border-default)] bg-[var(--color-component-surface-subtle)] p-6 shadow-2xl"
        onClick={e=>e.stopPropagation()}
        >
        <h1 className="mb-3 text-center font-bold text-xl text-[var(--color-foreground-secondary)]">
          🏎️ Kart Racer
        </h1>
        <div
          ref={containerRef}
          className="mx-auto w-full max-w-[720px] aspect-[3/2] overflow-hidden rounded-lg"
          style={{ width: '100%', maxWidth: '720px', aspectRatio: '3 / 2' }}
        />
        <p className="mt-3 text-center text-sm text-[var(--color-foreground-secondary)]">
          Flèches ↑ ↓ ou clic haut/bas pour changer de lane
        </p>
        <button
          onClick={onClose}
          className="mt-6 w-full rounded-lg border border-[var(--color-border-default)] py-2 text-sm
            text-[var(--color-foreground-primary)] transition-colors hover:border-[var(--color-border-neutral-default)] hover:bg-[var(--color-component-surface-muted)]"
        >
          Fermer (Échap)
        </button>
      </div>
    </div>
  )
}
