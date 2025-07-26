from openai import OpenAI
import random
import re
import time

client = OpenAI(
    base_url="https://api.featherless.ai/v1",
    api_key="rc_8cc0189a514371eebd0eb719863d70fddf251ee4e857c8edd51e506e9f729dcb"
)

def verzögerung(text):
    delay = random.uniform(1.5, 3) + len(text) * 0.03
    time.sleep(min(delay, 7))

def finde_trigger_antwort(text, trigger_daten):
    text = text.lower()
    for k, v in trigger_daten.items():
        for trigger in v['trigger']:
            if re.search(r'\b' + re.escape(trigger) + r'\b', text):
                beste = max(v['antworten'], key=lambda x: x['score'])
                return beste['text']
    return None

def ki_antwort(system_prompt_basis, anzeige_titel, chat_history):
    messages = [
        {"role": "system", "content": system_prompt_basis},
        {"role": "system", "content": f"Aktuelles Angebot: {anzeige_titel}"},
    ] + chat_history[-50:]
    try:
        response = client.chat.completions.create(
            model="Orenguteng/Llama-3-8B-Lexi-Uncensored",
            messages=messages,
            temperature=0.7,
            top_p=0.9,
        )
        return response.model_dump()['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Fehler bei OpenAI-Antwort: {e}")
        return "Tut mir leid, ich kann gerade nicht antworten."
        return "Tut mir leid, ich kann gerade nicht antworten."
        return "Tut mir leid, ich kann gerade nicht antworten."
        raise ValueError("Keine choices im Response")
        message = choices[0].message.content.strip()
        return message
    except Exception as e:
        logging.error(f"Fehler bei OpenAI-Antwort: {e}")
        return "Tut mir leid, ich kann gerade nicht antworten."
        return "Tut mir leid, ich kann gerade nicht antworten."
