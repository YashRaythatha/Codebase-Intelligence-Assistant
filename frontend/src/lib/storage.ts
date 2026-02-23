/**
 * Simple localStorage helpers for UI preferences.
 */

const SHOW_TRACES_KEY = 'codebase-intel-show-traces'

export function getShowTraces(): boolean {
  if (typeof window === 'undefined') return false
  try {
    const v = localStorage.getItem(SHOW_TRACES_KEY)
    return v === 'true'
  } catch {
    return false
  }
}

export function setShowTraces(value: boolean): void {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(SHOW_TRACES_KEY, value ? 'true' : 'false')
  } catch {
    // ignore
  }
}
