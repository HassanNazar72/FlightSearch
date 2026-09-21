import { formatDuration, formatPrice, formatStops } from '../lib/format'
import type { Flight, SortKey } from '../types'

interface Props {
  cheapest: Flight
  recommended: Flight
  fastest: Flight
  activeSort: SortKey
  onSelectSort: (sort: SortKey) => void
}

/** Top cards that double as tabs: clicking one re-sorts the list by that criterion. */
export default function HighlightBadges({ cheapest, recommended, fastest, activeSort, onSelectSort }: Props) {
  const cards: { sort: SortKey; icon: string; label: string; flight: Flight }[] = [
    { sort: 'price', icon: '🏷️', label: 'Cheapest', flight: cheapest },
    { sort: 'recommended', icon: '⭐', label: 'Recommended', flight: recommended },
    { sort: 'duration', icon: '⚡', label: 'Fastest', flight: fastest },
  ]

  return (
    <div role="tablist" aria-label="Highlights" className="grid gap-3 sm:grid-cols-3">
      {cards.map(({ sort, icon, label, flight }) => {
        const active = activeSort === sort
        return (
          <button
            key={label}
            role="tab"
            aria-selected={active}
            onClick={() => onSelectSort(sort)}
            className={`rounded-xl border p-4 text-left transition focus:outline-none focus:ring-2 focus:ring-sky-300 ${
              active
                ? 'border-sky-500 bg-sky-50 shadow-md'
                : 'border-slate-200 bg-white shadow-sm hover:border-sky-300 hover:shadow'
            }`}
          >
            <div className="text-sm font-semibold text-slate-600">
              <span aria-hidden="true">{icon}</span> {label}
            </div>
            <div className="mt-1 text-2xl font-bold text-slate-900">{formatPrice(flight.price_usd)}</div>
            <div className="mt-0.5 truncate text-sm text-slate-600">
              {flight.airline} · {formatDuration(flight.duration_minutes)} · {formatStops(flight.stops)}
            </div>
          </button>
        )
      })}
    </div>
  )
}
