import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, searchFlights } from '../api'
import type { SearchParams, SearchResponse } from '../types'

type State =
  | { status: 'idle' }
  | { status: 'loading'; slow: boolean }
  | { status: 'success'; data: SearchResponse }
  | { status: 'error'; message: string }

// Render's free tier sleeps when idle; after this long we tell the user why it's slow.
const SLOW_AFTER_MS = 4000

export function useFlightSearch() {
  const [state, setState] = useState<State>({ status: 'idle' })
  const controller = useRef<AbortController | null>(null)
  const slowTimer = useRef<number | undefined>(undefined)

  const search = useCallback(async (params: SearchParams) => {
    controller.current?.abort() // a newer search supersedes the one in flight
    window.clearTimeout(slowTimer.current)
    const current = new AbortController()
    controller.current = current

    setState({ status: 'loading', slow: false })
    slowTimer.current = window.setTimeout(() => {
      setState((s) => (s.status === 'loading' ? { status: 'loading', slow: true } : s))
    }, SLOW_AFTER_MS)

    try {
      const data = await searchFlights(params, current.signal)
      setState({ status: 'success', data })
    } catch (err) {
      if (current.signal.aborted) return
      setState({ status: 'error', message: err instanceof ApiError ? err.message : 'Something went wrong.' })
    } finally {
      // A superseded request must not cancel the newer request's timer.
      if (controller.current === current) window.clearTimeout(slowTimer.current)
    }
  }, [])

  useEffect(() => () => controller.current?.abort(), [])

  return { state, search }
}
