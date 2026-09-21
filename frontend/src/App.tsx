import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { fetchAirports } from './api'
import FilterSidebar from './components/FilterSidebar'
import HighlightBadges from './components/HighlightBadges'
import ResultsList from './components/ResultsList'
import SearchForm from './components/SearchForm'
import { EmptyState, ErrorState, ResultsSkeleton } from './components/States'
import { useFlightSearch } from './hooks/useFlightSearch'
import { applyFilters, formatDate, formatPrice, localDate } from './lib/format'
import type { Airport, Filters, Flight, SearchParams } from './types'

const DEFAULT_SEARCH: SearchParams = { origin: 'JFK', destination: 'LHR', date: localDate(14) }
const DEFAULT_FILTERS: Filters = { sort: 'recommended', directOnly: false, airlines: [] }

export default function App() {
  const { state, search } = useFlightSearch()
  const [airports, setAirports] = useState<Airport[]>([])
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS)
  const [selected, setSelected] = useState<Flight | null>(null)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const lastSearch = useRef(DEFAULT_SEARCH)

  const runSearch = useCallback(
    (params: SearchParams) => {
      lastSearch.current = params
      setFilters((f) => ({ ...f, airlines: [] })) // a new result set has a different airline list
      setSelected(null)
      void search(params)
    },
    [search],
  )

  // Load airports for the autocomplete and run the default search on first render.
  useEffect(() => {
    const controller = new AbortController()
    fetchAirports(controller.signal).then(setAirports, () => {})
    void search(DEFAULT_SEARCH)
    return () => controller.abort()
  }, [search])

  const flights = state.status === 'success' ? state.data.flights : null

  const visible = useMemo(() => (flights ? applyFilters(flights, filters) : []), [flights, filters])

  const airlines = useMemo(() => {
    const counts = new Map<string, number>()
    for (const f of flights ?? []) counts.set(f.airline, (counts.get(f.airline) ?? 0) + 1)
    return [...counts].map(([name, count]) => ({ name, count })).sort((a, b) => a.name.localeCompare(b.name))
  }, [flights])

  // Highlights follow the filters: "cheapest" means cheapest among what you can currently see.
  const highlights = useMemo(() => {
    if (visible.length === 0) return null
    const best = (beats: (candidate: Flight, current: Flight) => boolean) =>
      visible.reduce((current, candidate) => (beats(candidate, current) ? candidate : current))
    return {
      cheapest: best((c, cur) => c.price_usd < cur.price_usd),
      fastest: best((c, cur) => c.duration_minutes < cur.duration_minutes),
      recommended: best((c, cur) => c.score > cur.score),
    }
  }, [visible])

  const hasActiveFilters = filters.directOnly || filters.airlines.length > 0
  const resetFilters = () => setFilters(DEFAULT_FILTERS)

  return (
    <div className="min-h-screen pb-24">
      <header className="bg-gradient-to-br from-sky-700 to-sky-500 px-4 pb-10 pt-8 text-white">
        <div className="mx-auto max-w-6xl">
          <h1 className="text-2xl font-extrabold tracking-tight sm:text-3xl">✈ SkyCompare</h1>
          <p className="mb-5 mt-1 text-sky-100">One search, 100 flight providers.</p>
          <SearchForm
            initial={DEFAULT_SEARCH}
            airports={airports}
            loading={state.status === 'loading'}
            onSearch={runSearch}
          />
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        {state.status === 'loading' && <ResultsSkeleton slow={state.slow} />}

        {state.status === 'error' && (
          <ErrorState message={state.message} onRetry={() => runSearch(lastSearch.current)} />
        )}

        {state.status === 'success' && (
          <>
            <div className="mb-4 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
              <h2 className="text-lg font-bold">
                {state.data.query.origin} → {state.data.query.destination}
                <span className="ml-2 font-medium text-slate-500">{formatDate(state.data.query.date)}</span>
              </h2>
              <p className="text-sm text-slate-500" aria-live="polite">
                {visible.length} of {state.data.meta.total_flights} flights · results from{' '}
                <span title={state.data.meta.failures.map((f) => `${f.provider_id}: ${f.reason}`).join('\n')}>
                  {state.data.meta.providers_ok}/{state.data.meta.providers_total} providers
                </span>{' '}
                · {state.data.meta.cached ? 'cached' : `${(state.data.meta.took_ms / 1000).toFixed(1)}s`}
              </p>
            </div>

            {highlights && (
              <div className="mb-6">
                <HighlightBadges {...highlights} activeSort={filters.sort} onSelectSort={(sort) => setFilters({ ...filters, sort })} />
              </div>
            )}

            <button
              className="mb-3 w-full rounded-lg border border-slate-300 bg-white py-2 font-semibold lg:hidden"
              onClick={() => setFiltersOpen((o) => !o)}
              aria-expanded={filtersOpen}
            >
              {filtersOpen ? 'Hide filters' : 'Show filters'}
            </button>

            <div className="grid gap-6 lg:grid-cols-[16rem_1fr]">
              <div className={`${filtersOpen ? 'block' : 'hidden'} lg:block`}>
                <FilterSidebar filters={filters} airlines={airlines} onChange={setFilters} onReset={resetFilters} />
              </div>

              {visible.length > 0 ? (
                <ResultsList
                  key={`${filters.sort}|${filters.directOnly}|${filters.airlines.join()}|${state.data.query.date}${state.data.query.origin}${state.data.query.destination}`}
                  flights={visible}
                  selectedId={selected?.id ?? null}
                  onSelect={(f) => setSelected((s) => (s?.id === f.id ? null : f))}
                />
              ) : (
                <EmptyState hasFilters={hasActiveFilters} onReset={resetFilters} />
              )}
            </div>
          </>
        )}
      </main>

      {selected && (
        <div className="fixed inset-x-0 bottom-0 border-t border-slate-200 bg-white/95 px-4 py-3 shadow-[0_-4px_12px_rgba(0,0,0,0.08)] backdrop-blur">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-2">
            <p className="text-sm">
              <strong>
                {selected.airline} {selected.flight_number}
              </strong>{' '}
              · {selected.origin} → {selected.destination} · {formatPrice(selected.price_usd)}
              <span className="ml-2 text-slate-500">(Booking is out of scope for this demo.)</span>
            </p>
            <button onClick={() => setSelected(null)} className="text-sm font-semibold text-sky-600 hover:underline">
              Clear selection
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
