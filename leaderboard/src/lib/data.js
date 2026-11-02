// Chargement des données : leaderboard.json (produit par le batch) + scores-history.json (trajectoire).
// En local sans données, un jeu d'exemple est utilisé pour développer l'UI.

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
    details: {
      tests: {
        status: 'passed',
        detected: 12,
        failed: 0,
        frameworks: 'Vitest',
      },
      quality_breakdown: {
        gate: 20,
        maintainability: 15,
        maintainability_rating: 'A',
        security: 10,
        security_rating: 'A',
        coverage: 5,
        coverage_percent: 30,
        technical_debt_minutes: 120,
        technical_debt_ratio_percent: 2,
        code_smells: 3,
        supply_chain: 5,
        total: 55,
      },
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
    details: {
      tests: {
        status: 'failed',
        detected: 1,
        failed: 1,
        failed_tests: 3,
        frameworks: 'Spring Boot · Maven',
      },
      quality_breakdown: {
        gate: 20,
        maintainability: 10,
        maintainability_rating: 'B',
        security: 10,
        security_rating: 'A',
        coverage: 5,
        coverage_percent: 30,
        technical_debt_minutes: 180,
        technical_debt_ratio_percent: 3,
        code_smells: 8,
        supply_chain: 5,
        total: 50,
      },
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
    details: {
      tests: { status: 'not_found', detected: 0, failed: 0, frameworks: '' },
      quality_breakdown: {
        gate: 20,
        maintainability: 10,
        maintainability_rating: 'B',
        security: 6,
        security_rating: 'B',
        coverage: 4,
        coverage_percent: 24,
        technical_debt_minutes: 240,
        technical_debt_ratio_percent: 4,
        code_smells: 12,
        supply_chain: 5,
        total: 45,
      },
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
    details: {
      tests: { status: 'passed', detected: 4, failed: 0, frameworks: 'pytest' },
      quality_breakdown: {
        gate: 20,
        maintainability: 10,
        maintainability_rating: 'B',
        security: 3,
        security_rating: 'C',
        coverage: 2,
        coverage_percent: 12,
        technical_debt_minutes: 360,
        technical_debt_ratio_percent: 6,
        code_smells: 18,
        supply_chain: 5,
        total: 40,
      },
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
    details: {
      tests: { status: 'not_found', detected: 0, failed: 0, frameworks: '' },
      quality_breakdown: {
        gate: 0,
        maintainability: 10,
        maintainability_rating: 'B',
        security: 6,
        security_rating: 'B',
        coverage: 9,
        coverage_percent: 54,
        technical_debt_minutes: 300,
        technical_debt_ratio_percent: 5,
        code_smells: 15,
        supply_chain: 5,
        total: 30,
      },
    },
  },
]

// snapshots d'exemple (format identique à celui produit par scoring.py) :
// [{ ts, total, qualite, pente, resilience, heijunka, bonus_malus }, ...]
function snap(ts, total, q, p, r, h, b) {
  return {
    ts,
    total,
    qualite: q,
    pente: p,
    resilience: r,
    heijunka: h,
    bonus_malus: b,
  }
}

const SAMPLE_HISTORY = {
  'Kaizen Warriors': [
    snap('20:00', 12, 8, 0, 2.5, 1.5, 0),
    snap('21:00', 21, 14, 2.5, 2.5, 2.0, 0),
    snap('22:00', 28, 20, 4.0, 2.5, 1.5, 0),
    snap('23:00', 38, 28, 6.0, 5.0, 1.5, -2.5),
    snap('00:00', 45, 35, 8.0, 5.0, 4.0, -7),
    snap('01:00', 52, 40, 12.5, 7.5, 6.2, -14),
    snap('02:00', 65, 45, 15.0, 7.5, 7.0, -9.5),
    snap('03:00', 78, 50, 17.0, 7.5, 8.2, -4.7),
    snap('04:00', 86, 52, 18.5, 7.5, 8.2, 0),
    snap('05:00', 92.5, 55.0, 18.5, 7.5, 8.2, 3.0),
  ],
  'Jidoka Squad': [
    snap('20:00', 20, 15, 0, 0, 5.0, 0),
    snap('21:00', 25, 18, 1.0, 2.5, 3.5, 0),
    snap('22:00', 29, 20, 2.0, 2.5, 4.5, 0),
    snap('23:00', 35, 25, 4.0, 2.5, 3.5, 0),
    snap('00:00', 40, 28, 6.0, 2.5, 3.5, 0),
    snap('01:00', 44, 30, 8.0, 2.5, 3.5, 0),
    snap('02:00', 48, 33, 10.0, 5.0, 4.5, -4.5),
    snap('03:00', 55, 38, 12.0, 5.0, 5.0, -5),
    snap('04:00', 72, 45, 15.0, 7.5, 6.0, -1.5),
    snap('05:00', 84, 50, 15.0, 10.0, 6.0, 3),
  ],
  'Heijunka Team': [
    snap('20:00', 8, 5, 0, 0, 3.0, 0),
    snap('21:00', 11, 7, 0.5, 0, 3.5, 0),
    snap('22:00', 16, 10, 1.5, 2.5, 2.0, 0),
    snap('23:00', 20, 13, 2.5, 2.5, 2.0, 0),
    snap('00:00', 25, 16, 4.0, 2.5, 2.5, 0),
    snap('01:00', 29, 18, 5.5, 2.5, 3.0, 0),
    snap('02:00', 33, 21, 7.0, 2.5, 2.5, 0),
    snap('03:00', 38, 24, 8.5, 2.5, 3.0, 0),
    snap('04:00', 55, 35, 11.0, 5.0, 4.0, 0),
    snap('05:00', 71.5, 45, 12.0, 5.0, 9.5, 0.5),
  ],
  'Muda Hunters': [
    snap('20:00', 5, 3, 0, 0, 2.0, 0),
    snap('21:00', 9, 5, 0.5, 0, 3.5, 0),
    snap('22:00', 12, 7, 1.0, 0, 4.0, 0),
    snap('23:00', 15, 9, 1.5, 2.5, 2.0, 0),
    snap('00:00', 18, 11, 2.0, 2.5, 2.5, 0),
    snap('01:00', 21, 13, 2.5, 2.5, 3.0, 0),
    snap('02:00', 24, 15, 3.0, 2.5, 3.5, 0),
    snap('03:00', 27, 17, 4.0, 2.5, 3.5, 0),
    snap('04:00', 30, 19, 4.5, 2.5, 4.0, 0),
    snap('05:00', 58, 40, 8.0, 5.0, 5.0, 0),
  ],
  'Poka-Yoke Fan': [
    snap('20:00', 2, 1, 0, 0, 1.0, 0),
    snap('21:00', 4, 2, 0, 0, 2.0, 0),
    snap('22:00', 5, 3, 0, 0, 2.0, 0),
    snap('23:00', 6, 4, 0.5, 0, 1.5, 0),
    snap('00:00', 8, 5, 1.0, 0, 2.0, 0),
    snap('01:00', 10, 6, 1.5, 0, 2.5, 0),
    snap('02:00', 11, 7, 1.5, 0, 2.5, 0),
    snap('03:00', 12, 8, 2.0, 0, 2.0, 0),
    snap('04:00', 13, 9, 2.0, 0, 2.0, 0),
    snap('05:00', 42, 30, 5.0, 2.5, 4.5, 0),
  ],
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

// Normalise une série d'historique : nombres simples (ancien format) ou snapshots.
export function toSeries(historyEntry = []) {
  return historyEntry.map((s) =>
    typeof s === 'number' ? { ts: null, total: s } : s,
  )
}
