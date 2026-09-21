/** Loading skeleton, empty state and error state. */

const pulse = 'animate-pulse rounded bg-slate-200'

export function ResultsSkeleton({ slow }: { slow: boolean }) {
  return (
    <div aria-busy="true" aria-live="polite">
      <p className="mb-4 text-sm font-medium text-slate-500">
        {slow
          ? 'The server was asleep (free hosting) and is waking up - this first search can take up to a minute…'
          : 'Searching 100 providers…'}
      </p>
      <div className="mb-6 grid gap-3 sm:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className={`${pulse} h-4 w-24`} />
            <div className={`${pulse} mt-3 h-7 w-20`} />
            <div className={`${pulse} mt-3 h-3 w-40`} />
          </div>
        ))}
      </div>
      <div className="space-y-3">
        {[0, 1, 2, 3, 4].map((i) => (
          <div key={i} className="flex items-center gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className={`${pulse} h-11 w-11 rounded-full`} />
            <div className="flex-1 space-y-2">
              <div className={`${pulse} h-5 w-1/3`} />
              <div className={`${pulse} h-3 w-2/3`} />
            </div>
            <div className={`${pulse} h-9 w-24`} />
          </div>
        ))}
      </div>
    </div>
  )
}

export function EmptyState({ onReset, hasFilters }: { onReset: () => void; hasFilters: boolean }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center">
      <div className="text-4xl" aria-hidden="true">
        🛫
      </div>
      <h3 className="mt-3 text-lg font-bold">No flights found</h3>
      <p className="mt-1 text-slate-500">
        {hasFilters ? 'No flights match your filters.' : 'Try a different date or route.'}
      </p>
      {hasFilters && (
        <button
          onClick={onReset}
          className="mt-4 rounded-lg bg-sky-600 px-5 py-2 font-semibold text-white hover:bg-sky-700"
        >
          Clear filters
        </button>
      )}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-6 py-10 text-center">
      <h3 className="text-lg font-bold text-rose-800">Search failed</h3>
      <p className="mt-1 text-rose-700">{message}</p>
      <button onClick={onRetry} className="mt-4 rounded-lg bg-rose-600 px-5 py-2 font-semibold text-white hover:bg-rose-700">
        Try again
      </button>
    </div>
  )
}
