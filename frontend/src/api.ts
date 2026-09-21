import type { Airport, SearchParams, SearchResponse } from './types'

// Empty in development (Vite proxies /api); the deployed backend URL in production.
const BASE_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {}

async function request<T>(path: string, signal?: AbortSignal): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE_URL}${path}`, { signal })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError('Could not reach the server. Please try again in a moment.')
  }

  if (response.ok) return response.json() as Promise<T>

  if (response.status === 429) throw new ApiError('Too many searches - please wait a minute.')
  if (response.status === 400) {
    // DRF returns {field: ["message", ...]}
    const body = (await response.json().catch(() => ({}))) as Record<string, string[]>
    const message = Object.values(body).flat().join(' ')
    throw new ApiError(message || 'Invalid search.')
  }
  throw new ApiError('The flight service had a problem. Please try again.')
}

export function searchFlights(params: SearchParams, signal?: AbortSignal) {
  const query = new URLSearchParams({ ...params })
  return request<SearchResponse>(`/api/search/?${query}`, signal)
}

export function fetchAirports(signal?: AbortSignal) {
  return request<Airport[]>('/api/airports/', signal)
}
