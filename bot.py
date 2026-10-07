import os
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


# --- AVVIO STANDARD PER FLASK (Usato da Gunicorn) ---
if __name__ == "__main__":
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)
