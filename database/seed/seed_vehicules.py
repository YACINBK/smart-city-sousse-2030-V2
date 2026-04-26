"""Seeds vehicules and trajets with Sousse-governorate-aware routing."""

from __future__ import annotations

import random

from database.connection import execute_query
from database.seed.geo import haversine_km, seeded_zone_records

random.seed(77)

TYPES = ["camion", "berline", "moto", "bus", "utilitaire"]
CONDUCTEURS = ["Karim Ben", "Sana M.", "Rami T.", "Ali H.", "Leila S."]
STATUTS = ["STATIONNÉ", "STATIONNÉ", "STATIONNÉ", "EN_ROUTE", "EN_PANNE"]
AVERAGE_SPEED_KMH = {
    "camion": 35,
    "berline": 48,
    "moto": 42,
    "bus": 32,
    "utilitaire": 38,
}


def _route_distance_km(start_zone: dict, end_zone: dict) -> float:
    base_distance = haversine_km(start_zone, end_zone)
    road_factor = random.uniform(1.08, 1.28)
    return round(max(1.2, base_distance * road_factor), 2)


def _route_duration_minutes(distance_km: float, vehicle_type: str) -> int:
    avg_speed = AVERAGE_SPEED_KMH[vehicle_type] * random.uniform(0.9, 1.08)
    return max(5, round((distance_km / avg_speed) * 60))


def _co2_savings(distance_km: float, vehicle_type: str) -> float:
    factor = {
        "camion": 0.34,
        "berline": 0.21,
        "moto": 0.11,
        "bus": 0.29,
        "utilitaire": 0.24,
    }[vehicle_type]
    return round(distance_km * factor * random.uniform(0.85, 1.15), 2)


def seed_vehicules() -> None:
    print("  -> Seeding vehicules and trajets...")

    zones = seeded_zone_records(execute_query("SELECT id, nom FROM zones ORDER BY id"))
    if len(zones) < 2:
        print("     ! Not enough Sousse zones found, skipping vehicules.")
        return

    zone_ids = [zone["id"] for zone in zones]

    for index in range(1, 31):
        vehicle_type = TYPES[index % len(TYPES)]
        statut = STATUTS[index % len(STATUTS)]
        zone_id = random.choice(zone_ids)
        immat = f"TN-{1000 + index}-NS"

        execute_query(
            """INSERT INTO vehicules (immatriculation, type, zone_id, statut, conducteur, autonome)
               VALUES (:immat, :type, :zone_id, :statut, :conducteur, :autonome)
               ON CONFLICT (immatriculation) DO NOTHING""",
            {
                "immat": immat,
                "type": vehicle_type,
                "zone_id": zone_id,
                "statut": statut,
                "conducteur": random.choice(CONDUCTEURS),
                "autonome": random.choice([True, True, False]),
            },
        )

    vehicules = execute_query("SELECT id, statut, type FROM vehicules ORDER BY id")
    for vehicule in vehicules:
        execute_query(
            """INSERT INTO fsm_states (entity_type, entity_id, state)
               VALUES ('vehicule', :id, :state)
               ON CONFLICT (entity_type, entity_id) DO UPDATE SET state=EXCLUDED.state""",
            {"id": vehicule["id"], "state": vehicule["statut"]},
        )

    for _ in range(50):
        start_zone, end_zone = random.sample(zones, 2)
        vehicule = random.choice(vehicules)
        distance_km = _route_distance_km(start_zone, end_zone)
        duree_minutes = _route_duration_minutes(distance_km, vehicule["type"])
        economie_co2 = _co2_savings(distance_km, vehicule["type"])

        execute_query(
            """INSERT INTO trajets (vehicule_id, zone_depart_id, zone_arrivee_id,
               distance_km, economie_co2, duree_minutes)
               VALUES (:vid, :zdep, :zarr, :dist, :eco, :dur)""",
            {
                "vid": vehicule["id"],
                "zdep": start_zone["id"],
                "zarr": end_zone["id"],
                "dist": distance_km,
                "eco": economie_co2,
                "dur": duree_minutes,
            },
        )

    print("     - 30 vehicules, 50 trajets")
