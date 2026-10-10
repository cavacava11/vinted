import os
import threading
import time
import google.generativeai as genai
from flask import Flask
import requests

# --- CONFIGURAZIONE FLASK ---
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
    titolo, prezzo, target_vetrina, like, offerte, spedizione, url_annuncio
):
  if not GEMINI_API_KEY:
    return "Gemini API Key non configurata."

  prompt = f"""
    Analizza questo articolo appena caricato su Vinted per reselling streetwear/vintage:
    - Articolo: {titolo}
    - Prezzo d'acquisto: {prezzo}€
    - Spedizione + Commissioni stimate: {spedizione}€
    - Target stimato di rivendita in vetrina: {target_vetrina}€
    - Like attuali: {like}
    - Offerte già ricevute: {offerte}

    Istruzioni di calcolo e filtro:
    1. Calcola il Costo Totale = {prezzo} + {spedizione}.
    2. Calcola il Profitto Netto = {target_vetrina} - Costo Totale.
    3. Calcola la ROI % = (Profitto Netto / Costo Totale) * 100.
    
    CRITERIO NOTIFICA:
    - Se la ROI % è INFERIORE al 100%, rispondi ESATTAMENTE con la parola: NO_NOTIFICA
    - Se la ROI % è PARI O SUPERIORE al 100%, fornisci un'analisi sintetica strutturata così:
      🔥 **AFFARE IDENTIFICATO!**
      - **Articolo**: {titolo}
      - **Costo Totale**: [Costo Totale]€ (Prezzo: {prezzo}€ + Sped: {spedizione}€)
      - **Stima Rivendita**: {target_vetrina}€
      - **Profitto Netto**: [Profitto Netto]€
      - **ROI Stimata**: [ROI]%
      - **Interesse**: {like} Like | {offerte} Offerte
      - **Perché comprarlo**: [Spiega in 2 frasi la nicchia, il trend (es. Y2K, Blokecore, Center Swoosh) e la facilità di rivendita basandoti sul valore di mercato attuale]
      - **Link**: {url_annuncio}
    """

  try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()
  except Exception as e:
    return f"Errore analisi Gemini: {e}"


# --- LOGICA DEL BOT VINTED ---
def cerca_affari():
  print("Bot avviato con filtri aggiornati (Migliori annunci recenti)...")
  time.sleep(3)

  manda_messaggio_telegram(
      "🚀 *Bot Vinted Arbitrage Operativo!*\n"
      "• Ricerche sui *Più Recenti* (`newest_first`)\n"
      "• Prezzi: Nike/Jordan/Tech fino a *12€* | Vintage/Tracktop fino a *8€*\n"
      "• Criterio Notifica: Solo ROI >= *100% Netto*"
  )

  ricerche = [
      # Categoria High-Tier (Max 12€)
      {"query": "nike tech fleece", "prezzo_max": 12, "target_vetrina": 45},
      {"query": "nike center swoosh", "prezzo_max": 12, "target_vetrina": 35},
      {"query": "jordan hoodie", "prezzo_max": 12, "target_vetrina": 35},
      {"query": "felpa nike", "prezzo_max": 12, "target_vetrina": 30},
      # Categoria Vintage & Maranza / Y2K (Max 8€)
      {"query": "felpa adidas", "prezzo_max": 8, "target_vetrina": 25},
      {"query": "felpa vintage", "prezzo_max": 8, "target_vetrina": 28},
      {"query": "giacca a vento nike", "prezzo_max": 8, "target_vetrina": 30},
      {"query": "windbreaker vintage", "prezzo_max": 8, "target_vetrina": 28},
      {"query": "tracktop adidas", "prezzo_max": 8, "target_vetrina": 30},
      {"query": "giacca tuta adidas", "prezzo_max": 8, "target_vetrina": 28},
      {"query": "giacca acetata", "prezzo_max": 8, "target_vetrina": 25},
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

      # URL ordinato per I PIÙ RECENTI (order=newest_first)
      url = f"https://www.vinted.it/catalog?search_text={query}&price_to={prezzo_max}&currency=EUR&order=newest_first"

      try:
        response = session.get(url, headers=headers, timeout=10)
        print(
            f"Controllo recenti '{query}' (max {prezzo_max}€): stato HTTP"
            f" {response.status_code}"
        )

        # Inserire qui la logica di parsing dell'HTML/JSON dell'annuncio
        # Quando un annuncio viene estratto, invialo a Gemini:
        # risultato = analizza_con_gemini(titolo, prezzo, target_vetrina, like, offerte, 4.0, url_annuncio)
        # if "NO_NOTIFICA" not in risultato:
        #     manda_messaggio_telegram(risultato)

      except Exception as e:
        print(f"Errore durante la richiesta per '{query}': {e}")

      time.sleep(30)

    time.sleep(90)


bot_thread = threading.Thread(target=cerca_affari, daemon=True)
bot_thread.start()
