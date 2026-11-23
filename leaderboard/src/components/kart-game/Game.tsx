// Game.tsx — Kart Racer : autoroute horizontale à 3 voies, défilement de droite à gauche.
// Le kart est fixe à gauche, les obstacles arrivent de la droite. Score + vitesse croissante.
// Remplace les placeholders (makePlaceholder) par tes sprites PNG dans src/assets/.

import Phaser from 'phaser'
import KartSprtie from '../../assets/sprite_cheets/mascot_cyberio_sprite_sheet.png'

const GAME_WIDTH = 720
const GAME_HEIGHT = 480
const BACKGROUD_HEIGHT = 768
const LANE_COUNT = 3
const ROAD_TOP = 95 // Limite haute de la 1re voie (juste sous la glissière/bord haut)
const ROAD_BOTTOM = 385 // Limite basse de la 3e voie (juste au-dessus de la glissière/bord bas)
const PLAYABLE_ROAD_HEIGHT = ROAD_BOTTOM - ROAD_TOP
const LANE_HEIGHT = PLAYABLE_ROAD_HEIGHT / LANE_COUNT
const KART_SIZE = 100
const OBSTACLE_SIZE = 110
const KART_X = 140 // position horizontale fixe du kart
const KART_FRAME_NUMBER = 6
const KART_TYPES = 5
const BASE_SPEED = 220 // px/s au départ
const MAX_SPEED = 700
const SPEED_RAMP = 12 // px/s gagnés par seconde
const SPAWN_INTERVAL = 1400 // ms entre deux obstacles (diminue avec la vitesse)

class KartScene extends Phaser.Scene {
  private kart!: Phaser.GameObjects.Sprite
  private road!: Phaser.GameObjects.TileSprite
  private obstacles!: Phaser.GameObjects.Group
  private scoreText!: Phaser.GameObjects.Text
  private score = 0
  private speed = BASE_SPEED
  private nextSpawnAt = 0
  private cursors!: Phaser.Types.Input.Keyboard.CursorKeys
  private upKey!: Phaser.Input.Keyboard.Key
  private downKey!: Phaser.Input.Keyboard.Key
  private spaceKey!: Phaser.Input.Keyboard.Key
  private rKey!: Phaser.Input.Keyboard.Key
  private pauseText!: Phaser.GameObjects.Text
  private isPaused = false
  private gameOver = false
  private roadDeceleration = 0

  constructor() {
    super('kart')
  }

  preload(): void {
    const KART_TYPE = Math.floor(Math.random() * KART_TYPES) // Choisit un type de kart aléatoire à chaque partie
    this.load.spritesheet(
      'kart',
      // new URL('/sprite_cheets/mascot_cyberio_sprite_sheet.png', import.meta.url)
      new URL('/sprite_cheets/players.png', import.meta.url).href,
      {
        frameWidth: 424,
        frameHeight: 281,
        startFrame: KART_TYPE * KART_FRAME_NUMBER,
        endFrame: KART_TYPE * KART_FRAME_NUMBER + KART_FRAME_NUMBER - 1,
      },
    )
    this.load.spritesheet(
      'obstacle',
      new URL('/sprite_cheets/obstacle.png', import.meta.url).href,
      { frameWidth: 498, frameHeight: 203 },
    )
    this.load.spritesheet(
      'road',
      new URL('/sprite_cheets/background.png', import.meta.url).href,
      { frameWidth: 1378, frameHeight: BACKGROUD_HEIGHT },
    )

    // Placeholders (dessinés via CanvasTexture) pour tester sans assets :
    //this.makePlaceholder('kart', 0x3b82f6, KART_SIZE);
    //this.makePlaceholder('obstacle', 0xef4444, OBSTACLE_SIZE);
  }

  private makePlaceholder(key: string, color: number, size: number): void {
    if (this.textures.exists(key)) return
    const canvasTex = this.textures.createCanvas(key, size, size)
    if (!canvasTex) return
    const ctx = canvasTex.getContext()
    const r = Math.round(size * 0.2)
    ctx.fillStyle = '#' + color.toString(16).padStart(6, '0')
    ctx.beginPath()
    ctx.roundRect(4, 4, size - 8, size - 8, r)
    ctx.fill()
    ctx.strokeStyle = 'rgba(255,255,255,0.8)'
    ctx.lineWidth = 4
    ctx.stroke()
    canvasTex.refresh()
  }

  create(): void {
    // Route : TileSprite qui défileront en boucle (l'image 1378xBACKGROUD_HEIGHT est répétée horizontalement)
    this.road = this.add
      .tileSprite(0, 0, GAME_WIDTH, GAME_HEIGHT, 'road')
      .setOrigin(0, 0)
      .setDepth(-1)
    // Mise à l'échelle : la frame fait BACKGROUD_HEIGHTpx de haut, le jeu 480px
    const roadScale = GAME_HEIGHT / BACKGROUD_HEIGHT
    this.road.setTileScale(roadScale, roadScale)

    // Kart : fixe sur l'axe X, se déplace seulement entre les voies (Y)
    this.kart = this.add
      .sprite(KART_X, this.laneY(1), 'kart', 0)
      .setDisplaySize(KART_SIZE, KART_SIZE)
    this.kart.lane = 1

    this.obstacles = this.add.group()

    this.score = 0
    this.speed = BASE_SPEED
    this.gameOver = false
    this.isPaused = false
    this.scoreText = this.add
      .text(16, 16, 'Score : 0', { fontSize: '28px', color: '#ffffff' })
      .setDepth(10)

    this.cursors = this.input.keyboard!.createCursorKeys()
    this.upKey = this.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.UP)
    this.downKey = this.input.keyboard!.addKey(
      Phaser.Input.Keyboard.KeyCodes.DOWN,
    )
    this.spaceKey = this.input.keyboard!.addKey(
      Phaser.Input.Keyboard.KeyCodes.SPACE,
    )
    this.rKey = this.input.keyboard!.addKey(Phaser.Input.Keyboard.KeyCodes.R)

    // Overlay de pause (masqué au départ)
    this.pauseText = this.add
      .text(GAME_WIDTH / 2, GAME_HEIGHT / 2, 'Pause\nEspace pour reprendre', {
        fontSize: '36px',
        color: '#ffffff',
        align: 'center',
      })
      .setOrigin(0.5)
      .setDepth(10)
      .setVisible(false)

    // Clic / tap sur la moitié haute ou basse de l'écran (mobile)
    this.input.on('pointerdown', (p: Phaser.Input.Pointer) => {
      if (this.gameOver) return
      this.moveKart(p.y < GAME_HEIGHT / 2 ? -1 : 1)
    })
  }

  update(time: number, delta: number): void {
    const dt = delta / 1000
    if (this.gameOver) {
      // Ralentissement progressif de la route après le crash
      if (this.roadDeceleration > 0) {
        this.road.tilePositionX += this.roadDeceleration * dt
        this.roadDeceleration = Math.max(0, this.roadDeceleration - 600 * dt)
      }
      return
    }

    // Pause avec Espace (pendant la partie uniquement)
    if (Phaser.Input.Keyboard.JustDown(this.spaceKey)) {
      this.isPaused = !this.isPaused
      this.pauseText.setVisible(this.isPaused)
    }
    // Restart avec R (à tout moment)
    if (Phaser.Input.Keyboard.JustDown(this.rKey)) {
      this.scene.restart()
      return
    }

    if (this.isPaused) return

    if (
      Phaser.Input.Keyboard.JustDown(this.upKey) ||
      Phaser.Input.Keyboard.JustDown(this.cursors.up)
    ) {
      this.moveKart(-1)
    }
    if (
      Phaser.Input.Keyboard.JustDown(this.downKey) ||
      Phaser.Input.Keyboard.JustDown(this.cursors.down)
    ) {
      this.moveKart(1)
    }

    // Accélération progressive
    this.speed = Math.min(MAX_SPEED, this.speed + SPEED_RAMP * dt)

    // Défilement de la route en boucle (vers la gauche)
    this.road.tilePositionX += this.speed * dt

    // Sprite du kart selon la vitesse : frames 0 (lent) à 3 (rapide)
    let kartFrame = 0
    if (this.speed > 550) {
      kartFrame = 5 // Turbo / vitesse max
    } else if (this.speed > 400) {
      kartFrame = 2 // Vitesse rapide
    } else if (this.speed > 250) {
      kartFrame = 1 // Vitesse moyenne
    } else {
      kartFrame = 0 // Vitesse lente
    }
    // Exemple si tu ajoutes une gestion du freinage (touche BAS ou flèche bas) :
    if (this.upKey.isDown || this.downKey.isDown) {
      kartFrame = 3 // Freinage
    }
    this.kart.setFrame(kartFrame)

    // Spawn des obstacles à droite de l'écran
    if (time > this.nextSpawnAt) {
      this.spawnObstacle()
      this.nextSpawnAt =
        time + Math.max(500, SPAWN_INTERVAL * (BASE_SPEED / this.speed))
    }

    // Défilement vers la gauche + score
    for (const ob of this.obstacles.getChildren() as Phaser.GameObjects.Image[]) {
      ob.x -= this.speed * dt
      if (!ob.getData('counted') && ob.x < this.kart.x - KART_SIZE) {
        ob.setData('counted', true)
        this.score += 1
        this.scoreText.setText(`Score : ${this.score}`)
      }
      // Collision (AABB simplifiée)
      if (
        Math.abs(ob.x - this.kart.x) < (OBSTACLE_SIZE + KART_SIZE) / 2 - 20 &&
        Math.abs(ob.y - this.kart.y) < (OBSTACLE_SIZE + KART_SIZE) / 2 - 20
      ) {
        this.endGame()
        return
      }
    }

    // Nettoyage des obstacles sortis à gauche
    this.obstacles.getChildren().forEach((ob) => {
      if ((ob as Phaser.GameObjects.Image).x < -OBSTACLE_SIZE) ob.destroy()
    })
  }

  private laneY(lane: number): number {
    const clampedLane = Phaser.Math.Clamp(lane, 0, LANE_COUNT - 1)
    return ROAD_TOP + clampedLane * LANE_HEIGHT + LANE_HEIGHT / 2
  }

  private moveKart(dir: -1 | 1): void {
    const lane = Phaser.Math.Clamp(
      (this.kart.lane as number) + dir,
      0,
      LANE_COUNT - 1,
    )
    if (lane === this.kart.lane) return
    this.kart.lane = lane
    this.tweens.add({
      targets: this.kart,
      y: this.laneY(lane),
      duration: 120,
      ease: 'Quad.easeOut',
    })
  }

  private spawnObstacle(): void {
    const lanes = [0, 1, 2]
    // 25% de chance de spawner sur la voie du joueur pour garder la pression
    const freeLane =
      Math.random() < 0.25 ? (this.kart.lane as number) : undefined
    const lane = freeLane ?? Phaser.Utils.Array.GetRandom(lanes)
    const ob = this.add
      .image(GAME_WIDTH + OBSTACLE_SIZE, this.laneY(lane), 'obstacle')
      .setDisplaySize(OBSTACLE_SIZE, OBSTACLE_SIZE)
    ob.lane = lane
    ob.setData('counted', false)
    this.obstacles.add(ob)
  }

  private endGame(): void {
    this.gameOver = true
    this.roadDeceleration = this.speed * 0.6 // La route continue de glisser un peu

    // 1. Tremblement de caméra à l'impact
    this.cameras.main.shake(250, 0.015)

    // 2. Animation du kart (freinage + petit tête-à-queue)
    this.kart.setFrame(3)
    this.tweens.add({
      targets: this.kart,
      angle: -25,
      x: this.kart.x - 20,
      duration: 400,
      ease: 'Back.easeOut',
    })

    // 3. Fond sombre semi-transparent en fondu
    const overlay = this.add
      .rectangle(
        GAME_WIDTH / 2,
        GAME_HEIGHT / 2,
        GAME_WIDTH,
        GAME_HEIGHT,
        0x000000,
        0,
      )
      .setDepth(9)

    this.tweens.add({
      targets: overlay,
      fillAlpha: 0.65,
      duration: 400,
    })

    // 4. Message de félicitations adaptatif avec effet de rebond
    const titleMsg =
      this.score >= 15
        ? 'Incroyable course !'
        : this.score >= 5
          ? 'Bien joué !'
          : 'Belle tentative !'
    const titleText = this.add
      .text(GAME_WIDTH / 2, GAME_HEIGHT / 2 - 70, titleMsg, {
        fontSize: '42px',
        fontStyle: 'bold',
        color: '#fbbf24', // Jaune doré
        stroke: '#000000',
        strokeThickness: 6,
      })
      .setOrigin(0.5)
      .setScale(0)
      .setDepth(10)

    this.tweens.add({
      targets: titleText,
      scale: 1,
      duration: 500,
      ease: 'Back.easeOut',
    })

    // 5. Compteur de score animé (défile de 0 jusqu'au score final)
    const scoreDisplay = this.add
      .text(GAME_WIDTH / 2, GAME_HEIGHT / 2, 'Score : 0', {
        fontSize: '36px',
        fontStyle: 'bold',
        color: '#ffffff',
        stroke: '#000000',
        strokeThickness: 4,
      })
      .setOrigin(0.5)
      .setAlpha(0)
      .setDepth(10)

    this.tweens.add({
      targets: scoreDisplay,
      alpha: 1,
      duration: 300,
      delay: 200,
    })

    const counter = { val: 0 }
    this.tweens.add({
      targets: counter,
      val: this.score,
      duration: Math.min(1200, Math.max(400, this.score * 60)), // Dure entre 0.4s et 1.2s selon le score
      delay: 250,
      ease: 'Power2',
      onUpdate: () => {
        scoreDisplay.setText(`Score : ${Math.floor(counter.val)}`)
      },
    })

    // 6. Invite à rejouer clignotante
    const restartText = this.add
      .text(
        GAME_WIDTH / 2,
        GAME_HEIGHT / 2 + 75,
        'Appuie sur Espace, Entrée ou clique pour rejouer',
        {
          fontSize: '20px',
          color: '#e2e8f0',
        },
      )
      .setOrigin(0.5)
      .setAlpha(0)
      .setDepth(10)

    this.tweens.add({
      targets: restartText,
      alpha: 1,
      duration: 400,
      delay: 600,
      onComplete: () => {
        // Effet de pulsation douce
        this.tweens.add({
          targets: restartText,
          alpha: 0.4,
          duration: 700,
          yoyo: true,
          repeat: -1,
        })
      },
    })

    // 7. Activation des contrôles de redémarrage après 500ms (évite les clics accidentels)
    this.time.delayedCall(500, () => {
      this.input.keyboard!.once('keydown-SPACE', () => this.scene.restart())
      this.input.once('pointerdown', () => this.scene.restart())
      this.input.keyboard!.once('keydown-ENTER', () => this.scene.restart())
    })
  }
}

export {
  KartScene,
  GAME_WIDTH,
  GAME_HEIGHT,
  LANE_COUNT,
  LANE_HEIGHT,
  KART_SIZE,
  OBSTACLE_SIZE,
  KART_X,
  BASE_SPEED,
  MAX_SPEED,
  SPEED_RAMP,
  SPAWN_INTERVAL,
}
