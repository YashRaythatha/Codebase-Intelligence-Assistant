'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { getRepos, ingestRepoFull, getApiErrorMessage } from '@/lib/api'
import RepoSelect from '@/components/RepoSelect'
import IngestForm from '@/components/IngestForm'

export default function Home() {
  const [repoUrl, setRepoUrl] = useState('')
  const [localPath, setLocalPath] = useState('')
  const [branch, setBranch] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [repos, setRepos] = useState<{ repo_id: string; root_path: string }[]>([])
  const [reposLoading, setReposLoading] = useState(true)
  const [reposError, setReposError] = useState('')
  const [status, setStatus] = useState('')

  async function loadRepos() {
    setReposError('')
    setReposLoading(true)
    try {
      const data = await getRepos()
      setRepos(data.repos || [])
    } catch {
      setRepos([])
      setReposError('Could not load repos. Is the backend running at ' + (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000') + '?')
    } finally {
      setReposLoading(false)
    }
  }

  useEffect(() => {
    loadRepos()
  }, [])

  async function handleIngest(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setStatus('')
    const source = repoUrl.trim() || localPath.trim()
    if (!source) return
    setLoading(true)
    try {
      const result = await ingestRepoFull({
        repo_url: repoUrl.trim() || undefined,
        local_path: localPath.trim() || undefined,
        branch: branch.trim() || undefined,
      })
      setStatus(`Indexed repo_id: ${result.repo_id}${result.detected ? ' · Framework: ' + JSON.stringify((result.detected as { frameworks?: string[] })?.frameworks || []) : ''}`)
      setRepoUrl('')
      setLocalPath('')
      setBranch('')
      loadRepos()
    } catch (err) {
      setError(getApiErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container home-page" id="main">
      <nav className="ask-nav">
        <span className="ask-nav-brand">Codebase Intelligence</span>
        <div className="ask-nav-links">
          <Link href="/" className="active">Home</Link>
          <Link href="/ask">Ask</Link>
        </div>
      </nav>
      <h1>Codebase Intelligence Assistant</h1>
      <IngestForm
        repoUrl={repoUrl}
        localPath={localPath}
        branch={branch}
        onRepoUrlChange={setRepoUrl}
        onLocalPathChange={setLocalPath}
        onBranchChange={setBranch}
        onSubmit={handleIngest}
        loading={loading}
        status={status}
        error={error}
      />
      <div className="card">
        <h2>Indexed repos</h2>
        {reposLoading ? (
          <p className="repos-loading">Loading repos…</p>
        ) : reposError ? (
          <p className="ask-error">{reposError}</p>
        ) : repos.length === 0 ? (
          <p>No repos yet. Ingest a repo above.</p>
        ) : (
          <ul>
            {repos.map((r) => (
              <li key={r.repo_id}>
                <strong>{r.repo_id}</strong> {r.root_path && `(${r.root_path})`}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
