import { useState } from 'react'

const MASCOTS = [
  { src:'mascot_qual-e.png', direction: false },
  { src:'mascot_cyberio.png', direction: false },
  { src:'mascot_ecobaboy.png', direction: true },
  { src:'mascot_mamoro.png', direction: false },
  { src:'mascot_toyaya.png', direction: true },
  { src:'mascot_toyoyo.png', direction: false },
]

export default function MascotCrossing() {
  const [mascot] = useState(() => {
    if (Math.random() >= 1 / 1) return null
    return MASCOTS[Math.floor(Math.random() * MASCOTS.length)]
  })
  const [loaded, setLoaded] = useState(false)

  if (!mascot) return null

  return (
    <div className="mascot-crossing" aria-hidden="true">
      <img
        className={`mascot-crossing-image${loaded ? ' is-loaded' : ''}${mascot.direction ? ' is-reversed' : ''}`}
        src={`${import.meta.env.BASE_URL}mascots/${mascot.src}`}
        alt=""
        draggable="false"
        onLoad={() => setLoaded(true)}
      />
    </div>
  )
}
