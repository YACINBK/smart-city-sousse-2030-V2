"""Seeds zones, techniciens, and capteurs tables."""

from __future__ import annotations

import random
from datetime import datetime, timedelta

from database.connection import execute_query
from database.seed.geo import SOUSSE_ZONES, seeded_zone_records, sensor_coordinate

TECHNICIENS = [
    ("Ben Ali", "Mohamed", "electronique"),
    ("Trabelsi", "Fatma", "mecanique"),
    ("Mansour", "Karim", "informatique"),
    ("Chaabane", "Nour", "electronique"),
    ("Bouzid", "Yassine", "mecanique"),
]

CAPTEUR_TYPES = ["qualite_air", "temperature", "trafic", "bruit", "humidite"]
FABRICANTS = ["SensorTech", "AirMetrics", "UrbanSense", "SmartCity"]
STATUTS = ["ACTIF", "ACTIF", "ACTIF", "ACTIF", "SIGNALÉ", "EN_MAINTENANCE", "HORS_SERVICE"]


def seed_capteurs() -> None:
    print("  -> Seeding Sousse governorate zones, techniciens, capteurs...")

    for zone in SOUSSE_ZONES:
        execute_query(
            """INSERT INTO zones (nom, description, geom_lat, geom_lon, superficie)
               VALUES (:nom, :desc, :lat, :lon, :sup)
               ON CONFLICT (nom) DO NOTHING""",
            {
                "nom": zone["name"],
                "desc": zone["description"],
                "lat": zone["center_lat"],
                "lon": zone["center_lon"],
                "sup": zone["surface_km2"],
            },
        )

    for nom, prenom, spec in TECHNICIENS:
        execute_query(
            """INSERT INTO techniciens (nom, prenom, specialite)
               VALUES (:nom, :prenom, :spec)
               ON CONFLICT DO NOTHING""",
            {"nom": nom, "prenom": prenom, "spec": spec},
        )

    zones = seeded_zone_records(execute_query("SELECT id, nom FROM zones ORDER BY id"))
    if not zones:
        print("     ! No Sousse zones found, skipping capteurs.")
        return

    sensors_per_zone = 5
    total_sensors = len(zones) * sensors_per_zone

    random.seed(42)
    for index in range(total_sensors):
        zone = zones[index % len(zones)]
        zone_slot = index // len(zones)
        capteur_type = CAPTEUR_TYPES[(index + 1) % len(CAPTEUR_TYPES)]
        statut = STATUTS[(index + 1) % len(STATUTS)]
        fabricant = FABRICANTS[(index + 1) % len(FABRICANTS)]
        install_date = datetime.now() - timedelta(days=random.randint(30, 730))
        latitude, longitude = sensor_coordinate(zone, zone_slot)

        execute_query(
            """INSERT INTO capteurs (nom, type, zone_id, statut, date_installation,
               fabricant, modele, latitude, longitude)
               VALUES (:nom, :type, :zone_id, :statut, :install_date,
                       :fab, :mod, :lat, :lon)
               ON CONFLICT DO NOTHING""",
            {
                "nom": f"Capteur-{capteur_type[:3].upper()}-{index + 1:03d}",
                "type": capteur_type,
                "zone_id": zone["id"],
                "statut": statut,
                "install_date": install_date,
                "fab": fabricant,
                "mod": f"Model-{random.choice(['X1', 'X2', 'Pro', 'Elite'])}",
                "lat": latitude,
                "lon": longitude,
            },
        )

    capteurs = execute_query("SELECT id, statut FROM capteurs")
    for capteur in capteurs:
        execute_query(
            """INSERT INTO fsm_states (entity_type, entity_id, state)
               VALUES ('capteur', :id, :state)
               ON CONFLICT (entity_type, entity_id) DO UPDATE SET state=EXCLUDED.state""",
            {"id": capteur["id"], "state": capteur["statut"]},
        )

    print(
        f"     - {len(zones)} zones, {len(TECHNICIENS)} techniciens, {total_sensors} capteurs"
    )
