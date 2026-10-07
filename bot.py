import os
import threading
import time
import google.generativeai as genai
from flask import Flask
import requests

# --- CONFIGURAZIONE FLASK (Server Web per Render) ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Il bot Vinted è attivo e operativo 24/7!"


# --- CONFIGURAZIONE CHIAVI E API ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
  genai.configure(api_key=GEMINI_API_KEY)


def manda_messaggio_telegram(testo):
  if not TELEGRAM_TOKEN or not CHAT_ID:
    print("Telegram Token o Chat ID mancanti.")
    return

  # Inviamo come testo semplice per evitare problemi di sintassi Markdown
  url = f"https://api.telegram.com/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": testo}
  try:
    response = requests.post(url, json=payload, timeout=10)
    print(
        f"Risposta invio Telegram: {response.status_code} -"
        f" {response.text}"
    )
  except Exception as e:
    print(f"Errore nell'invio del messaggio Telegram: {e}")


# --- LOGICA DEL BOT VINTED ---
def cerca_affari():
  print("Bot avviato in background...")
  time.sleep(3)

  # Messaggio di prova pulito senza formattazioni complesse
  manda_messaggio_telegram(
      "TEST: Bot Vinted avviato con successo su Render!"
  )

  ricerche = [
      {"query": "nike center swoosh", "prezzo_max": 35},
      {"query": "nike tech fleece", "prezzo_max": 45},
      {"query": "jordan hoodie", "prezzo_max": 30},
  ]

  session = requests.Session()
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/122.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "it-IT,it;q=0.9",
  }

  while True:
    for item in ricerche:
      query = item["query"]
      prezzo_max = item["prezzo_max"]

      # Utilizziamo l'endpoint di ricerca web/catalogo standard
      url = f"https://www.vinted.it/catalog?search_text={query}&price_to={prezzo_max}&currency=EUR"

      try:
        response = session.get(url, headers=headers, timeout=10)
        print(
            f"Controllo ricerca '{query}': stato HTTP {response.status_code}"
        )
      except Exception as e:
        print(f"Errore durante la richiesta per '{query}': {e}")

      time.sleep(45)

    time.sleep(120)


# --- AVVIO AUTOMATICO DEL THREAD PER GUNICORN ---
bot_thread = threading.Thread(target=cerca_affari, daemon=True)
bot_thread.start()
