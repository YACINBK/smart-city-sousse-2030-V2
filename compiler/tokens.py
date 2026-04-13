"""Token types and the French→canonical keyword map."""
from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    # ── Intents ───────────────────────────────────────────────
    INTENT_SHOW  = auto()   # affiche, montre, donne, liste, quels, quelles
    INTENT_COUNT = auto()   # combien, compte, nombre
    INTENT_AVG   = auto()   # moyenne, calcule la moyenne
    INTENT_TOP   = auto()   # les N premiers / top N

    # ── Entities (DB tables) ──────────────────────────────────
    ENTITY       = auto()   # capteurs, interventions, citoyens, véhicules, mesures, zones, trajets

    # ── Attributes (DB columns or column groups) ──────────────
    ATTRIBUTE    = auto()   # statut, zone, pm25, pm10, température, …

    # ── Clause keywords ───────────────────────────────────────
    KW_WHERE     = auto()   # où, avec, dont, ayant, qui ont
    KW_ORDER_ASC = auto()   # croissant, par ordre croissant, du plus bas
    KW_ORDER_DESC= auto()   # décroissant, du plus haut, du plus élevé
    KW_GROUPBY   = auto()   # par, groupé par, selon, par zone
    KW_LIMIT     = auto()   # limité à, au maximum, les N premiers

    # ── Logical operators ─────────────────────────────────────
    KW_AND       = auto()   # et
    KW_OR        = auto()   # ou

    # ── Comparators ───────────────────────────────────────────
    CMP_EQ  = auto()   # =, égal, est, vaut
    CMP_GT  = auto()   # >, supérieur, dépasse, plus grand que
    CMP_LT  = auto()   # <, inférieur, sous, plus petit que, moins de
    CMP_GTE = auto()   # >=, au moins, minimum
    CMP_LTE = auto()   # <=, au plus, maximum

    # ── Literals ──────────────────────────────────────────────
    NUMBER  = auto()
    STRING  = auto()   # quoted or unquoted value after comparator

    # ── Special ───────────────────────────────────────────────
    IDENTIFIER = auto()  # unrecognized word → resolved in semantic phase
    EOF        = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    pos: int


# ──────────────────────────────────────────────────────────────
#  French keyword → canonical TokenType  (ORDER MATTERS — longer
#  phrases must appear before their sub-words in multi-word scan)
# ──────────────────────────────────────────────────────────────

# Multi-word phrases (up to 4 tokens), checked first in lexer
PHRASE_MAP: dict[str, TokenType] = {
    "par ordre décroissant":   TokenType.KW_ORDER_DESC,
    "par ordre croissant":     TokenType.KW_ORDER_ASC,
    "du plus élevé au plus bas": TokenType.KW_ORDER_DESC,
    "du plus bas au plus élevé": TokenType.KW_ORDER_ASC,
    "du plus haut":            TokenType.KW_ORDER_DESC,
    "du plus bas":             TokenType.KW_ORDER_ASC,
    "plus grand que":          TokenType.CMP_GT,
    "plus petit que":          TokenType.CMP_LT,
    "plus élevé que":          TokenType.CMP_GT,
    "moins de":                TokenType.CMP_LT,
    "au moins":                TokenType.CMP_GTE,
    "au plus":                 TokenType.CMP_LTE,
    "qui ont":                 TokenType.KW_WHERE,
    "qui a":                   TokenType.KW_WHERE,
    "nombre de":               TokenType.INTENT_COUNT,
    "calcule la moyenne":      TokenType.INTENT_AVG,
    "la moyenne":              TokenType.INTENT_AVG,
    "les plus":                TokenType.KW_ORDER_DESC,   # "les 5 zones les plus polluées"
    "groupé par":              TokenType.KW_GROUPBY,
    "trié par":                TokenType.KW_GROUPBY,
    "limité à":                TokenType.KW_LIMIT,
    "au maximum":              TokenType.KW_LIMIT,
}

# Single-word keywords
KEYWORD_MAP: dict[str, TokenType] = {
    # ── INTENT_SHOW
    "affiche":    TokenType.INTENT_SHOW,
    "montre":     TokenType.INTENT_SHOW,
    "donne":      TokenType.INTENT_SHOW,
    "liste":      TokenType.INTENT_SHOW,
    "donner":     TokenType.INTENT_SHOW,
    "afficher":   TokenType.INTENT_SHOW,
    "montrer":    TokenType.INTENT_SHOW,
    "quels":      TokenType.INTENT_SHOW,
    "quelles":    TokenType.INTENT_SHOW,
    "quel":       TokenType.INTENT_SHOW,
    "quelle":     TokenType.INTENT_SHOW,
    "trouver":    TokenType.INTENT_SHOW,
    "obtenir":    TokenType.INTENT_SHOW,
    # ── INTENT_COUNT
    "combien":    TokenType.INTENT_COUNT,
    "compte":     TokenType.INTENT_COUNT,
    "compter":    TokenType.INTENT_COUNT,
    # ── INTENT_AVG
    "moyenne":    TokenType.INTENT_AVG,
    # ── ENTITY names
    "capteurs":   TokenType.ENTITY,
    "capteur":    TokenType.ENTITY,
    "interventions": TokenType.ENTITY,
    "intervention":  TokenType.ENTITY,
    "citoyens":   TokenType.ENTITY,
    "citoyen":    TokenType.ENTITY,
    "véhicules":  TokenType.ENTITY,
    "vehicules":  TokenType.ENTITY,
    "véhicule":   TokenType.ENTITY,
    "vehicule":   TokenType.ENTITY,
    "mesures":    TokenType.ENTITY,
    "mesure":     TokenType.ENTITY,
    "zones":      TokenType.ENTITY,
    "zone":       TokenType.ENTITY,
    "trajets":    TokenType.ENTITY,
    "trajet":     TokenType.ENTITY,
    "techniciens":  TokenType.ENTITY,
    "technicien":   TokenType.ENTITY,
    # ── Attributes
    "statut":     TokenType.ATTRIBUTE,
    "état":       TokenType.ATTRIBUTE,
    "etat":       TokenType.ATTRIBUTE,
    "pm25":       TokenType.ATTRIBUTE,
    "pm10":       TokenType.ATTRIBUTE,
    "température": TokenType.ATTRIBUTE,
    "temperature": TokenType.ATTRIBUTE,
    "humidité":   TokenType.ATTRIBUTE,
    "humidite":   TokenType.ATTRIBUTE,
    "co2":        TokenType.ATTRIBUTE,
    "no2":        TokenType.ATTRIBUTE,
    "pollution":  TokenType.ATTRIBUTE,  # alias → pm25
    "score":      TokenType.ATTRIBUTE,
    "score_ecolo": TokenType.ATTRIBUTE,
    "nom":        TokenType.ATTRIBUTE,
    "type":       TokenType.ATTRIBUTE,
    "date":       TokenType.ATTRIBUTE,
    "priorité":   TokenType.ATTRIBUTE,
    "priorite":   TokenType.ATTRIBUTE,
    "immatriculation": TokenType.ATTRIBUTE,
    "trajet_id":  TokenType.ATTRIBUTE,
    "economie_co2": TokenType.ATTRIBUTE,
    "économie_co2": TokenType.ATTRIBUTE,
    "distance":   TokenType.ATTRIBUTE,
    "bruit":      TokenType.ATTRIBUTE,
    "trafic":     TokenType.ATTRIBUTE,
    # ── WHERE
    "où":         TokenType.KW_WHERE,
    "ou":         TokenType.KW_WHERE,   # context-dependent, checked in parser
    "avec":       TokenType.KW_WHERE,
    "dont":       TokenType.KW_WHERE,
    "ayant":      TokenType.KW_WHERE,
    "ont":        TokenType.KW_WHERE,   # "quels X ont Y > Z"
    "a":          TokenType.KW_WHERE,   # "quel X a Y > Z"
    # ── GROUPBY
    "par":        TokenType.KW_GROUPBY,
    "selon":      TokenType.KW_GROUPBY,
    # ── ORDER
    "croissant":  TokenType.KW_ORDER_ASC,
    "décroissant": TokenType.KW_ORDER_DESC,
    "decroissant": TokenType.KW_ORDER_DESC,
    # ── COMPARATORS
    "égal":       TokenType.CMP_EQ,
    "egal":       TokenType.CMP_EQ,
    "est":        TokenType.CMP_EQ,
    "vaut":       TokenType.CMP_EQ,
    "supérieur":  TokenType.CMP_GT,
    "superieur":  TokenType.CMP_GT,
    "dépasse":    TokenType.CMP_GT,
    "depasse":    TokenType.CMP_GT,
    "inférieur":  TokenType.CMP_LT,
    "inferieur":  TokenType.CMP_LT,
    "sous":       TokenType.CMP_LT,
    # ── LOGICAL
    "et":         TokenType.KW_AND,
    # ── MISC stop words (swallowed by lexer, never emitted)
}

STOP_WORDS = {
    # Articles / determiners
    "les", "des", "le", "la", "l", "un", "une", "de", "du",
    # Prepositions
    "dans", "à", "au", "aux", "sur", "en",
    # Pronouns
    "me", "moi", "je", "tu", "il", "nous", "vous", "ils", "se",
    "qui", "que", "quoi", "ce", "ces", "cet", "cette",
    # Quantity words (context-free)
    "tous", "toutes", "tout", "toute", "seuls", "seul",
    "très", "tres", "assez", "trop", "peu",
    # Punctuation
    "?", "!", ".", ",", ";", ":", "-", "_",
    # Connectors / auxiliary verbs without semantic value
    "avoir", "être", "sont",
    # Compound status prefixes handled as string literals when after comparators
    "hors", "service",
    # misc
    "plus",  # "du plus" is caught as a phrase; standalone "plus" is noise
    # Post-apostrophe split fragments
    "d", "l", "j", "n", "m", "s", "y",
    # Noise words that appear in common query phrases
    "cours", "actuellement", "présentement",
}

# Entity name → canonical SQL table name
ENTITY_TABLE_MAP: dict[str, str] = {
    "capteur":      "capteurs",
    "capteurs":     "capteurs",
    "intervention": "interventions",
    "interventions":"interventions",
    "citoyen":      "citoyens",
    "citoyens":     "citoyens",
    "vehicule":     "vehicules",
    "vehicules":    "vehicules",
    "véhicule":     "vehicules",
    "véhicules":    "vehicules",
    "mesure":       "mesures",
    "mesures":      "mesures",
    "zone":         "zones",
    "zones":        "zones",
    "trajet":       "trajets",
    "trajets":      "trajets",
    "technicien":   "techniciens",
    "techniciens":  "techniciens",
}

# Attribute alias → canonical column name in its table
ATTRIBUTE_COLUMN_MAP: dict[str, str] = {
    "état":       "statut",
    "etat":       "statut",
    "pollution":  "pm25",
    "température": "temperature",
    "humidité":   "humidite",
    "priorité":   "priorite",
    "économie_co2": "economie_co2",
    "score":      "score_ecolo",
}

# Table → available columns
SCHEMA_REGISTRY: dict[str, list[str]] = {
    "capteurs":     ["id", "nom", "type", "zone_id", "statut", "date_installation",
                     "fabricant", "modele", "latitude", "longitude"],
    "mesures":      ["id", "capteur_id", "mesure_at", "pm25", "pm10", "temperature",
                     "humidite", "co2", "no2", "niveau_bruit", "indice_trafic"],
    "interventions":["id", "capteur_id", "tech1_id", "tech2_id", "statut",
                     "description", "priorite", "created_at", "completed_at"],
    "citoyens":     ["id", "nom", "prenom", "email", "telephone", "zone_id",
                     "score_ecolo", "date_inscription"],
    "vehicules":    ["id", "immatriculation", "type", "zone_id", "statut",
                     "conducteur", "autonome"],
    "zones":        ["id", "nom", "description", "geom_lat", "geom_lon", "superficie"],
    "trajets":      ["id", "vehicule_id", "zone_depart_id", "zone_arrivee_id",
                     "distance_km", "economie_co2", "duree_minutes", "date_trajet"],
    "techniciens":  ["id", "nom", "prenom", "specialite", "telephone", "disponible"],
}
