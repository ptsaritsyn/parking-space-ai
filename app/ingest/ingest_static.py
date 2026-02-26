import json
import os

from app.core.schemas import StaticParkingInfo


STATIC_DATA_PATH = os.path.join(os.path.dirname(__file__), "static_data.json")


def load_static_data():
    """Load and validate static parking data from JSON file."""
    with open(STATIC_DATA_PATH, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    validated = [StaticParkingInfo(**item).dict() for item in raw_data]
    return validated


def ingest_static_data(vector_db):
    """
    Insert static parking data into the vector database if not already present.
    """
    data = load_static_data()
    vector_db.add_documents(data)
