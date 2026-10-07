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

genai.configure(api_key=GEMINI_API_KEY)


def manda_messaggio_telegram(testo):
  url = f"https://api.telegram.com/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown"}
  try:
    response = requests.post(url, json=payload)
    print(f"Risposta invio Telegram: {response.status_code}")
  except Exception as e:
    print(f"Errore nell'invio del messaggio Telegram: {e}")


# --- LOGICA DEL BOT VINTED CON TEST INIZIALE ---
def cerca_affari():
  print("Bot avviato in background...")
  time.sleep(3)

  # TEST IMMEDIATO SU TELEGRAM
  print("Invio messaggio di test su Telegram...")
  manda_messaggio_telegram(
      "🧪 **TEST RIUSCITO!**\nIl bot Vinted su Render è collegato"
      " correttamente a Telegram!"
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
      "Accept": (
          "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
      ),
      "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
      "Accept-Encoding": "gzip, deflate, br",
      "Connection": "keep-alive",
  }

  try:
    session.get("https://www.vinted.it", headers=headers, timeout=10)
  except Exception as e:
    print(f"Impossibile connettersi alla home di Vinted: {e}")

  while True:
    for item in ricerche:
      query = item["query"]
      prezzo_max = item["prezzo_max"]

      url = f"https://www.vinted.it/api/v2/catalog/items?search_text={query}&price_to={prezzo_max}&order=newest_first"

      try:
        headers["Referer"] = f"https://www.vinted.it/catalog?search_text={query}"
        response = session.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
          data = response.json()
          items = data.get("items", [])
          print(
              f"Ricerca '{query}': trovati {len(items)} articoli senza errori."
          )

          for p in items[:2]:
            titolo = p.get("title")
            prezzo = p.get("price")
            valuta = p.get("currency", "€")
            print(f"-> Trovato: {titolo} a {prezzo} {valuta}")
        else:
          print(f"Risposta Vinted per '{query}': {response.status_code}")

      except Exception as e:
        print(f"Errore durante lo scraping di '{query}': {e}")

      time.sleep(45)

    time.sleep(300)


# --- AVVIO AUTOMATICO DEL THREAD ---
bot_thread = threading.Thread(target=cerca_affari, daemon=True)
bot_thread.start()
