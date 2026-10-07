import os
import threading
import time
import google.generativeai as genai
from flask import Flask
import requests

# --- CONFIGURAZIONE FLASK (Pinger per Render 24/7) ---
app = Flask(__name__)


@app.route("/")
def home():
  return "Il bot Vinted è attivo e operativo 24/7!"


def run_flask():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# --- CONFIGURAZIONE CHIAVI E API ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


def manda_messaggio_telegram(testo):
  url = f"https://api.telegram.com/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": testo, "parse_mode": "Markdown"}
  try:
    requests.post(url, json=payload)
  except Exception as e:
    print(f"Errore nell'invio del messaggio Telegram: {e}")


# --- LOGICA DEL BOT VINTED ---
def cerca_affari():
  print("Avvio ricerca automatica Vinted...")
  manda_messaggio_telegram(
      "🚀 Bot Vinted avviato e a caccia di affari su Render!"
  )

  # Configurazione ricerche (puoi personalizzare termini e prezzi massimi)
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

          # Prendiamo gli ultimi 3 articoli trovati
          for p in items[:3]:
            titolo = p.get("title")
            prezzo = p.get("price")
            valuta = p.get("currency", "€")
            link = f"https://www.vinted.it{p.get('url')}"
            foto_url = (
                p.get("photos", [{}])[0].get("full_size_url")
                if p.get("photos")
                else None
            )

            # Esempio di validazione rapida con Gemini se necessario o invio diretto
            messaggio = (
                f"🔥 **Nuovo affare trovato!**\n\n"
                f"👕 **Oggetto:** {titolo}\n"
                f"💰 **Prezzo:** {prezzo} {valuta}\n"
                f"🔍 **Ricerca:** {query}\n\n"
                f"[🔗 Apri su Vinted]({link})"
            )

            # Qui potresti aggiungere un controllo per non inviare doppioni,
            # per ora inviamo la notifica di test/monitoraggio
            print(f"Trovato: {titolo} a {prezzo} {valuta}")

        else:
          print(
              f"Errore nella richiesta Vinted per '{query}':"
              f" {response.status_code}"
          )

      except Exception as e:
        print(f"Errore durante lo scraping di '{query}': {e}")

      # Pausa tra una ricerca e l'altra per evitare blocchi IP
      time.sleep(30)

    # Pausa principale prima del prossimo ciclo completo
    time.sleep(300)


# --- AVVIO CONTENITORI ---
if __name__ == "__main__":
  # Facciamo partire Flask in un thread separato così non blocca il bot
  t = threading.Thread(target=run_flask)
  t.daemon = True
  t.start()

  # Avviamo il ciclo principale del bot
  cerca_affari()
