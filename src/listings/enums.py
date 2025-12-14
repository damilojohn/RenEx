from enum import Enum


class ListingType(Enum, str):
    demand: str = "demand"
    supply: str = "supply"


class EnergyType(Enum, str):
    solar: str = "solar"
    wind: str = "wind"
