"""Seeds interventions table with realistic workflow data."""

import random
from datetime import datetime, timedelta

from database.connection import execute_query

random.seed(55)

DESCRIPTIONS = [
    "Anomalie detectee sur les mesures PM2.5 - calibration requise",
    "Capteur ne repond plus aux requetes reseau",
    "Drift de temperature constate - remplacement sonde",
    "Panneau solaire endommage - remplacement batterie",
    "Connexion intermittente - verification cablage",
    "Firmware obsolete - mise a jour requise",
    "Boitier fissure suite aux intemperies",
    "Capteur sature - nettoyage filtre PM",
]

STATUTS_SEQUENCE = [
    "DEMANDE",
    "TECH1_ASSIGNÉ",
    "TECH1_ASSIGNÉ",
    "TECH2_VALIDE",
    "TECH2_VALIDE",
    "IA_VALIDE",
    "TERMINÉ",
    "TERMINÉ",
    "TERMINÉ",
]


def seed_interventions():
    print("  -> Seeding interventions...")
    capteurs = execute_query("SELECT id FROM capteurs")
    capteur_ids = [capteur["id"] for capteur in capteurs]
    techniciens = execute_query("SELECT id FROM techniciens")
    tech_ids = [tech["id"] for tech in techniciens]

    for _ in range(60):
        capteur_id = random.choice(capteur_ids)
        statut = STATUTS_SEQUENCE[_ % len(STATUTS_SEQUENCE)]
        created_at = datetime.now() - timedelta(days=random.randint(0, 60))
        description = random.choice(DESCRIPTIONS)
        priorite = random.choice(["BASSE", "NORMALE", "NORMALE", "HAUTE", "URGENTE"])

        tech1_id = random.choice(tech_ids) if statut != "DEMANDE" else None
        tech2_candidates = [tech_id for tech_id in tech_ids if tech_id != tech1_id]
        tech2_id = (
            random.choice(tech2_candidates)
            if statut in ("TECH2_VALIDE", "IA_VALIDE", "TERMINÉ")
            else None
        )
        completed_at = (
            datetime.now() - timedelta(days=random.randint(0, 5))
            if statut == "TERMINÉ"
            else None
        )
        ai_val = (
            '{"approved": true, "confidence": 0.91, "reason": "Intervention conforme."}'
            if statut in ("IA_VALIDE", "TERMINÉ")
            else None
        )

        execute_query(
            """INSERT INTO interventions
               (capteur_id, tech1_id, tech2_id, statut, description, priorite,
                ai_validation, created_at, completed_at)
               VALUES (:cid, :t1, :t2, :statut, :desc, :prio,
                       CAST(:ai AS JSONB), :created, :completed)""",
            {
                "cid": capteur_id,
                "t1": tech1_id,
                "t2": tech2_id,
                "statut": statut,
                "desc": description,
                "prio": priorite,
                "ai": ai_val,
                "created": created_at,
                "completed": completed_at,
            },
        )

    interventions = execute_query("SELECT id, statut FROM interventions")
    for intervention in interventions:
        execute_query(
            """INSERT INTO fsm_states (entity_type, entity_id, state)
               VALUES ('intervention', :id, :state)
               ON CONFLICT (entity_type, entity_id) DO UPDATE SET state=EXCLUDED.state""",
            {"id": intervention["id"], "state": intervention["statut"]},
        )

    print("     - 60 interventions")
