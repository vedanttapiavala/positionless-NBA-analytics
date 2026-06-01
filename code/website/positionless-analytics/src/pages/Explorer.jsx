import { useState, useMemo, useCallback } from 'react'
import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid
} from 'recharts'

const ORANGE  = '#f7630c'
const ORANGE2 = '#ff8c42'
const TEXT2   = '#9090aa'
const PAGE_SIZE = 20

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div style={{ background: '#12121a', border: '1px solid #2a2a3e', borderRadius: 6, padding: '8px 12px', fontSize: 12, fontFamily: 'JetBrains Mono, monospace' }}>
      <div style={{ color: '#9090aa', marginBottom: 4 }}>Season {label}</div>
      {payload.map(p => (
        <div key={p.name} style={{ color: ORANGE }}>
          Index: <strong>{typeof p.value === 'number' ? p.value.toFixed(4) : p.value}</strong>
        </div>
      ))}
    </div>
  )
}

function PlayerModal({ player, data, onClose }) {
  // Find all seasons for this player from playersIndex
  const rows = useMemo(() =>
    (data?.playersIndexTable || [])
      .filter(r => r.player === player)
      .sort((a, b) => a.season - b.season),
    [data, player]
  )

  // Also check trajectories
  const traj = useMemo(() => {
    const t = (data?.playerTrajectories || []).find(t => t.player === player)
    if (t) return t.trajectory
    // Build from playersIndex rows
    return rows.map(r => ({ season: r.season, positionless_index: r.positionless_index }))
  }, [data, player, rows])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>{player}</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="chart-card" style={{ marginBottom: '1.2rem' }}>
          <div className="chart-title">Positionless Index Over Time</div>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={traj} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3e" />
              <XAxis dataKey="season" tick={{ fill: TEXT2, fontSize: 11, fontFamily: 'JetBrains Mono' }} />
              <YAxis tick={{ fill: TEXT2, fontSize: 11, fontFamily: 'JetBrains Mono' }} domain={['auto', 'auto']} />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="positionless_index"
                stroke={ORANGE}
                strokeWidth={2.5}
                dot={{ fill: ORANGE, r: 3 }}
                activeDot={{ r: 5, fill: ORANGE2 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#1a1a26' }}>
              {['Season','Team','Index','Games'].map(h => (
                <th key={h} style={{ padding: '8px 12px', fontSize: '0.72rem', fontFamily: 'Barlow Condensed, sans-serif', fontWeight: 700, letterSpacing: '0.1em', textTransform: 'uppercase', color: '#5a5a72', textAlign: 'left', borderBottom: '1px solid #2a2a3e' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td style={{ padding: '7px 12px', fontSize: '0.85rem', borderBottom: '1px solid rgba(42,42,62,0.4)', fontFamily: 'JetBrains Mono, monospace', color: '#9090aa' }}>{r.season}</td>
                <td style={{ padding: '7px 12px', fontSize: '0.85rem', borderBottom: '1px solid rgba(42,42,62,0.4)' }}><span className="badge">{r.team}</span></td>
                <td style={{ padding: '7px 12px', fontSize: '0.85rem', borderBottom: '1px solid rgba(42,42,62,0.4)', fontFamily: 'JetBrains Mono, monospace', color: ORANGE2, fontWeight: 600 }}>{Number(r.positionless_index).toFixed(4)}</td>
                <td style={{ padding: '7px 12px', fontSize: '0.85rem', borderBottom: '1px solid rgba(42,42,62,0.4)', color: '#9090aa', fontFamily: 'JetBrains Mono, monospace' }}>{r.games_played ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default function Explorer({ data }) {
  const [search,      setSearch]      = useState('')
  const [teamFilter,  setTeamFilter]  = useState('')
  const [seasonFilter,setSeasonFilter]= useState('')
  const [sortKey,     setSortKey]     = useState('positionless_index')
  const [sortDir,     setSortDir]     = useState('desc')
  const [page,        setPage]        = useState(1)
  const [selected,    setSelected]    = useState(null)

  const rows = data?.playersIndexTable || []

  const teams   = useMemo(() => [...new Set(rows.map(r => r.team))].sort(), [rows])
  const seasons = useMemo(() => [...new Set(rows.map(r => r.season))].sort((a,b) => b - a), [rows])

  const filtered = useMemo(() => {
    let r = rows
    if (search)       r = r.filter(x => x.player?.toLowerCase().includes(search.toLowerCase()))
    if (teamFilter)   r = r.filter(x => x.team === teamFilter)
    if (seasonFilter) r = r.filter(x => String(x.season) === seasonFilter)
    r = [...r].sort((a, b) => {
      const va = a[sortKey], vb = b[sortKey]
      if (typeof va === 'number') return sortDir === 'asc' ? va - vb : vb - va
      return sortDir === 'asc'
        ? String(va).localeCompare(String(vb))
        : String(vb).localeCompare(String(va))
    })
    return r
  }, [rows, search, teamFilter, seasonFilter, sortKey, sortDir])

  const pages     = Math.ceil(filtered.length / PAGE_SIZE)
  const pageRows  = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)

  const handleSort = useCallback(key => {
    if (key === sortKey) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortKey(key); setSortDir('desc') }
    setPage(1)
  }, [sortKey])

  const cols = [
    { key: 'player',             label: 'Player' },
    { key: 'team',               label: 'Team' },
    { key: 'season',             label: 'Season' },
    { key: 'positionless_index', label: 'P. Index' },
    { key: 'games_played',       label: 'GP' },
  ]

  return (
    <div className="page">
      <div className="page-title">Positionless Index <span className="accent">Explorer</span></div>
      <div className="page-subtitle">
        Browse all player–season positionless index scores. Click any row to view the player's trajectory.
      </div>

      <div className="table-wrap">
        <div className="table-controls">
          <input
            className="search-input"
            placeholder="Search player…"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
          />
          <select
            className="filter-select"
            value={teamFilter}
            onChange={e => { setTeamFilter(e.target.value); setPage(1) }}
          >
            <option value="">All Teams</option>
            {teams.map(t => <option key={t} value={t}>{t}</option>)}
          </select>
          <select
            className="filter-select"
            value={seasonFilter}
            onChange={e => { setSeasonFilter(e.target.value); setPage(1) }}
          >
            <option value="">All Seasons</option>
            {seasons.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table>
            <thead>
              <tr>
                {cols.map(c => (
                  <th key={c.key} onClick={() => handleSort(c.key)}>
                    {c.label}
                    <span className="sort-arrow">
                      {sortKey === c.key ? (sortDir === 'asc' ? ' ↑' : ' ↓') : ' ↕'}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageRows.length === 0 ? (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--text3)', padding: '2rem' }}>No results</td></tr>
              ) : pageRows.map((r, i) => (
                <tr key={i} onClick={() => setSelected(r.player)}>
                  <td style={{ fontWeight: 500, color: 'var(--white)' }}>{r.player}</td>
                  <td><span className="badge">{r.team}</span></td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: TEXT2 }}>{r.season}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.88rem', color: ORANGE2, fontWeight: 600 }}>
                    {Number(r.positionless_index).toFixed(4)}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', color: TEXT2 }}>{r.games_played ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="table-footer">
          {filtered.length.toLocaleString()} records
        </div>

        {pages > 1 && (
          <div className="pagination">
            <button className="page-btn" disabled={page === 1} onClick={() => setPage(p => p - 1)}>‹</button>
            {Array.from({ length: Math.min(pages, 7) }, (_, i) => {
              const p = page <= 4 ? i + 1 : page - 3 + i
              if (p < 1 || p > pages) return null
              return (
                <button key={p} className={`page-btn ${p === page ? 'active' : ''}`} onClick={() => setPage(p)}>{p}</button>
              )
            })}
            <button className="page-btn" disabled={page === pages} onClick={() => setPage(p => p + 1)}>›</button>
          </div>
        )}
      </div>

      {selected && (
        <PlayerModal
          player={selected}
          data={data}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  )
}