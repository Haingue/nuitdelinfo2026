const SAMPLE_LEADERBOARD = [
  {
    team: 'Kaizen Warriors',
    repo: 'kaizen-warriors/nuit-de-linfo',
    rank: 1,
    score: 92.5,
    eligible: true,
    breakdown: {
      qualite: 55.0,
      pente: 18.5,
      resilience: 7.5,
      heijunka: 8.2,
      bonus_malus: 3,
    },
  },
  {
    team: 'Jidoka Squad',
    repo: 'jidoka-squad/nuit-de-linfo',
    rank: 2,
    score: 84.0,
    eligible: true,
    breakdown: {
      qualite: 50.0,
      pente: 15.0,
      resilience: 10.0,
      heijunka: 6.0,
      bonus_malus: 3,
    },
  },
  {
    team: 'Heijunka Team',
    repo: 'heijunka-team/nuit-de-linfo',
    rank: 3,
    score: 71.5,
    eligible: true,
    breakdown: {
      qualite: 45.0,
      pente: 12.0,
      resilience: 5.0,
      heijunka: 9.5,
      bonus_malus: 0,
    },
  },
  {
    team: 'Muda Hunters',
    repo: 'muda-hunters/nuit-de-linfo',
    rank: 4,
    score: 58.0,
    eligible: true,
    breakdown: {
      qualite: 40.0,
      pente: 8.0,
      resilience: 5.0,
      heijunka: 5.0,
      bonus_malus: 0,
    },
  },
  {
    team: 'Poka-Yoke Fan',
    repo: 'poka-yoke-fan/nuit-de-linfo',
    rank: 5,
    score: 42.0,
    eligible: false,
    breakdown: {
      qualite: 30.0,
      pente: 5.0,
      resilience: 2.5,
      heijunka: 4.5,
      bonus_malus: 0,
    },
  },
]

const SAMPLE_HISTORY = {
  'Kaizen Warriors': [12, 15, 21, 24, 28, 27, 33, 38, 41, 45, 52],
  'Jidoka Squad': [20, 22, 21, 25, 30, 29, 35, 38, 40, 42, 44],
  'Heijunka Team': [8, 9, 11, 13, 16, 18, 20, 23, 25, 27, 29],
  'Muda Hunters': [5, 6, 8, 9, 11, 12, 14, 15, 17, 18, 19],
  'Poka-Yoke Fan': [2, 2, 3, 4, 4, 5, 6, 6, 7, 7, 8],
}

export async function loadLeaderboard() {
  try {
    const res = await fetch('./data/leaderboard.json', { cache: 'no-store' })
    if (!res.ok) throw new Error(String(res.status))
    return await res.json()
  } catch {
    return SAMPLE_LEADERBOARD
  }
}

export async function loadHistory() {
  try {
    const res = await fetch('./data/scores-history.json', { cache: 'no-store' })
    if (!res.ok) throw new Error(String(res.status))
    return await res.json()
  } catch {
    return SAMPLE_HISTORY
  }
}
