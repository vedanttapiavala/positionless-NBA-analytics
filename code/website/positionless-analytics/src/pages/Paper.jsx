//Generated with Claude in accordance with course AI policy
const PAPER_URL = import.meta.env.VITE_PAPER_URL || ''

export default function Paper() {
  return (
    <div className="page">
      <div className="page-title">Research <span className="accent">Paper</span></div>
      <div className="page-subtitle">
        Positionless Basketball and Injury Risk in the National Basketball Association
      </div>

      {PAPER_URL ? (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden', height: '80vh' }}>
          <iframe
            src={PAPER_URL}
            style={{ width: '100%', height: '100%', border: 'none' }}
            title="Research Paper"
          />
        </div>
      ) : (
        <div className="paper-iframe-wrap">
          <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
            <rect width="56" height="56" rx="10" fill="rgba(247,99,12,0.08)" stroke="rgba(247,99,12,0.2)" strokeWidth="1.5"/>
            <path d="M16 14h16l8 8v20H16V14z" stroke="#f7630c" strokeWidth="1.5" fill="none" strokeLinejoin="round"/>
            <path d="M32 14v8h8" stroke="#f7630c" strokeWidth="1.5" fill="none" strokeLinejoin="round"/>
            <path d="M20 26h16M20 31h16M20 36h10" stroke="#9090aa" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
          <div className="paper-placeholder">
            <h2>Paper Coming Soon</h2>
            <p style={{ color: 'var(--text2)', fontSize: '0.88rem', maxWidth: 420, margin: '0 auto', lineHeight: 1.7 }}>
              The full manuscript is under preparation.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}