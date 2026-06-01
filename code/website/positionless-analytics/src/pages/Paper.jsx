const PAPER_URL = import.meta.env.VITE_PAPER_URL || ''

export default function Paper() {
  return (
    <div className="page">
      <div className="page-title">Research <span className="accent">Paper</span></div>
      <div className="page-subtitle">
        Full manuscript: Positionless Basketball and Injury Risk in the NBA
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
              The full manuscript is under preparation. Set the{' '}
              <code style={{ fontFamily: 'var(--font-mono)', fontSize: '0.82rem', background: 'var(--bg3)', padding: '0.1rem 0.3rem', borderRadius: 3 }}>VITE_PAPER_URL</code>{' '}
              environment variable to embed a PDF URL here.
            </p>
          </div>
        </div>
      )}

      {/* Citation block */}
      <div style={{ marginTop: '2rem' }}>
        <div className="section-label">Citation</div>
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6, padding: '1.2rem 1.4rem', marginTop: '0.6rem' }}>
          <div style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text2)', lineHeight: 1.8, userSelect: 'all' }}>
            [Author(s)]. (2024). <em style={{ color: 'var(--text)' }}>Positionless Basketball and Injury Risk in the NBA: An Empirical Analysis.</em> Manuscript in preparation.
          </div>
        </div>
      </div>

      {/* Abstract placeholder */}
      <div style={{ marginTop: '2rem' }}>
        <div className="section-label">Abstract</div>
        <div className="callout" style={{ marginTop: '0.6rem' }}>
          <p>
            We introduce a continuous Positionless Index to quantify role fluidity across NBA player-seasons (2014–2024) and model its relationship to injury risk. Using a CatBoost gradient-boosted classifier trained on 7-game rolling load windows and team context, we find that a one standard deviation increase in the positionless index is associated with an odds ratio of 1.081 (95% CI: 1.012–1.154) for injury in the subsequent game. A structural breakpoint test identifies the 2018–19 season as the inflection point for league-wide positional convergence.
          </p>
        </div>
      </div>
    </div>
  )
}