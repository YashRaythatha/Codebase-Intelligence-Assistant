'use client'

interface IngestFormProps {
  repoUrl: string
  localPath: string
  branch: string
  onRepoUrlChange: (v: string) => void
  onLocalPathChange: (v: string) => void
  onBranchChange: (v: string) => void
  onSubmit: (e: React.FormEvent) => void
  loading: boolean
  status: string
  error: string
}

export default function IngestForm({
  repoUrl,
  localPath,
  branch,
  onRepoUrlChange,
  onLocalPathChange,
  onBranchChange,
  onSubmit,
  loading,
  status,
  error,
}: IngestFormProps) {
  return (
    <div className="card">
      <h2>Ingest a repo</h2>
      <form onSubmit={onSubmit}>
        <label>Repo URL (GitHub)</label>
        <input
          value={repoUrl}
          onChange={(e) => onRepoUrlChange(e.target.value)}
          placeholder="https://github.com/user/repo"
          disabled={loading}
        />
        <label style={{ marginTop: '1rem' }}>Or local path</label>
        <input
          value={localPath}
          onChange={(e) => onLocalPathChange(e.target.value)}
          placeholder="C:\path\to\repo or /path/to/repo"
          disabled={loading}
        />
        <label style={{ marginTop: '1rem' }}>Branch (optional)</label>
        <input
          value={branch}
          onChange={(e) => onBranchChange(e.target.value)}
          placeholder="main"
          disabled={loading}
        />
        <button type="submit" disabled={loading || (!repoUrl.trim() && !localPath.trim())} className="ingest-submit" aria-busy={loading}>
          {loading ? <span className="ingest-loading"><span className="ask-spinner" aria-hidden /> Indexing…</span> : 'Ingest'}
        </button>
      </form>
      {status && <p className="ingest-status">{status}</p>}
      {error && <p className="ask-error" role="alert">{error}</p>}
    </div>
  )
}
