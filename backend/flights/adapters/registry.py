from flights.adapters.base import BaseAdapter

_ADAPTERS: dict[str, BaseAdapter] = {}


def register(schema: str):
    """Class decorator: `@register("fare_iso")` makes the adapter discoverable by name."""

    def wrap(cls: type[BaseAdapter]) -> type[BaseAdapter]:
        _ADAPTERS[schema] = cls()
        return cls

    return wrap


def get_adapter(schema: str) -> BaseAdapter:
    try:
        return _ADAPTERS[schema]
    except KeyError:
        raise LookupError(f"No adapter registered for schema '{schema}'") from None


def registered_schemas() -> list[str]:
    return list(_ADAPTERS)
