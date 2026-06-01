import { useState, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const FEATURES = [
  { key: 'rolling_7g_three_pointers_attempted', label: '7g 3PA',        min: 0,   max: 12,  step: 0.1,  default: 3.5,  unit: 'per game' },
  { key: 'rolling_7g_rebounds',                 label: '7g Rebounds',   min: 0,   max: 16,  step: 0.1,  default: 5.0,  unit: 'per game' },
  { key: 'rolling_7g_USG',                      label: '7g Usage %',    min: 0,   max: 45,  step: 0.5,  default: 22,   unit: '%' },
  { key: 'positionless_index',                  label: 'Positionless Index', min: 0, max: 1, step: 0.01, default: 0.45, unit: '' },
  { key: 'rolling_7g_blocks',                   label: '7g Blocks',     min: 0,   max: 4,   step: 0.05, default: 0.4,  unit: 'per game' },
  { key: 'winPercent_team',                     label: 'Team Win %',    min: 0,   max: 100, step: 1,    default: 50,   unit: '%' },
  { key: 'rolling_7g_points_per36',             label: '7g Pts/36',     min: 0,   max: 40,  step: 0.5,  default: 16,   unit: 'pts' },
  { key: 'rolling_7g_minutes',                  label: '7g Minutes',    min: 0,   max: 42,  step: 0.5,  default: 28,   unit: 'min/g' },
  { key: 'games_last_14d',                      label: 'Games (14d)',   min: 0,   max: 10,  step: 1,    default: 6,    unit: 'games' },
  { key: 'rolling_7g_assists_per36',            label: '7g Ast/36',     min: 0,   max: 14,  step: 0.1,  default: 4.5,  unit: 'ast' },
]

function riskColor(p) {
  if (p < 0.25) return '#2ecc71'
  if (p < 0.50) return '#f39c12'
  if (p < 0.75) return '#e67e22'
  return '#e74c3c'
}

function riskLabel(p) {
  if (p < 0.25) return 'LOW'
  if (p < 0.50) return 'MODERATE'
  if (p < 0.75) return 'HIGH'
  return 'VERY HIGH'
}

// Approximate SHAP-style waterfall using feature deviations from midpoints
function approximateShap(inputs, probability) {
  const midpoints = Object.fromEntries(
    FEATURES.map(f => [f.key, (f.min + f.max) / 2])
  )
  // Rough importance weights (heuristic for demo; real weights come from backend)
  const weights = {
    rolling_7g_minutes:               0.22,
    rolling_7g_USG:                   0.18,
    games_last_14d:                   0.14,
    rolling_7g_points_per36:          0.11,
    positionless_index:               0.10,
    rolling_7g_rebounds:              0.08,
    rolling_7g_three_pointers_attempted: 0.06,
    winPercent_team:                  0.05,
    rolling_7g_assists_per36:         0.04,
    rolling_7g_blocks:                0.02,
  }
  const base = 0.15
  const contributions = FEATURES.map(f => {
    const norm  = (inputs[f.key] - midpoints[f.key]) / Math.max(f.max - f.min, 0.0001)
    const w     = weights[f.key] || 0.05
    return { key: f.key, label: f.label, value: norm * w * (probability - base) * 2 }
  }).sort((a, b) => Math.abs(b.value) - Math.abs(a.value))

  return contributions.slice(0, 8)
}

export default function Dashboard() {
  const initInputs = Object.fromEntries(FEATURES.map(f => [f.key, f.default]))
  const [inputs,      setInputs]      = useState(initInputs)
  const [result,      setResult]      = useState(null)
  const [shap,        setShap]        = useState(null)
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(null)
  const [apiUsed,     setApiUsed]     = useState(false)

  const handleChange = useCallback((key, val) => {
    setInputs(prev => ({ ...prev, [key]: Number(val) }))
  }, [])

  const predict = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_URL}/predict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ features: inputs }),
      })
      if (!res.ok) throw new Error(`API error: ${res.status}`)
      const json = await res.json()
      const prob = json.injury_probability
      setResult(prob)
      setShap(json.shap_values || approximateShap(inputs, prob))
      setApiUsed(true)
    } catch {
      // Fallback: simple heuristic model
      const rawScore =
        (inputs.rolling_7g_minutes / 42) * 0.22 +
        (inputs.rolling_7g_USG / 45) * 0.18 +
        (inputs.games_last_14d / 10) * 0.14 +
        (inputs.rolling_7g_points_per36 / 40) * 0.11 +
        inputs.positionless_index * 0.10 +
        (inputs.rolling_7g_rebounds / 16) * 0.08 +
        (inputs.rolling_7g_three_pointers_attempted / 12) * 0.06 +
        ((100 - inputs.winPercent_team) / 100) * 0.05 +
        (inputs.rolling_7g_assists_per36 / 14) * 0.04 +
        (inputs.rolling_7g_blocks / 4) * 0.02
      const prob = Math.max(0.02, Math.min(0.97, rawScore * 0.8 + 0.08))
      setResult(prob)
      setShap(approximateShap(inputs, prob))
      setApiUsed(false)
      setError('Backend offline — showing heuristic estimate')
    } finally {
      setLoading(false)
    }
  }, [inputs])

  const maxAbsShap = shap ? Math.max(...shap.map(s => Math.abs(s.value)), 0.001) : 0.001

  return (
    <div className="page">
      <div className="page-title">Injury Risk <span className="accent">Dashboard</span></div>
      <div className="page-subtitle">
        Adjust the rolling-window and context features below to compute a player's estimated injury probability.
      </div>

      {error && (
        <div style={{ background: 'rgba(231,76,60,0.08)', border: '1px solid rgba(231,76,60,0.25)', borderRadius: 6, padding: '0.75rem 1rem', marginBottom: '1.2rem', fontSize: '0.82rem', color: '#e74c3c', fontFamily: 'var(--font-mono)' }}>
          ⚠ {error}
        </div>
      )}

      <div className="dashboard-grid">
        {/* Input panel */}
        <div className="input-panel">
          <h3>Feature Inputs</h3>
          {FEATURES.map(f => (
            <div className="input-group" key={f.key}>
              <label>{f.label} {f.unit && <span style={{ opacity: 0.5 }}>({f.unit})</span>}</label>
              <div className="range-row">
                <input
                  type="range"
                  min={f.min}
                  max={f.max}
                  step={f.step}
                  value={inputs[f.key]}
                  onChange={e => handleChange(f.key, e.target.value)}
                />
                <span className="range-val">{Number(inputs[f.key]).toFixed(f.step < 0.1 ? 2 : 1)}</span>
              </div>
            </div>
          ))}
          <button
            className="predict-btn"
            onClick={predict}
            disabled={loading}
          >
            {loading ? 'Computing…' : 'Compute Injury Risk'}
          </button>
          {apiUsed && result !== null && (
            <div style={{ marginTop: '0.6rem', fontSize: '0.72rem', color: 'var(--text3)', fontFamily: 'var(--font-mono)', textAlign: 'center' }}>
              ✓ CatBoost model via backend
            </div>
          )}
        </div>

        {/* Result panel */}
        <div className="result-panel">
          <h3>Prediction Output</h3>

          {result === null ? (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text3)', fontFamily: 'var(--font-mono)', fontSize: '0.82rem', textAlign: 'center', padding: '3rem 0' }}>
              Set inputs and click<br />"Compute Injury Risk"
            </div>
          ) : (
            <>
              <div className="prob-display">
                <div className="prob-value" style={{ color: riskColor(result) }}>
                  {(result * 100).toFixed(1)}%
                </div>
                <div className="prob-label" style={{ color: riskColor(result) }}>
                  {riskLabel(result)} RISK
                </div>
              </div>

              <div>
                <div style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text3)', marginBottom: '0.4rem', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Injury Probability</div>
                <div className="risk-bar-wrap">
                  <div
                    className="risk-bar-fill"
                    style={{ width: `${result * 100}%`, background: riskColor(result) }}
                  />
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', color: 'var(--text3)', fontFamily: 'var(--font-mono)', marginTop: '0.25rem' }}>
                  <span>0%</span><span>50%</span><span>100%</span>
                </div>
              </div>

              {shap && (
                <div>
                  <div style={{ fontSize: '0.78rem', fontFamily: 'var(--font-display)', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--text2)', marginBottom: '0.75rem' }}>
                    Top Contributing Factors
                  </div>
                  {shap.map((s, i) => (
                    <div className="waterfall-row" key={i}>
                      <div className="waterfall-name">{s.label}</div>
                      <div className="waterfall-bar-bg">
                        <div
                          className="waterfall-bar"
                          style={{
                            width: `${(Math.abs(s.value) / maxAbsShap) * 100}%`,
                            background: s.value > 0 ? '#e74c3c' : '#2ecc71',
                            opacity: 0.8,
                          }}
                        />
                      </div>
                      <div className="waterfall-val" style={{ color: s.value > 0 ? '#e74c3c' : '#2ecc71' }}>
                        {s.value > 0 ? '+' : ''}{(s.value * 100).toFixed(1)}%
                      </div>
                    </div>
                  ))}
                  <div style={{ fontSize: '0.68rem', color: 'var(--text3)', fontFamily: 'var(--font-mono)', marginTop: '0.75rem' }}>
                    Red = increases risk · Green = decreases risk
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>

      {/* Feature glossary */}
      <div className="section" style={{ marginTop: '3rem' }}>
        <div className="section-label">Feature Glossary</div>
        <div className="section-title">Input Definitions</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '0.6rem' }}>
          {[
            ['rolling_7g_three_pointers_attempted','Rolling 7-game avg 3-pointers attempted per game'],
            ['rolling_7g_rebounds','Rolling 7-game avg total rebounds per game'],
            ['rolling_7g_USG','Rolling 7-game usage rate (%)'],
            ['positionless_index','Positional fluidity score (0=traditional, 1=fully positionless)'],
            ['rolling_7g_blocks','Rolling 7-game avg blocks per game'],
            ['winPercent_team','Team win percentage at time of game'],
            ['rolling_7g_points_per36','Rolling 7-game avg points per 36 minutes'],
            ['rolling_7g_minutes','Rolling 7-game avg minutes played per game'],
            ['games_last_14d','Number of games played in the previous 14 days'],
            ['rolling_7g_assists_per36','Rolling 7-game avg assists per 36 minutes'],
          ].map(([key, desc]) => (
            <div key={key} style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6, padding: '0.75rem 1rem' }}>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--orange2)', marginBottom: '0.3rem' }}>{key}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text2)' }}>{desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}