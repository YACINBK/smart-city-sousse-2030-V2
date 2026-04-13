-- =============================================================
--  Neo-Sousse 2030 — Database Schema (3NF, TimescaleDB)
-- =============================================================

CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- ─── Lookup / reference tables ────────────────────────────────

CREATE TABLE zones (
    id          SERIAL PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    geom_lat    DECIMAL(9,6),
    geom_lon    DECIMAL(9,6),
    superficie  DECIMAL(10,2)  -- km²
);

-- ─── Urban sensors ────────────────────────────────────────────

CREATE TABLE capteurs (
    id                  SERIAL PRIMARY KEY,
    nom                 VARCHAR(100) NOT NULL,
    type                VARCHAR(50)  NOT NULL
                        CHECK (type IN ('qualite_air','temperature','trafic','bruit','humidite')),
    zone_id             INTEGER      REFERENCES zones(id) ON DELETE SET NULL,
    statut              VARCHAR(20)  NOT NULL DEFAULT 'INACTIF'
                        CHECK (statut IN ('INACTIF','ACTIF','SIGNALÉ','EN_MAINTENANCE','HORS_SERVICE')),
    date_installation   TIMESTAMPTZ,
    fabricant           VARCHAR(100),
    modele              VARCHAR(100),
    latitude            DECIMAL(9,6),
    longitude           DECIMAL(9,6),
    created_at          TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_capteurs_statut  ON capteurs(statut);
CREATE INDEX idx_capteurs_zone    ON capteurs(zone_id);
CREATE INDEX idx_capteurs_type    ON capteurs(type);

-- ─── Time-series measurements (TimescaleDB hypertable) ────────

CREATE TABLE mesures (
    id          BIGSERIAL,
    capteur_id  INTEGER      NOT NULL REFERENCES capteurs(id) ON DELETE CASCADE,
    mesure_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    pm25        DECIMAL(6,2),
    pm10        DECIMAL(6,2),
    temperature DECIMAL(5,2),
    humidite    DECIMAL(5,2),
    co2         DECIMAL(7,2),
    no2         DECIMAL(7,2),
    niveau_bruit DECIMAL(5,2),
    indice_trafic DECIMAL(5,2),  -- 0-100
    PRIMARY KEY (id, mesure_at)
);

SELECT create_hypertable('mesures', 'mesure_at',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE);

CREATE INDEX idx_mesures_capteur ON mesures(capteur_id, mesure_at DESC);

-- ─── Citizens ─────────────────────────────────────────────────

CREATE TABLE citoyens (
    id               SERIAL PRIMARY KEY,
    nom              VARCHAR(100) NOT NULL,
    prenom           VARCHAR(100) NOT NULL,
    email            VARCHAR(200) UNIQUE,
    telephone        VARCHAR(20),
    zone_id          INTEGER      REFERENCES zones(id) ON DELETE SET NULL,
    score_ecolo      DECIMAL(5,2) DEFAULT 0
                     CHECK (score_ecolo >= 0 AND score_ecolo <= 100),
    date_inscription TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_citoyens_zone       ON citoyens(zone_id);
CREATE INDEX idx_citoyens_score_ecolo ON citoyens(score_ecolo DESC);

-- ─── Technicians ──────────────────────────────────────────────

CREATE TABLE techniciens (
    id          SERIAL PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL,
    prenom      VARCHAR(100) NOT NULL,
    specialite  VARCHAR(100),
    telephone   VARCHAR(20),
    disponible  BOOLEAN      DEFAULT TRUE,
    created_at  TIMESTAMPTZ  DEFAULT NOW()
);

-- ─── Interventions ────────────────────────────────────────────

CREATE TABLE interventions (
    id              SERIAL PRIMARY KEY,
    capteur_id      INTEGER      NOT NULL REFERENCES capteurs(id),
    tech1_id        INTEGER      REFERENCES techniciens(id),
    tech2_id        INTEGER      REFERENCES techniciens(id),
    statut          VARCHAR(30)  NOT NULL DEFAULT 'DEMANDE'
                    CHECK (statut IN ('DEMANDE','TECH1_ASSIGNÉ','TECH2_VALIDE','IA_VALIDE','TERMINÉ')),
    description     TEXT,
    rapport_tech1   TEXT,
    rapport_tech2   TEXT,
    ai_validation   JSONB,       -- {"approved": bool, "confidence": float, "reason": str}
    priorite        VARCHAR(10)  DEFAULT 'NORMALE'
                    CHECK (priorite IN ('BASSE','NORMALE','HAUTE','URGENTE')),
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_interventions_statut  ON interventions(statut);
CREATE INDEX idx_interventions_capteur ON interventions(capteur_id);
CREATE INDEX idx_interventions_dates   ON interventions(created_at DESC);

-- ─── Autonomous vehicles ──────────────────────────────────────

CREATE TABLE vehicules (
    id              SERIAL PRIMARY KEY,
    immatriculation VARCHAR(20)  UNIQUE NOT NULL,
    type            VARCHAR(50)  NOT NULL
                    CHECK (type IN ('camion','berline','moto','bus','utilitaire')),
    zone_id         INTEGER      REFERENCES zones(id) ON DELETE SET NULL,
    statut          VARCHAR(20)  NOT NULL DEFAULT 'STATIONNÉ'
                    CHECK (statut IN ('STATIONNÉ','EN_ROUTE','EN_PANNE','ARRIVÉ')),
    conducteur      VARCHAR(100),
    autonome        BOOLEAN      DEFAULT TRUE,
    created_at      TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_vehicules_statut ON vehicules(statut);
CREATE INDEX idx_vehicules_zone   ON vehicules(zone_id);

-- ─── Alerts ───────────────────────────────────────────────────

CREATE TABLE alertes (
    id          SERIAL PRIMARY KEY,
    type        VARCHAR(50)  NOT NULL,
    entity_type VARCHAR(50),                         -- 'capteur', 'intervention', 'vehicule'
    entity_id   INTEGER,
    message     TEXT         NOT NULL,
    severity    VARCHAR(10)  NOT NULL DEFAULT 'INFO'
                CHECK (severity IN ('INFO','WARNING','CRITICAL')),
    resolved    BOOLEAN      DEFAULT FALSE,
    created_at  TIMESTAMPTZ  DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_alertes_entity   ON alertes(entity_type, entity_id);
CREATE INDEX idx_alertes_severity ON alertes(severity) WHERE resolved = FALSE;

-- ─── FSM state tracking ───────────────────────────────────────

CREATE TABLE fsm_states (
    entity_type VARCHAR(50)  NOT NULL,
    entity_id   INTEGER      NOT NULL,
    state       VARCHAR(50)  NOT NULL,
    updated_at  TIMESTAMPTZ  DEFAULT NOW(),
    PRIMARY KEY (entity_type, entity_id)
);

CREATE TABLE fsm_history (
    id           BIGSERIAL   PRIMARY KEY,
    entity_type  VARCHAR(50) NOT NULL,
    entity_id    INTEGER     NOT NULL,
    from_state   VARCHAR(50),
    event        VARCHAR(50) NOT NULL,
    to_state     VARCHAR(50) NOT NULL,
    triggered_at TIMESTAMPTZ DEFAULT NOW(),
    triggered_by VARCHAR(100)             -- 'user:jean', 'system:scheduler', 'ai:module'
);

CREATE INDEX idx_fsm_history_entity ON fsm_history(entity_type, entity_id, triggered_at DESC);

-- ─── Trajets (for CO2 economy queries) ───────────────────────

CREATE TABLE trajets (
    id              SERIAL PRIMARY KEY,
    vehicule_id     INTEGER      REFERENCES vehicules(id),
    zone_depart_id  INTEGER      REFERENCES zones(id),
    zone_arrivee_id INTEGER      REFERENCES zones(id),
    distance_km     DECIMAL(8,2),
    economie_co2    DECIMAL(8,2),   -- kg CO2 saved vs. thermal vehicle
    duree_minutes   INTEGER,
    date_trajet     TIMESTAMPTZ  DEFAULT NOW()
);

CREATE INDEX idx_trajets_co2 ON trajets(economie_co2 DESC);
