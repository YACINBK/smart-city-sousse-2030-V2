"""Seeds citoyens table with 100 realistic Tunisian citizens."""

import random

from faker import Faker

from database.connection import execute_query

fake = Faker("fr_FR")
random.seed(123)

TUNISIAN_FIRST = [
    "Mohamed",
    "Ahmed",
    "Ali",
    "Fatma",
    "Nour",
    "Yasmine",
    "Karim",
    "Sana",
    "Omar",
    "Leila",
    "Rami",
    "Amira",
    "Zied",
]
TUNISIAN_LAST = [
    "Ben Ali",
    "Trabelsi",
    "Mansour",
    "Chaabane",
    "Bouzid",
    "Jebali",
    "Hamdi",
    "Sfaxi",
    "Nasr",
    "Khelifi",
    "Miled",
]


def seed_citoyens():
    print("  -> Seeding citoyens...")
    zones = execute_query("SELECT id FROM zones")
    zone_ids = [zone["id"] for zone in zones]

    for index in range(100):
        zone_id = random.choice(zone_ids)
        prenom = random.choice(TUNISIAN_FIRST)
        nom = random.choice(TUNISIAN_LAST)
        email = f"{prenom.lower()}.{nom.lower().replace(' ', '')}{index}@neo-sousse.tn"
        score = round(random.gauss(55, 20), 2)
        score = max(0, min(100, score))

        execute_query(
            """INSERT INTO citoyens (nom, prenom, email, telephone, zone_id, score_ecolo)
               VALUES (:nom, :prenom, :email, :tel, :zone_id, :score)
               ON CONFLICT (email) DO NOTHING""",
            {
                "nom": nom,
                "prenom": prenom,
                "email": email,
                "tel": fake.phone_number()[:20],
                "zone_id": zone_id,
                "score": score,
            },
        )
    print("     - 100 citoyens")
