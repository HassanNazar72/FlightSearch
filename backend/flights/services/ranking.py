from flights.domain import Flight


def _normalise(value: float, low: float, high: float) -> float:
    """Min-max scale to 0..1 (0 = best/lowest). Everything equal -> 0."""
    return 0.0 if high == low else (value - low) / (high - low)


def rank_and_tag(flights: list[Flight], weights: dict[str, float]) -> list[Flight]:
    """Score every flight, tag the winners and return the list best-first.

    score (0-100) = 100 * (1 - (w_price * norm_price + w_duration * norm_duration))
    Price and duration are on different scales (dollars vs minutes), so each is
    min-max normalised across the result set before the weights are applied.
    Tags: 'cheapest', 'fastest', 'recommended' (highest score). One flight can carry several.
    """
    if not flights:
        return []

    prices = [f.price_usd for f in flights]
    durations = [f.duration_minutes for f in flights]
    p_lo, p_hi, d_lo, d_hi = min(prices), max(prices), min(durations), max(durations)

    for f in flights:
        penalty = weights["price"] * _normalise(f.price_usd, p_lo, p_hi) + weights[
            "duration"
        ] * _normalise(f.duration_minutes, d_lo, d_hi)
        f.score = round(100 * (1 - penalty), 1)
        f.tags = []

    # Ties are broken by the other criterion so the result is deterministic.
    min(flights, key=lambda f: (f.price_usd, f.duration_minutes)).tags.append("cheapest")
    min(flights, key=lambda f: (f.duration_minutes, f.price_usd)).tags.append("fastest")
    max(flights, key=lambda f: (f.score, -f.price_usd)).tags.append("recommended")

    return sorted(flights, key=lambda f: (-f.score, f.price_usd, f.id))
