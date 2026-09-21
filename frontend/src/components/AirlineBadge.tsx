import { airlineColor } from '../lib/format'

/** Airline "logo": coloured circle with the IATA code. Avoids hot-linking third-party logo images. */
export default function AirlineBadge({ airline, flightNumber }: { airline: string; flightNumber: string }) {
  return (
    <div
      aria-hidden="true"
      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-sm font-bold text-white ${airlineColor(airline)}`}
    >
      {flightNumber.slice(0, 2)}
    </div>
  )
}
