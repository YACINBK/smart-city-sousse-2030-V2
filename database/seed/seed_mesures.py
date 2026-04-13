"""
Seeds mesures table with 90 days of realistic time-series data.

Uses sinusoidal patterns + Gaussian noise to generate believable sensor readings:
  - Daily temperature cycle
  - Higher pollution at peak hours (7-9h, 17-19h)
  - Random anomaly spikes (simulating sensor malfunction)

Total rows ≈ 90 days × 24h × ~15 active sensors = ~32,400 rows (well above 1000+ target).
"""

import random
import math
from datetime import datetime, timedelta
from database.connection import execute_query

random.seed(99)


def _pm25(hour: int, day_of_week: int, zone_type: str) -> float:
    """Generate realistic PM2.5 based on time and zone type."""
    base = 30 if "Industrielle" in zone_type else 18
    # Peak traffic hours
    peak = 1.0 + 0.6 * math.exp(-0.5 * ((hour - 8) / 2) ** 2) \
               + 0.4 * math.exp(-0.5 * ((hour - 18) / 1.5) ** 2)
    # Weekend reduction
    weekend_factor = 0.75 if day_of_week >= 5 else 1.0
    noise = random.gauss(0, 3)
    return max(1, base * peak * weekend_factor + noise)


def _temperature(hour: int, month: int) -> float:
    """Seasonal + daily temperature pattern for Sousse, Tunisia."""
    seasonal_base = 15 + 12 * math.sin(2 * math.pi * (month - 3) / 12)
    daily = 6 * math.sin(2 * math.pi * (hour - 6) / 24)
    return round(seasonal_base + daily + random.gauss(0, 1.2), 2)


def seed_mesures():
    print("  → Seeding mesures (time-series, 90 days)...")
    capteurs = execute_query(
        "SELECT c.id, c.type, z.nom AS zone FROM capteurs c "
        "LEFT JOIN zones z ON z.id = c.zone_id "
        "WHERE c.statut IN ('ACTIF', 'SIGNALÉ')"
    )
    if not capteurs:
        print("     ⚠ No active capteurs found, skipping mesures.")
        return

    now = datetime.utcnow()
    rows_inserted = 0
    batch: list[dict] = []

    for day_offset in range(89, -1, -1):
        day_dt = now - timedelta(days=day_offset)
        month = day_dt.month
        dow = day_dt.weekday()

        for hour in range(24):
            ts = day_dt.replace(hour=hour, minute=0, second=0, microsecond=0)
            for cap in capteurs:
                cap_type = cap["type"]
                zone_name = cap.get("zone") or ""

                # Random data dropout (1% chance — simulates outage)
                if random.random() < 0.01:
                    continue

                # Spike anomaly (2% chance)
                spike = random.random() < 0.02

                pm25_val = _pm25(hour, dow, zone_name) * (3 if spike else 1) \
                           if cap_type == "qualite_air" else None
                pm10_val = (pm25_val * random.uniform(1.4, 2.0)) if pm25_val else None
                temp_val = _temperature(hour, month) if cap_type in ("temperature", "qualite_air") else None
                hum_val = max(20, min(95, random.gauss(60, 15))) \
                          if cap_type in ("humidite", "qualite_air") else None
                co2_val = max(350, random.gauss(420, 40)) if cap_type == "qualite_air" else None
                no2_val = max(0, random.gauss(25, 10)) if cap_type == "qualite_air" else None
                bruit_val = max(30, random.gauss(55, 12)) if cap_type == "bruit" else None
                trafic_val = max(0, min(100, random.gauss(
                    60 if 7 <= hour <= 9 or 17 <= hour <= 19 else 30, 15
                ))) if cap_type == "trafic" else None

                batch.append({
                    "capteur_id": cap["id"], "mesure_at": ts,
                    "pm25": round(pm25_val, 2) if pm25_val else None,
                    "pm10": round(pm10_val, 2) if pm10_val else None,
                    "temperature": temp_val,
                    "humidite": round(hum_val, 2) if hum_val else None,
                    "co2": round(co2_val, 2) if co2_val else None,
                    "no2": round(no2_val, 2) if no2_val else None,
                    "niveau_bruit": round(bruit_val, 2) if bruit_val else None,
                    "indice_trafic": round(trafic_val, 2) if trafic_val else None,
                })

                # Flush batch every 500 rows
                if len(batch) >= 500:
                    _insert_batch(batch)
                    rows_inserted += len(batch)
                    batch.clear()

    if batch:
        _insert_batch(batch)
        rows_inserted += len(batch)

    print(f"     ✓ {rows_inserted:,} mesures inserted")


def _insert_batch(batch: list[dict]) -> None:
    for row in batch:
        execute_query(
            """INSERT INTO mesures
               (capteur_id, mesure_at, pm25, pm10, temperature, humidite,
                co2, no2, niveau_bruit, indice_trafic)
               VALUES (:capteur_id, :mesure_at, :pm25, :pm10, :temperature, :humidite,
                       :co2, :no2, :niveau_bruit, :indice_trafic)""",
            row,
        )
