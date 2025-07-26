import os
import openai

BASE_DIR = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))

CHROMEDRIVER_PATH = os.path.join(BASE_DIR, "chromedriver.exe")
FEATHERLESS_API_KEY = "rc_354d3dad61c32c81182cea17af0abf71df43ed593177e568f422d059ccbad2be"
WAIT_BETWEEN_CHECKS = 10  # Sekunden
MELINA_PROMPT_PATH = os.path.join(BASE_DIR, "melina_prompt.txt")
TRIGGER_PATH = os.path.join(BASE_DIR, "trigger_antworten.json")
SESSIONS_PATH = os.path.join(BASE_DIR, "sessions.json")
TELEGRAM_NAME = "hotwithmelina"
TELEGRAM_NAMES = ["hotwithmelina", "HotWithMelina", "@HotWithMelina", "@hotwithmelina"]

# NEU: Pfad zur Payment-Trigger JSON (jetzt korrekt relativ zum Projekt-Hauptordner)
PAYMENT_TRIGGER_PATH = os.path.join(BASE_DIR, "config", "payment_trigger.json")

# Featherless/OpenAI API global setzen
openai.api_key = FEATHERLESS_API_KEY
openai.base_url = "https://api.featherless.ai/v1/"

