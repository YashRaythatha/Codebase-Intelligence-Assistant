import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="container home-page" id="main">
      <nav className="ask-nav">
        <span className="ask-nav-brand">Codebase Intelligence</span>
        <div className="ask-nav-links">
          <Link href="/">Home</Link>
          <Link href="/ask">Ask</Link>
        </div>
      </nav>
      <div className="card not-found-card">
        <h1 className="not-found-title">Page not found</h1>
        <p className="not-found-text">The page you’re looking for doesn’t exist or has been moved.</p>
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap', marginTop: '1.5rem' }}>
          <Link href="/" className="ask-empty-repos-link">Go to Home</Link>
          <Link href="/ask" className="secondary-link">Go to Ask</Link>
        </div>
      </div>
    </div>
  )
}
