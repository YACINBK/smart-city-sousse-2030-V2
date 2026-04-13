"""Seeds vehicules table."""

import random
from database.connection import execute_query

random.seed(77)

TYPES = ["camion", "berline", "moto", "bus", "utilitaire"]
CONDUCTEURS = ["Karim Ben", "Sana M.", "Rami T.", "Ali H.", "Leila S."]
STATUTS = ["STATIONNÉ", "STATIONNÉ", "STATIONNÉ", "EN_ROUTE", "EN_PANNE"]


def seed_vehicules():
    print("  → Seeding vehicules...")
    zones = execute_query("SELECT id FROM zones")
    zone_ids = [z["id"] for z in zones]

    for i in range(1, 31):
        vtype = TYPES[i % len(TYPES)]
        statut = STATUTS[i % len(STATUTS)]
        zone_id = random.choice(zone_ids)
        immat = f"TN-{1000 + i}-NS"

        execute_query(
            """INSERT INTO vehicules (immatriculation, type, zone_id, statut, conducteur, autonome)
               VALUES (:immat, :type, :zone_id, :statut, :conducteur, :autonome)
               ON CONFLICT (immatriculation) DO NOTHING""",
            {
                "immat": immat, "type": vtype, "zone_id": zone_id, "statut": statut,
                "conducteur": random.choice(CONDUCTEURS),
                "autonome": random.choice([True, True, False]),
            },
        )

    # Seed FSM states
    vehicules = execute_query("SELECT id, statut FROM vehicules")
    for v in vehicules:
        execute_query(
            """INSERT INTO fsm_states (entity_type, entity_id, state)
               VALUES ('vehicule', :id, :state)
               ON CONFLICT (entity_type, entity_id) DO UPDATE SET state=EXCLUDED.state""",
            {"id": v["id"], "state": v["statut"]},
        )

    # Seed some trajets
    for i in range(50):
        zone_ids_2 = random.sample(zone_ids, 2)
        execute_query(
            """INSERT INTO trajets (vehicule_id, zone_depart_id, zone_arrivee_id,
               distance_km, economie_co2, duree_minutes)
               VALUES (:vid, :zdep, :zarr, :dist, :eco, :dur)""",
            {
                "vid": random.randint(1, 30),
                "zdep": zone_ids_2[0], "zarr": zone_ids_2[1],
                "dist": round(random.uniform(1, 25), 2),
                "eco": round(random.uniform(0.5, 8.0), 2),
                "dur": random.randint(5, 60),
            },
        )

    print("     ✓ 30 vehicules, 50 trajets")
