//Generated with Claude in accordance with course AI policy
export default function Paper() {
  const PAPER_URL = "/Evolution of Positionless Basketball and Associated Injury Risk in the NBA.pdf"

  return (
    <div className="page">
      <div className="page-title">Research <span className="accent">Paper</span></div>
      <div className="page-subtitle">
        Positionless Basketball and Injury Risk in the National Basketball Association
      </div>

      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden', height: '80vh' }}>
        <iframe
          src={PAPER_URL}
          style={{ width: '100%', height: '100%', border: 'none' }}
          title="Research Paper"
        />
      </div>
    </div>
  )
}