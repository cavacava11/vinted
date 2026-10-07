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
  return "Il bot Vinted Arbitrage è attivo e operativo 24/7!"


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

  token = TELEGRAM_TOKEN.strip()
  chat = CHAT_ID.strip()
  url = f"https://api.telegram.org/bot{token}/sendMessage"
  payload = {"chat_id": chat, "text": testo, "parse_mode": "Markdown"}

  try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Risposta invio Telegram: {response.status_code}")
  except Exception as e:
    print(f"Errore nell'invio del messaggio Telegram: {e}")


def analizza_con_gemini(
    titolo, prezzo, target_vetrina, like, offerte, spedizione
):
  if not GEMINI_API_KEY:
    return "Gemini API Key non configurata."

  prompt = (
      f"Analizza questo affare di reselling streetwear su Vinted:\n"
      f"- Articolo: {titolo}\n"
      f"- Prezzo d'acquisto: {prezzo}€\n"
      f"- Spedizione minima stimata: {spedizione}€\n"
      f"- Target prezzo in vetrina: {target_vetrina}€\n"
      f"- Like ricevuti: {like}\n"
      f"- Offerte già ricevute: {offerte}\n\n"
      "Calcola il ROI effettivo considerando il costo totale (acquisto + spedizione). "
      "Fornisci un giudizio rapido (compralo subito / da valutare) e il margine di guadagno stimato. "
      "Sii sintetico, ideale per una notifica Telegram."
  )

  try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text
  except Exception as e:
    return f"Errore analisi Gemini: {e}"


# --- LOGICA DEL BOT VINTED ---
def cerca_affari():
  print("Bot avviato in background con analisi completa...")
  time.sleep(3)

  manda_messaggio_telegram(
      "🚀 *TEST: Bot Vinted Arbitrage avviato!*\nNome articolo in cima e"
      " metriche pronte."
  )

  # Ricerche con prezzo massimo di acquisto <= 12€ e target di vetrina associato
  ricerche = [
      {"query": "nike center swoosh", "prezzo_max": 12, "target_vetrina": 35},
      {"query": "nike tech fleece", "prezzo_max": 12, "target_vetrina": 45},
      {"query": "jordan hoodie", "prezzo_max": 12, "target_vetrina": 40},
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
      target_vetrina = item["target_vetrina"]

      url = f"https://www.vinted.it/catalog?search_text={query}&price_to={prezzo_max}&currency=EUR"

      try:
        response = session.get(url, headers=headers, timeout=10)
        print(
            f"Controllo ricerca '{query}' (max {prezzo_max}€): stato HTTP"
            f" {response.status_code}"
        )
      except Exception as e:
        print(f"Errore durante la richiesta per '{query}': {e}")

      time.sleep(45)

    time.sleep(120)


# --- AVVIO AUTOMATICO DEL THREAD PER GUNICORN ---
bot_thread = threading.Thread(target=cerca_affari, daemon=True)
bot_thread.start()
