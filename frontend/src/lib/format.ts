import type { Filters, Flight } from '../types'

const usd = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })

export const formatPrice = (amount: number) => usd.format(amount)

export function formatDuration(minutes: number) {
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  return `${h}h ${String(m).padStart(2, '0')}m`
}

export const formatStops = (stops: number) => (stops === 0 ? 'Direct' : `${stops} stop${stops > 1 ? 's' : ''}`)

// Times arrive as local wall-clock ISO strings ("2026-10-01T18:30-04:00"). Slice instead of
// using `new Date()`, which would shift them into the *browser's* time zone.
export const clockTime = (iso: string) => iso.slice(11, 16)

/** How many calendar days after departure the arrival happens (local dates), e.g. overnight flights -> 1. */
export function arrivalDayOffset(departure: string, arrival: string) {
  const day = (iso: string) => Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10))
  return Math.round((day(arrival) - day(departure)) / 86_400_000)
}

export function formatDate(isoDate: string) {
  const [y, m, d] = isoDate.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

/** YYYY-MM-DD in the user's local time, `daysFromNow` days ahead. */
export function localDate(daysFromNow = 0) {
  const d = new Date()
  d.setDate(d.getDate() + daysFromNow)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const BADGE_COLORS = [
  'bg-sky-600',
  'bg-emerald-600',
  'bg-violet-600',
  'bg-rose-600',
  'bg-amber-600',
  'bg-teal-600',
  'bg-indigo-600',
  'bg-fuchsia-600',
]

/** Stable colour per airline so the same airline always looks the same. */
export function airlineColor(name: string) {
  let hash = 0
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0
  return BADGE_COLORS[hash % BADGE_COLORS.length]
}

export function applyFilters(flights: Flight[], { sort, directOnly, airlines }: Filters): Flight[] {
  const filtered = flights.filter(
    (f) => (!directOnly || f.stops === 0) && (airlines.length === 0 || airlines.includes(f.airline)),
  )
  const compare: Record<Filters['sort'], (a: Flight, b: Flight) => number> = {
    recommended: (a, b) => b.score - a.score || a.price_usd - b.price_usd,
    price: (a, b) => a.price_usd - b.price_usd || a.duration_minutes - b.duration_minutes,
    duration: (a, b) => a.duration_minutes - b.duration_minutes || a.price_usd - b.price_usd,
  }
  return filtered.sort(compare[sort])
}
