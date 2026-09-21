from flights.adapters import schemas  # noqa: F401  (importing registers every adapter)
from flights.adapters.registry import get_adapter, registered_schemas

__all__ = ["get_adapter", "registered_schemas"]
