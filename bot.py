import os
import time
import requests
from flask import Flask
import google.generativeai as genai

# Configurazione Flask per mantenere il bot attivo sul piano gratuito di Render
app = Flask(__name__)


@app.route("/")
def home():
  return "Il bot Vinted è attivo e operativo 24/7!"


# Recupero delle chiavi dalle variabili d'ambiente di Render
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Configurazione di Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def manda_messaggio_telegram(testo):
  url = f"https://api.telegram.com/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload)
  except Exception as e:
    print(f"Errore nell'invio del messaggio Telegram: {e}")


def avvia_bot():
  print("Bot avviato con successo!")
  # Qui inserisci la logica principale del tuo scraper Vinted
  # Esempio di test all'avvio:
  # manda_messaggio_telegram("🚀 Bot Vinted avviato correttamente su Render!")


if __name__ == "__main__":
  # Avviamo il bot in background o eseguiamo la logica
  # Per sicurezza su Render, facciamo partire Flask sulla porta 10000
  port = int(os.environ.get("PORT", 10000))

  # Nota: per far girare Flask e il bot insieme senza bloccare la porta,
  # di solito si usa un thread, oppure per iniziare testiamo che il server parta.
  app.run(host="0.0.0.0", port=port)
