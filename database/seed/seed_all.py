"""Orchestrates all seeders. Run: python database/seed/seed_all.py"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.seed.seed_capteurs import seed_capteurs
from database.seed.seed_citoyens import seed_citoyens
from database.seed.seed_vehicules import seed_vehicules
from database.seed.seed_interventions import seed_interventions
from database.seed.seed_mesures import seed_mesures


def seed_all():
    print("🌱 Seeding Neo-Sousse 2030 database...")
    seed_capteurs()
    seed_citoyens()
    seed_vehicules()
    seed_interventions()
    seed_mesures()
    print("✅ All data seeded successfully.")


if __name__ == "__main__":
    seed_all()
