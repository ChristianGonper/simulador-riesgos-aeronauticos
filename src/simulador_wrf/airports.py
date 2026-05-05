"""
Catálogo de aeropuertos y utilidades de resolución.
"""

from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class Airport:
    icao: str
    iata: str
    name: str
    country: str
    latitude: float
    longitude: float

# Catálogo inicial de aeropuertos principales
_AIRPORTS_CATALOG: Dict[str, Airport] = {
    "LEMD": Airport("LEMD", "MAD", "Adolfo Suárez Madrid-Barajas", "Spain", 40.4722, -3.5608),
    "LEBL": Airport("LEBL", "BCN", "Josep Tarradellas Barcelona-El Prat", "Spain", 41.2971, 2.0785),
    "EGLL": Airport("EGLL", "LHR", "London Heathrow", "United Kingdom", 51.4700, -0.4543),
    "LFPG": Airport("LFPG", "CDG", "Charles de Gaulle", "France", 49.0097, 2.5478),
    "EDDF": Airport("EDDF", "FRA", "Frankfurt am Main", "Germany", 50.0333, 8.5705),
    "EHAM": Airport("EHAM", "AMS", "Amsterdam Schiphol", "Netherlands", 52.3081, 4.7642),
    "KJFK": Airport("KJFK", "JFK", "John F. Kennedy International", "USA", 40.6413, -73.7781),
    "KLAX": Airport("KLAX", "LAX", "Los Angeles International", "USA", 33.9416, -118.4085),
    "LEPA": Airport("LEPA", "PMI", "Palma de Mallorca", "Spain", 39.5517, 2.7388),
    "LEMG": Airport("LEMG", "AGP", "Málaga-Costa del Sol", "Spain", 36.6749, -4.4991),
    "LEVC": Airport("LEVC", "VLC", "Valencia", "Spain", 39.4893, -0.4816),
    "LEZL": Airport("LEZL", "SVQ", "Sevilla", "Spain", 37.4180, -5.8931),
    "LPPT": Airport("LPPT", "LIS", "Lisbon Humberto Delgado", "Portugal", 38.7742, -9.1342),
}

def resolve_airport(code: str) -> Optional[Airport]:
    """
    Resuelve un aeropuerto por su código ICAO o IATA.
    """
    code = code.upper()
    
    # Búsqueda directa por ICAO
    if code in _AIRPORTS_CATALOG:
        return _AIRPORTS_CATALOG[code]
    
    # Búsqueda por IATA
    for airport in _AIRPORTS_CATALOG.values():
        if airport.iata == code:
            return airport
            
    return None

def get_all_airports() -> Dict[str, Airport]:
    """
    Devuelve el catálogo completo de aeropuertos.
    """
    return _AIRPORTS_CATALOG.copy()
