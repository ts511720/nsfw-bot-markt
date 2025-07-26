import json
import logging
from bot.config import SESSIONS_PATH

def lade_sessions(pfad=SESSIONS_PATH):
    try:
        with open(pfad, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Fehler beim Laden der Sessions: {e}")
        return {}

def speichere_sessions(daten, pfad=SESSIONS_PATH):
    try:
        with open(pfad, "w", encoding="utf-8") as f:
            json.dump(daten, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Fehler beim Speichern der Sessions: {e}")
