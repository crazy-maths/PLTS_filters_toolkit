import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATA_DIR = os.path.join(BASE_DIR, "data")
JSON_DIR = os.path.join(DATA_DIR, "json_files")

PATHS = {
    "config": os.path.join(JSON_DIR, "config.json"),
    "lattices": os.path.join(JSON_DIR, "lattices.json"),
    "models": os.path.join(JSON_DIR, "models.json"),
    "twist_structures": os.path.join(JSON_DIR, "twist_structures.json"),
    "worlds": os.path.join(JSON_DIR, "worlds.json"),
    "assets": os.path.join(DATA_DIR, "assets"),
    "lattice_filters": os.path.join(JSON_DIR, "lattice_filters.json"),
    "twist_filters": os.path.join(JSON_DIR, "twist_filters.json"),
    "filtered_models": os.path.join(JSON_DIR, "filtered_models.json"),
    "morphisms": os.path.join(JSON_DIR, "morphisms.json")
}