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
  payload = {
      "chat_id": chat,
      "text": testo,
      "parse_mode": "Markdown",
      "disable_web_page_preview": False,
  }

  try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"Risposta invio Telegram: {response.status_code}")
  except Exception as e:
    print(f"Errore nell'invio del messaggio Telegram: {e}")


def analizza_con_gemini(
    titolo, prezzo, target_vetrina, like, spedizione, url_annuncio
):
  if not GEMINI_API_KEY:
    return "Gemini API Key non configurata."

  prompt = f"""
    Analizza questo articolo appena caricato su Vinted per reselling streetwear/vintage:
    - Articolo: {titolo}
    - Prezzo d'acquisto: {prezzo}€
    - Spedizione + Commissioni stimate: {spedizione}€
    - Target stimato di rivendita in vetrina: {target_vetrina}€
    - Like / Preferiti attuali: {like}

    Istruzioni di calcolo e filtro:
    1. Calcola il Costo Totale = {prezzo} + {spedizione}.
    2. Calcola il Profitto Netto = {target_vetrina} - Costo Totale.
    3. Calcola la ROI % = (Profitto Netto / Costo Totale) * 100.
    
    CRITERIO NOTIFICA:
    - Se la ROI % è INFERIORE al 100%, rispondi ESATTAMENTE con la parola: NO_NOTIFICA
    - Se la ROI % è PARI O SUPERIORE al 100%, fornisci un'analisi sintetica strutturata esattamente così:
      🔥 **AFFARE IDENTIFICATO!**
      - **Articolo**: {titolo}
      - **Prezzo d'Acquisto**: {prezzo}€ (+ {spedizione}€ sped/comm)
      - **Target Rivendita**: {target_vetrina}€
      - **ROI Stimata**: [ROI]% (Profitto Netto: [Profitto Netto]€)
      - **Social Proof**: {like} Like
      - **Perché comprarlo**: [Spiega in 2 frasi il valore di mercato, la nicchia (es. Y2K, Center Swoosh, Blokecore, Maranza) e la velocità di rivendita]
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
  print("Bot avviato con API Vinted e filtri ROI...")
  time.sleep(3)

  manda_messaggio_telegram(
      "🚀 *Bot Vinted Arbitrage Operativo!*\n"
      "• Monitoraggio in tempo reale (`newest_first`)\n"
      "• Filtro Notifica: Solo articoli con *ROI >= 100% Netto*\n"
      "• Analisi trend e social proof inclusa."
  )

  ricerche = [
      # High-Tier (Max 12€)
      {"query": "nike tech fleece", "prezzo_max": 12, "target_vetrina": 45},
      {"query": "nike center swoosh", "prezzo_max": 12, "target_vetrina": 35},
      {"query": "jordan hoodie", "prezzo_max": 12, "target_vetrina": 35},
      {"query": "felpa nike", "prezzo_max": 12, "target_vetrina": 30},
      # Vintage & Tracktop / Maranza (Max 8€)
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
      "Accept": "application/json, text/plain, */*",
      "Accept-Language": "it-IT,it;q=0.9",
  }

  articoli_visti = set()

  # Inizializza i cookie visitando la home page di Vinted
  try:
    session.get("https://www.vinted.it", headers=headers, timeout=10)
  except Exception as e:
    print(f"Errore inizializzazione sessione Vinted: {e}")

  while True:
    for item in ricerche:
      query = item["query"]
      prezzo_max = item["prezzo_max"]
      target_vetrina = item["target_vetrina"]

      # API endpoint per ricerca articoli ordinati per più recenti
      api_url = f"https://www.vinted.it/api/v2/catalog/items?search_text={query}&price_to={prezzo_max}&currency=EUR&order=newest_first&per_page=10"

      try:
        res = session.get(api_url, headers=headers, timeout=10)

        # Se i cookie sono scaduti, li rigeneriamo
        if res.status_code in [401, 403]:
          session.get("https://www.vinted.it", headers=headers, timeout=10)
          res = session.get(api_url, headers=headers, timeout=10)

        if res.status_code == 200:
          data = res.json()
          items = data.get("items", [])

          for articolo in items:
            item_id = articolo.get("id")
            if item_id in articoli_visti:
              continue

            articoli_visti.add(item_id)

            # Estrazione Dati Articolo
            titolo = articolo.get("title", "Senza titolo")
            prezzo_str = articolo.get("price", "0")
            prezzo = float(prezzo_str) if prezzo_str else 0.0
            like = articolo.get("favourite_count", 0)
            url_annuncio = articolo.get("url", "")

            # Costo indicativo di spedizione + commissioni Vinted
            spedizione_stima = 4.0

            # Analisi con Gemini
            risultato = analizza_con_gemini(
                titolo=titolo,
                prezzo=prezzo,
                target_vetrina=target_vetrina,
                like=like,
                spedizione=spedizione_stima,
                url_annuncio=url_annuncio,
            )

            # Invia la notifica solo se passa il filtro ROI
            if "NO_NOTIFICA" not in risultato and risultato.strip():
              manda_messaggio_telegram(risultato)

        else:
          print(
              f"Ricerca '{query}': Stato {res.status_code} (possibile limit"
              " temporaneo)"
          )

      except Exception as e:
        print(f"Errore durante l'estrazione per '{query}': {e}")

      time.sleep(15)

    # Pausa tra i cicli di ricerca
    time.sleep(60)


bot_thread = threading.Thread(target=cerca_affari, daemon=True)
bot_thread.start()
