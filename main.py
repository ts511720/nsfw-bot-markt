import logging
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from bot.config import CHROMEDRIVER_PATH, WAIT_BETWEEN_CHECKS, MELINA_PROMPT_PATH, TRIGGER_PATH, PAYMENT_TRIGGER_PATH
from bot.selenium_handler import safe_find_elements, bearbeite_chat
from bot.session_manager import lade_sessions

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

def main():
    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service)
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://www.markt.de/")
        print("Bitte logge dich manuell im Browser ein.")
        input("Wenn du fertig bist, drücke Enter hier im Terminal...")

        driver.get("https://www.markt.de/benutzer/postfach.htm")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.clsy-c-mbx-threads-list")))

        with open(MELINA_PROMPT_PATH, "r", encoding="utf-8") as f:
            system_prompt_basis = f.read()

        with open(TRIGGER_PATH, "r", encoding="utf-8") as f:
            trigger_daten = json.load(f)

        with open(PAYMENT_TRIGGER_PATH, "r", encoding="utf-8") as f:
            payment_triggers = json.load(f)

        sessions = lade_sessions()

        while True:
            chats = safe_find_elements(driver, "div.clsy-c-mbx-threads-item")
            print(f"Gefundene Chats: {len(chats)}")

            for chat in chats:
                # Hier payment_triggers an bearbeite_chat übergeben
                bearbeite_chat(chat, driver, wait, trigger_daten, sessions, system_prompt_basis, payment_triggers)

            print(f"Warte {WAIT_BETWEEN_CHECKS} Sekunden bis zum nächsten Check...")
            time.sleep(WAIT_BETWEEN_CHECKS)

    except KeyboardInterrupt:
        print("Bot wird beendet...")
    except Exception as e:
        print(f"Fehler: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
