from enum import Enum


class ListingType(str, Enum):
    demand: str = "demand"
    supply: str = "supply"


class EnergyType(str, Enum):
    solar: str = "solar"
    wind: str = "wind"
