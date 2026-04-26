"""Shared Sousse governorate geography used by the seeders."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt

SOUSSE_ZONES = [
    {
        "name": "Medina de Sousse",
        "description": "Coeur historique et commercial de la ville de Sousse",
        "center_lat": 35.8254,
        "center_lon": 10.6370,
        "surface_km2": 4.1,
        "coastal": True,
        "profile": "historic",
    },
    {
        "name": "La Corniche",
        "description": "Front de mer urbain au nord du centre de Sousse",
        "center_lat": 35.8425,
        "center_lon": 10.6292,
        "surface_km2": 3.6,
        "coastal": True,
        "profile": "coastal",
    },
    {
        "name": "Hammam Sousse",
        "description": "Commune littorale residentielle reliee a l'agglomeration de Sousse",
        "center_lat": 35.8609,
        "center_lon": 10.6031,
        "surface_km2": 17.8,
        "coastal": True,
        "profile": "residential",
    },
    {
        "name": "Akouda",
        "description": "Pole urbain mixte entre habitat, services et agriculture",
        "center_lat": 35.8691,
        "center_lon": 10.5653,
        "surface_km2": 12.4,
        "coastal": False,
        "profile": "urban",
    },
    {
        "name": "Chott Meriem",
        "description": "Zone littorale et agricole au nord-ouest de Hammam Sousse",
        "center_lat": 35.9381,
        "center_lon": 10.5550,
        "surface_km2": 21.6,
        "coastal": True,
        "profile": "agricultural",
    },
    {
        "name": "Zone industrielle de Sidi Abdelhamid",
        "description": "Secteur industriel et logistique au sud-ouest de Sousse",
        "center_lat": 35.8053,
        "center_lon": 10.6407,
        "surface_km2": 9.2,
        "coastal": False,
        "profile": "industrial",
    },
    {
        "name": "Kalaa Kebira",
        "description": "Grande commune de l'interieur orientee vers l'habitat et l'agroalimentaire",
        "center_lat": 35.8870,
        "center_lon": 10.4324,
        "surface_km2": 67.5,
        "coastal": False,
        "profile": "agricultural",
    },
    {
        "name": "M'saken",
        "description": "Carrefour urbain majeur du centre du gouvernorat de Sousse",
        "center_lat": 35.7333,
        "center_lon": 10.5833,
        "surface_km2": 48.0,
        "coastal": False,
        "profile": "urban",
    },
    {
        "name": "Sidi Bou Ali",
        "description": "Commune du nord du gouvernorat a dominante agricole",
        "center_lat": 35.9567,
        "center_lon": 10.4731,
        "surface_km2": 55.0,
        "coastal": False,
        "profile": "agricultural",
    },
    {
        "name": "Enfidha",
        "description": "Corridor logistique du sud du gouvernorat, proche de l'aeroport",
        "center_lat": 36.1353,
        "center_lon": 10.3808,
        "surface_km2": 72.0,
        "coastal": False,
        "profile": "logistics",
    },
]

ZONE_BY_NAME = {zone["name"]: zone for zone in SOUSSE_ZONES}

_COASTAL_SENSOR_OFFSETS = [
    (-0.0045, -0.0110),
    (0.0020, -0.0090),
    (0.0055, -0.0075),
    (-0.0030, -0.0065),
    (0.0010, -0.0080),
]

_INLAND_SENSOR_OFFSETS = [
    (-0.0060, -0.0065),
    (0.0035, -0.0025),
    (0.0065, 0.0040),
    (-0.0020, 0.0060),
    (0.0015, -0.0075),
]


def seeded_zone_records(rows: list[dict]) -> list[dict]:
    """Attach local metadata to DB rows for the Sousse-specific seeded zones only."""
    return [
        {**ZONE_BY_NAME[row["nom"]], "id": row["id"]}
        for row in rows
        if row["nom"] in ZONE_BY_NAME
    ]


def sensor_coordinate(zone: dict, slot: int) -> tuple[float, float]:
    offsets = _COASTAL_SENSOR_OFFSETS if zone["coastal"] else _INLAND_SENSOR_OFFSETS
    lat_offset, lon_offset = offsets[slot % len(offsets)]
    return round(zone["center_lat"] + lat_offset, 6), round(zone["center_lon"] + lon_offset, 6)


def zone_profile(zone_name: str) -> str:
    return ZONE_BY_NAME.get(zone_name, {}).get("profile", "urban")


def haversine_km(start: dict, end: dict) -> float:
    """Great-circle distance between two zone centers."""
    lat1 = radians(start["center_lat"])
    lon1 = radians(start["center_lon"])
    lat2 = radians(end["center_lat"])
    lon2 = radians(end["center_lon"])

    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(a))
