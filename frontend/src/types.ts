// Mirrors the canonical flight schema returned by the Django API.

export type Tag = 'cheapest' | 'fastest' | 'recommended'

export interface Flight {
  id: string
  provider_id: string
  airline: string
  flight_number: string
  origin: string
  destination: string
  /** ISO-8601 in the airport's local time, e.g. 2026-10-01T18:30-04:00 */
  departure_time: string
  arrival_time: string
  duration_minutes: number
  stops: number
  price_usd: number
  /** Always "USD" in this prototype. */
  currency: string
  /** 0-100 weighted price/duration score, higher is better. */
  score: number
  tags: Tag[]
}

export interface SearchMeta {
  total_flights: number
  providers_total: number
  providers_ok: number
  providers_failed: number
  failures: { provider_id: string; reason: string }[]
  cached: boolean
  took_ms: number
}

export interface SearchParams {
  origin: string
  destination: string
  date: string
}

export interface SearchResponse {
  query: SearchParams
  meta: SearchMeta
  flights: Flight[]
}

export interface Airport {
  code: string
  city: string
}

export type SortKey = 'recommended' | 'price' | 'duration'

export interface Filters {
  sort: SortKey
  directOnly: boolean
  /** Selected airline names; empty means "all airlines". */
  airlines: string[]
}
