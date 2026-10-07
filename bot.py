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
    requests.post(url, json=payload)
  except Exception as e:
    print(f"Errore nell'invio del messaggio Telegram: {e}")


# --- LOGICA DEL BOT VINTED ---
def cerca_affari():
  print("Bot avviato in background, attesa connessione...")
  time.sleep(10)  # Breve attesa per stabilizzare il server
  manda_messaggio_telegram(
      "🚀 **Bot Vinted avviato con successo su Render!**\nA caccia di"
      " streetwear..."
  )

  ricerche = [
      {"query": "nike center swoosh", "prezzo_max": 35},
      {"query": "nike tech fleece", "prezzo_max": 45},
      {"query": "jordan hoodie", "prezzo_max": 30},
  ]

  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/120.0.0.0 Safari/537.36"
      ),
      "Accept-Language": "it-IT,it;q=0.9",
  }

  while True:
    for item in ricerche:
      query = item["query"]
      prezzo_max = item["prezzo_max"]

      url = f"https://www.vinted.it/api/v2/catalog/items?search_text={query}&price_to={prezzo_max}&order=newest_first"

      try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
          data = response.json()
          items = data.get("items", [])

          for p in items[:2]:
            titolo = p.get("title")
            prezzo = p.get("price")
            valuta = p.get("currency", "€")
            link = f"https://www.vinted.it{p.get('url')}"

            print(f"Trovato: {titolo} a {prezzo} {valuta}")
        else:
          print(f"Risposta Vinted per '{query}': {response.status_code}")

      except Exception as e:
        print(f"Errore durante lo scraping di '{query}': {e}")

      time.sleep(45)

    time.sleep(300)


# --- AVVIO DEL THREAD DEL BOT ---
# Fa partire il bot in background non appena lo script viene caricato
bot_thread = threading.Thread(target=cerca_affari, daemon=True)
bot_thread.start()

if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
