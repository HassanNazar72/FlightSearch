import { arrivalDayOffset, clockTime, formatDuration, formatPrice, formatStops } from '../lib/format'
import type { Flight, Tag } from '../types'
import AirlineBadge from './AirlineBadge'

const TAG_STYLE: Record<Tag, string> = {
  cheapest: 'bg-emerald-100 text-emerald-800',
  recommended: 'bg-amber-100 text-amber-800',
  fastest: 'bg-sky-100 text-sky-800',
}
const TAG_LABEL: Record<Tag, string> = { cheapest: 'Cheapest', recommended: 'Recommended', fastest: 'Fastest' }

interface Props {
  flight: Flight
  selected: boolean
  onSelect: (flight: Flight) => void
}

export default function FlightCard({ flight, selected, onSelect }: Props) {
  const dayOffset = arrivalDayOffset(flight.departure_time, flight.arrival_time)

  return (
    <article
      className={`rounded-xl border bg-white p-4 shadow-sm transition sm:p-5 ${
        selected ? 'border-emerald-500 ring-1 ring-emerald-500' : 'border-slate-200 hover:shadow-md'
      }`}
    >
      {flight.tags.length > 0 && (
        <div className="mb-3 flex flex-wrap gap-1.5">
          {flight.tags.map((tag) => (
            <span key={tag} className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${TAG_STYLE[tag]}`}>
              {TAG_LABEL[tag]}
            </span>
          ))}
        </div>
      )}

      <div className="grid items-center gap-4 sm:grid-cols-[13rem_1fr_auto]">
        <div className="flex items-center gap-3">
          <AirlineBadge airline={flight.airline} flightNumber={flight.flight_number} />
          <div className="min-w-0">
            <div className="truncate font-semibold">{flight.airline}</div>
            <div className="text-sm text-slate-500">{flight.flight_number}</div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-center">
            <div className="text-xl font-bold">{clockTime(flight.departure_time)}</div>
            <div className="text-sm text-slate-500">{flight.origin}</div>
          </div>

          <div className="flex-1 px-1 text-center">
            <div className="text-xs font-medium text-slate-500">{formatDuration(flight.duration_minutes)}</div>
            <div className="relative my-1 h-px bg-slate-300">
              {flight.stops > 0 && (
                <span className="absolute left-1/2 top-1/2 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-amber-500 bg-white" />
              )}
            </div>
            <div className={`text-xs font-medium ${flight.stops === 0 ? 'text-emerald-600' : 'text-amber-600'}`}>
              {formatStops(flight.stops)}
            </div>
          </div>

          <div className="text-center">
            <div className="text-xl font-bold">
              {clockTime(flight.arrival_time)}
              {dayOffset > 0 && <sup className="ml-0.5 text-xs font-semibold text-rose-600">+{dayOffset}</sup>}
            </div>
            <div className="text-sm text-slate-500">{flight.destination}</div>
          </div>
        </div>

        <div className="flex items-center justify-between gap-4 sm:flex-col sm:items-end sm:gap-2">
          <div className="text-right">
            <div className="text-2xl font-bold">{formatPrice(flight.price_usd)}</div>
            <div className="text-xs text-slate-400" title="Provider that supplied this fare">
              via {flight.provider_id.replace('provider_', 'P-')}
            </div>
          </div>
          <button
            onClick={() => onSelect(flight)}
            aria-pressed={selected}
            className={`rounded-lg px-5 py-2 text-sm font-semibold transition focus:outline-none focus:ring-2 ${
              selected
                ? 'bg-emerald-600 text-white focus:ring-emerald-300'
                : 'bg-sky-600 text-white hover:bg-sky-700 focus:ring-sky-300'
            }`}
          >
            {selected ? 'Selected ✓' : 'Select'}
          </button>
        </div>
      </div>
    </article>
  )
}
