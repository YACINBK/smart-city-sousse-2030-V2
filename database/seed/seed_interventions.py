"""Seeds interventions table with realistic workflow data."""

import random
from datetime import datetime, timedelta
from database.connection import execute_query

random.seed(55)

DESCRIPTIONS = [
    "Anomalie détectée sur les mesures PM2.5 — calibration requise",
    "Capteur ne répond plus aux requêtes réseau",
    "Drift de température constaté — remplacement sonde",
    "Panneau solaire endommagé — remplacement batterie",
    "Connexion intermittente — vérification câblage",
    "Firmware obsolète — mise à jour requise",
    "Boîtier fissuré suite aux intempéries",
    "Capteur saturé — nettoyage filtre PM",
]

STATUTS_SEQUENCE = [
    "DEMANDE",
    "TECH1_ASSIGNÉ", "TECH1_ASSIGNÉ",
    "TECH2_VALIDE", "TECH2_VALIDE",
    "IA_VALIDE",
    "TERMINÉ", "TERMINÉ", "TERMINÉ",
]


def seed_interventions():
    print("  → Seeding interventions...")
    capteurs = execute_query("SELECT id FROM capteurs")
    capteur_ids = [c["id"] for c in capteurs]
    techniciens = execute_query("SELECT id FROM techniciens")
    tech_ids = [t["id"] for t in techniciens]

    for i in range(60):
        capteur_id = random.choice(capteur_ids)
        statut = STATUTS_SEQUENCE[i % len(STATUTS_SEQUENCE)]
        created_at = datetime.now() - timedelta(days=random.randint(0, 60))
        desc = random.choice(DESCRIPTIONS)
        priorite = random.choice(["BASSE", "NORMALE", "NORMALE", "HAUTE", "URGENTE"])

        tech1_id = random.choice(tech_ids) if statut != "DEMANDE" else None
        tech2_id = random.choice([t for t in tech_ids if t != tech1_id]) \
                   if statut in ("TECH2_VALIDE", "IA_VALIDE", "TERMINÉ") else None
        completed_at = datetime.now() - timedelta(days=random.randint(0, 5)) \
                       if statut == "TERMINÉ" else None
        ai_val = '{"approved": true, "confidence": 0.91, "reason": "Intervention conforme."}' \
                 if statut in ("IA_VALIDE", "TERMINÉ") else None

        execute_query(
            """INSERT INTO interventions
               (capteur_id, tech1_id, tech2_id, statut, description, priorite,
                ai_validation, created_at, completed_at)
               VALUES (:cid, :t1, :t2, :statut, :desc, :prio,
                       :ai::jsonb, :created, :completed)""",
            {
                "cid": capteur_id, "t1": tech1_id, "t2": tech2_id,
                "statut": statut, "desc": desc, "prio": priorite,
                "ai": ai_val, "created": created_at, "completed": completed_at,
            },
        )

    # Seed FSM states for interventions
    interventions = execute_query("SELECT id, statut FROM interventions")
    for inv in interventions:
        execute_query(
            """INSERT INTO fsm_states (entity_type, entity_id, state)
               VALUES ('intervention', :id, :state)
               ON CONFLICT (entity_type, entity_id) DO UPDATE SET state=EXCLUDED.state""",
            {"id": inv["id"], "state": inv["statut"]},
        )

    print("     ✓ 60 interventions")
