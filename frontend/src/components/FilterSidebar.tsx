import type { Filters, SortKey } from '../types'

const SORT_OPTIONS: { value: SortKey; label: string }[] = [
  { value: 'recommended', label: 'Recommended' },
  { value: 'price', label: 'Price (low to high)' },
  { value: 'duration', label: 'Duration (shortest)' },
]

interface Props {
  filters: Filters
  /** Every airline in the current results, with how many flights it has. */
  airlines: { name: string; count: number }[]
  onChange: (filters: Filters) => void
  onReset: () => void
}

export default function FilterSidebar({ filters, airlines, onChange, onReset }: Props) {
  const toggleAirline = (name: string) =>
    onChange({
      ...filters,
      airlines: filters.airlines.includes(name)
        ? filters.airlines.filter((a) => a !== name)
        : [...filters.airlines, name],
    })

  const isDefault = filters.sort === 'recommended' && !filters.directOnly && filters.airlines.length === 0

  return (
    <aside className="space-y-6 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="font-bold">Filters</h2>
        <button
          onClick={onReset}
          disabled={isDefault}
          className="text-sm font-medium text-sky-600 hover:underline disabled:cursor-default disabled:text-slate-300 disabled:no-underline"
        >
          Reset
        </button>
      </div>

      <fieldset>
        <legend className="mb-2 text-sm font-semibold text-slate-600">Sort by</legend>
        <div className="space-y-1.5">
          {SORT_OPTIONS.map((o) => (
            <label key={o.value} className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="radio"
                name="sort"
                className="accent-sky-600"
                checked={filters.sort === o.value}
                onChange={() => onChange({ ...filters, sort: o.value })}
              />
              {o.label}
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset>
        <legend className="mb-2 text-sm font-semibold text-slate-600">Stops</legend>
        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input
            type="checkbox"
            className="accent-sky-600"
            checked={filters.directOnly}
            onChange={(e) => onChange({ ...filters, directOnly: e.target.checked })}
          />
          Direct flights only
        </label>
      </fieldset>

      <fieldset>
        <legend className="mb-2 text-sm font-semibold text-slate-600">Airlines</legend>
        <div className="max-h-64 space-y-1.5 overflow-y-auto pr-1">
          {airlines.map(({ name, count }) => (
            <label key={name} className="flex cursor-pointer items-center gap-2 text-sm">
              <input
                type="checkbox"
                className="accent-sky-600"
                checked={filters.airlines.includes(name)}
                onChange={() => toggleAirline(name)}
              />
              <span className="flex-1">{name}</span>
              <span className="text-xs text-slate-400">{count}</span>
            </label>
          ))}
        </div>
      </fieldset>
    </aside>
  )
}
