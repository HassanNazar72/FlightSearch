import { useState } from 'react'
import type { Flight } from '../types'
import FlightCard from './FlightCard'

const PAGE_SIZE = 20

interface Props {
  flights: Flight[]
  selectedId: string | null
  onSelect: (flight: Flight) => void
}

/** Renders the first page of results; "Show more" reveals the next. Remount (via `key`) to reset paging. */
export default function ResultsList({ flights, selectedId, onSelect }: Props) {
  const [shown, setShown] = useState(PAGE_SIZE)

  return (
    <div className="space-y-3">
      {flights.slice(0, shown).map((flight) => (
        <FlightCard key={flight.id} flight={flight} selected={flight.id === selectedId} onSelect={onSelect} />
      ))}
      {shown < flights.length && (
        <button
          onClick={() => setShown((n) => n + PAGE_SIZE)}
          className="w-full rounded-xl border border-slate-300 bg-white py-3 font-semibold text-slate-700 hover:bg-slate-100"
        >
          Show more ({flights.length - shown} remaining)
        </button>
      )}
    </div>
  )
}
