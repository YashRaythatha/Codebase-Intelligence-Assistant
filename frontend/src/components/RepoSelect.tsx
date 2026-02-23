'use client'

export interface RepoInfo {
  repo_id: string
  root_path: string
}

interface RepoSelectProps {
  repos: RepoInfo[]
  value: string
  onChange: (repoId: string) => void
  disabled?: boolean
}

export default function RepoSelect({ repos, value, onChange, disabled }: RepoSelectProps) {
  return (
    <div className="ask-repo-select">
      <label htmlFor="ask-repo-select">Repo</label>
      <select
        id="ask-repo-select"
        aria-label="Select repository"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="ask-input"
        style={{ maxWidth: '100%' }}
      >
        <option value="">Select repo</option>
        {repos.map((r) => (
          <option key={r.repo_id} value={r.repo_id}>
            {r.repo_id} {r.root_path ? `(${r.root_path})` : ''}
          </option>
        ))}
      </select>
    </div>
  )
}
