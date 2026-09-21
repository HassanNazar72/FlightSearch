import { useState, type FormEvent } from 'react'
import { localDate } from '../lib/format'
import type { Airport, SearchParams } from '../types'

interface Props {
  initial: SearchParams
  airports: Airport[]
  loading: boolean
  onSearch: (params: SearchParams) => void
}

const inputClass =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-slate-900 shadow-sm focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-200'

export default function SearchForm({ initial, airports, loading, onSearch }: Props) {
  const [origin, setOrigin] = useState(initial.origin)
  const [destination, setDestination] = useState(initial.destination)
  const [date, setDate] = useState(initial.date)
  const [error, setError] = useState<string | null>(null)

  const codes = new Set(airports.map((a) => a.code))

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    // Airports load asynchronously; only validate against them once we have the list.
    if (codes.size && (!codes.has(origin) || !codes.has(destination))) {
      setError('Pick airports from the suggestions (3-letter codes, e.g. JFK, LHR).')
    } else if (origin === destination) {
      setError('Origin and destination must be different.')
    } else if (!date) {
      setError('Choose a departure date.')
    } else {
      setError(null)
      onSearch({ origin, destination, date })
    }
  }

  const swap = () => {
    setOrigin(destination)
    setDestination(origin)
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="rounded-2xl bg-white p-4 shadow-lg sm:p-5">
      <div className="grid gap-3 md:grid-cols-[1fr_auto_1fr_11rem_auto] md:items-end">
        <label className="block">
          <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">From</span>
          <input
            className={`${inputClass} uppercase`}
            value={origin}
            onChange={(e) => setOrigin(e.target.value.toUpperCase().slice(0, 3))}
            list="airport-options"
            placeholder="JFK"
            autoComplete="off"
            required
          />
        </label>

        <button
          type="button"
          onClick={swap}
          aria-label="Swap origin and destination"
          className="hidden h-10 w-10 items-center justify-center rounded-full border border-slate-300 text-slate-600 hover:bg-slate-100 md:flex"
        >
          ⇄
        </button>

        <label className="block">
          <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">To</span>
          <input
            className={`${inputClass} uppercase`}
            value={destination}
            onChange={(e) => setDestination(e.target.value.toUpperCase().slice(0, 3))}
            list="airport-options"
            placeholder="LHR"
            autoComplete="off"
            required
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-semibold uppercase tracking-wide text-slate-500">Departure</span>
          <input
            type="date"
            className={inputClass}
            value={date}
            min={localDate()}
            onChange={(e) => setDate(e.target.value)}
            required
          />
        </label>

        <button
          type="submit"
          disabled={loading}
          className="rounded-lg bg-sky-600 px-6 py-2.5 font-semibold text-white shadow-sm transition hover:bg-sky-700 focus:outline-none focus:ring-2 focus:ring-sky-300 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Searching…' : 'Search Flights'}
        </button>
      </div>

      <datalist id="airport-options">
        {airports.map((a) => (
          <option key={a.code} value={a.code}>
            {a.city}
          </option>
        ))}
      </datalist>

      {error && (
        <p role="alert" className="mt-3 text-sm font-medium text-rose-600">
          {error}
        </p>
      )}
    </form>
  )
}
