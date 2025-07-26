import time
import re
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bot.ki_handler import finde_trigger_antwort, ki_antwort, verzögerung
from bot.session_manager import lade_sessions, speichere_sessions
from bot.config import WAIT_BETWEEN_CHECKS

def check_payment_status(chat_history, payment_triggers, telegram_name="hotwithmelina"):
    bezahlt = False
    unsicher = False

    kaufbestaetigung_phrases = payment_triggers.get("kaufbestaetigung", [])
    telegram_phrases = payment_triggers.get("telegram_fragen", [])
    zahlungscode_regex = re.compile(payment_triggers.get("zahlungscode_regex", ""), re.IGNORECASE)

    for msg in chat_history:
        text = msg['content'].strip()
        text_lower = text.lower()

        if "drive.google.com/drive/folders" in text_lower:
            print(f"Zahlungs-Indikator gefunden (Google Drive Link): {text}")
            bezahlt = True

        if zahlungscode_regex.match(text):
            print(f"Zahlungs-Indikator gefunden (Gutschein-Code): {text}")
            bezahlt = True

        if telegram_name.lower() in text_lower and msg['role'] == 'assistant':
            print(f"Telegramname im Assistant-Text gefunden: {text}")
            unsicher = True

        if msg['role'] == 'user':
            if any(phrase in text_lower for phrase in telegram_phrases):
                if '?' in text_lower or text_lower.strip().endswith("?"):
                    print(f"User fragt nach Telegram oder Name: {text}")
                    unsicher = True

            if len(text) < 150:
                if any(phrase in text_lower for phrase in kaufbestaetigung_phrases):
                    print(f"User bestätigt Kauf mit: {text}")
                    bezahlt = True
                    unsicher = False
                    break

    print(f"check_payment_status Ergebnis: bezahlt={bezahlt}, unsicher={unsicher}")
    if bezahlt:
        return "bezahlt"
    elif unsicher:
        return "unsicher"
    else:
        return "unbezahlt"


def safe_find_elements(driver, selector, retries=3):
    for attempt in range(retries):
        try:
            return driver.find_elements(By.CSS_SELECTOR, selector)
        except StaleElementReferenceException:
            time.sleep(0.5)
    return []


def ist_melina_nachricht(elem):
    bg = elem.value_of_css_property("background-color")
    return bg == "rgba(129, 189, 221, 1)"  # hellblau #81BDDD


def ist_kunden_nachricht(elem):
    bg = elem.value_of_css_property("background-color")
    return bg == "rgba(180, 180, 179, 1)"  # hellgrau #B4B4B3


def filter_bmp(text):
    # Entfernt Zeichen außerhalb der Basic Multilingual Plane, die ChromeDriver Probleme bereiten
    return ''.join(c for c in text if ord(c) <= 0xFFFF)


def bearbeite_chat(chat, driver, wait, trigger_daten, sessions, system_prompt_basis, payment_triggers):
    try:
        inner = chat.find_element(By.CSS_SELECTOR, "div.clsy-c-mbx-threads-item__inner")
        title = chat.find_element(By.CSS_SELECTOR, "h2.clsy-c-mbx-threads-item__title").text
        nickname = chat.find_element(By.CSS_SELECTOR, "h3.clsy-c-mbx-threads-item__nickname").text
    except Exception:
        return

    # Neue Struktur: sessions[title]["users"][nickname]
    if title not in sessions:
        sessions[title] = {"users": {}}
    if nickname not in sessions[title]["users"]:
        sessions[title]["users"][nickname] = {"history": [], "bezahlt": False, "status": "unbezahlt"}

    user_session = sessions[title]["users"][nickname]

    # Speichere Titel und Nickname explizit in der Session
    user_session["title"] = title
    user_session["nickname"] = nickname

    speichere_sessions(sessions)  # Hier speichern vor dem Öffnen

    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", inner)
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.clsy-c-mbx-threads-item__inner")))
        time.sleep(1)
        inner.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.clsy-c-mbx-chat-message__content")))
        time.sleep(2)
    except Exception:
        return

    nachrichten = safe_find_elements(driver, "div.clsy-c-mbx-chat-message__content")
    chat_history = user_session["history"]
    chat_history.clear()

    letztes_datum = None

    for elem in nachrichten:
        text = elem.text.strip()
        try:
            datum_elem = elem.find_element(By.CSS_SELECTOR, "span.clsy-c-mbx-chat-message__date")
            datum_text = datum_elem.text.strip()
            letztes_datum = datum_text
        except Exception:
            pass

        if ist_melina_nachricht(elem):
            rolle = "assistant"
        elif ist_kunden_nachricht(elem):
            rolle = "user"
        else:
            continue

        chat_history.append({"role": rolle, "content": text})

    # zuletzt gefundenes Datum speichern, wenn vorhanden
    if letztes_datum:
        user_session["last_message_time"] = letztes_datum
    else:
        user_session["last_message_time"] = "Unbekannt"

    # === Zahlungsstatus prüfen und speichern ===
    status = check_payment_status(chat_history, payment_triggers)

    user_session["bezahlt"] = (status == "bezahlt")
    user_session["status"] = status
    user_session["history"] = chat_history

    speichere_sessions(sessions)

    if not chat_history:
        driver.back()
        time.sleep(2)
        return

    letzte_rolle = chat_history[-1]["role"]
    letzte_nachricht_text = chat_history[-1]["content"]

    if letzte_rolle == "assistant":
        driver.back()
        time.sleep(2)
        return

    trigger_antwort = finde_trigger_antwort(letzte_nachricht_text, trigger_daten)

    # === Antwortlogik je nach Zahlungsstatus ===
    if trigger_antwort:
        antwort_text = trigger_antwort
    else:
        if status == "bezahlt":
            antwort_text = ki_antwort(system_prompt_basis, title, chat_history)
        elif status == "unsicher":
            antwort_text = "Ich sehe, du hast nach meinem Telegramnamen gefragt. Hast du schon einmal bei mir gekauft? 😊"
        else:  # unbezahlt
            if (("link" in letzte_nachricht_text.lower() or
                 "video" in letzte_nachricht_text.lower() or
                 "sexchat" in letzte_nachricht_text.lower())):
                antwort_text = "Den Link / Chat schicke ich dir gern, sobald die Zahlung bei mir eingegangen ist. Danke für dein Verständnis, baby! 😊💕"
            else:
                antwort_text = ki_antwort(system_prompt_basis, title, chat_history)

    verzögerung(antwort_text)

    print("\n=== AKTUELLER CHATVERLAUF ===")
    for msg in chat_history:
        print(f"{msg['role'].capitalize()}: {msg['content']}")
    print("=============================\n")

    print("\n=== MELINA ANTWORT ===")
    print(antwort_text)
    print("======================")
    senden = input("Antwort senden? (j/n) > ").strip().lower()
    if senden != "j":
        print("Antwort nicht gesendet, Chat wird geschlossen...")
        driver.back()
        time.sleep(2)
        return

    try:
        input_field = driver.find_element(By.CSS_SELECTOR, "textarea.clsy-c-form__expanding-textarea")
        input_field.click()
        saubere_antwort = filter_bmp(antwort_text)
        input_field.send_keys(saubere_antwort)
        input_field.send_keys(Keys.SHIFT, Keys.ENTER)
        chat_history.append({"role": "assistant", "content": antwort_text})
        speichere_sessions(sessions)
    except Exception:
        driver.back()
        time.sleep(2)
        return

    time.sleep(2)

    driver.back()
    time.sleep(2)
