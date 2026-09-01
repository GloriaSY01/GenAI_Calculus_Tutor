import { useEffect, useState, useCallback } from 'react'
import { api } from '../api.js'

export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ loading: true, data: null, error: null })
  const run = useCallback(() => {
    let alive = true
    setState(s => ({ ...s, loading: true, error: null }))
    fn()
      .then(data => { if (alive) setState({ loading: false, data, error: null }) })
      .catch(error => { if (alive) setState({ loading: false, data: null, error }) })
    return () => { alive = false }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  useEffect(run, [run])
  return { ...state, reload: run }
}

export const useAnalytics = () => useAsync(() => api.getClassAnalytics(), [])
