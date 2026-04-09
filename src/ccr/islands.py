"""Caribbean island metadata and configuration registry."""

from __future__ import annotations
from dataclasses import dataclass

@dataclass
class IslandConfig:
    """Configuration for a Caribbean island."""
    name: str
    area_km2: float
    coastal_population: int
    bbox: tuple[float, float, float, float]
    tide_gauge: str
    mean_elevation_m: float
    hurricane_basin: str = "atlantic"

ISLAND_REGISTRY: dict[str, IslandConfig] = {
    "Jamaica": IslandConfig("Jamaica", 10991, 1_200_000, (-78.4, 17.7, -76.2, 18.6), "Kingston", 340),
    "Trinidad": IslandConfig("Trinidad", 5131, 800_000, (-61.9, 10.0, -60.5, 10.8), "Port of Spain", 83),
    "Barbados": IslandConfig("Barbados", 431, 200_000, (-59.7, 13.0, -59.4, 13.3), "Bridgetown", 166),
    "Bahamas": IslandConfig("Bahamas", 13943, 300_000, (-79.0, 21.0, -72.7, 27.3), "Nassau", 7),
    "Haiti": IslandConfig("Haiti", 27750, 3_100_000, (-74.5, 18.0, -71.6, 20.1), "Port-au-Prince", 470),
    "Cuba": IslandConfig("Cuba", 109884, 4_200_000, (-85.0, 19.8, -74.1, 23.3), "Havana", 108),
    "Dominican Republic": IslandConfig("Dominican Republic", 48671, 3_800_000, (-72.0, 17.5, -68.3, 19.9), "Santo Domingo", 424),
    "Puerto Rico": IslandConfig("Puerto Rico", 9104, 1_900_000, (-67.3, 17.9, -65.6, 18.5), "San Juan", 261),
    "Guadeloupe": IslandConfig("Guadeloupe", 1628, 300_000, (-61.8, 15.8, -61.0, 16.5), "Pointe-a-Pitre", 484),
    "Martinique": IslandConfig("Martinique", 1128, 200_000, (-61.2, 14.4, -60.8, 14.9), "Fort-de-France", 217),
    "St. Lucia": IslandConfig("St. Lucia", 617, 100_000, (-61.1, 13.7, -60.9, 14.1), "Castries", 333),
    "Grenada": IslandConfig("Grenada", 344, 60_000, (-61.8, 11.9, -61.6, 12.2), "St. George's", 172),
    "Dominica": IslandConfig("Dominica", 751, 40_000, (-61.5, 15.2, -61.2, 15.6), "Roseau", 442),
}

def get_island(name: str) -> IslandConfig:
    """Get island configuration by name."""
    key = next((k for k in ISLAND_REGISTRY if k.lower() == name.lower()), None)
    if key is None:
        raise ValueError(f"Island '{name}' not found. Available: {list(ISLAND_REGISTRY.keys())}")
    return ISLAND_REGISTRY[key]
