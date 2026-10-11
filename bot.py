import os
import threading
import time
from urllib.parse import quote
import google.generativeai as genai
from flask import Flask
import requests

app = Flask(__name__)


@app.route('/')
def home():
  return 'Il bot Vinted Arbitrage è attivo e operativo 24/7!'


TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
SCRAPERAPI_KEY = os.environ.get('SCRAPERAPI_KEY')

if GEMINI_API_KEY:
  genai.configure(api_key=GEMINI_API_KEY)


def manda_messaggio_telegram(testo):
  if not TELEGRAM_TOKEN or not CHAT_ID:
    print('Telegram Token o Chat ID mancanti.', flush=True)
    return

  token = TELEGRAM_TOKEN.strip()
  chat = CHAT_ID.strip()
  url = f'https://api.telegram.org/bot{token}/sendMessage'
  payload = {
      'chat_id': chat,
      'text': testo,
      'parse_mode': 'Markdown',
      'disable_web_page_preview': False,
  }

  try:
    response = requests.post(url, json=payload, timeout=10)
    print(f'Risposta invio Telegram: {response.status_code}', flush=True)
  except Exception as e:
    print(f"Errore nell'invio del messaggio Telegram: {e}", flush=True)


def analizza_con_gemini(
    titolo, prezzo, target_vetrina, like, spedizione, url_annuncio
):
  if not GEMINI_API_KEY:
    return 'Gemini API Key non configurata.'

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
    
    CRITERIO NOTIFICA RIGIDO:
    - Se la ROI % è INFERIORE al 100%, rispondi ESATTAMENTE con la parola: NO_NOTIFICA
    - Se la ROI % è PARI O SUPERIORE al 100%, fornisci un'analisi sintetica strutturata esattamente così:
      🔥 **AFFARE IDENTIFICATO!**
      - **Articolo**: {titolo}
      - **Prezzo d'Acquisto**: {prezzo}€ (+ {spedizione}€ sped/comm)
      - **Target Rivendita**: {target_vetrina}€
      - **ROI Stimata**: [ROI]% (Profitto Netto: [Profitto Netto]€)
      - **Social Proof**: {like} Like
      - **Perché comprarlo**: [Spiega in 2 frasi il valore di mercato, la nicchia e la velocità di rivendita]
      - **Link**: {url_annuncio}
    """

  try:
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(prompt)
    return response.text.strip()
  except Exception as e:
    return f'Errore analisi Gemini: {e}'


def cerca_affari():
  print('=== INIZIO LOOP DI RICERCA CON SCRAPERAPI ===', flush=True)
  time.sleep(2)

  manda_messaggio_telegram(
      '🚀 *Bot Vinted Arbitrage Operativo!*\n'
      '• ScraperAPI attivo (Fix URL 200 OK)\n'
      '• ROI minima confermata: *>= 100% Netto*'
  )

  ricerche = [
      {'query': 'nike tech fleece', 'prezzo_max': 12, 'target_vetrina': 45},
      {'query': 'nike center swoosh', 'prezzo_max': 12, 'target_vetrina': 35},
      {'query': 'jordan hoodie', 'prezzo_max': 12, 'target_vetrina': 35},
      {'query': 'felpa nike', 'prezzo_max': 12, 'target_vetrina': 30},
      {'query': 'felpa adidas', 'prezzo_max': 8, 'target_vetrina': 25},
      {'query': 'felpa vintage', 'prezzo_max': 8, 'target_vetrina': 28},
      {'query': 'giacca a vento nike', 'prezzo_max': 8, 'target_vetrina': 30},
      {'query': 'windbreaker vintage', 'prezzo_max': 8, 'target_vetrina': 28},
      {'query': 'tracktop adidas', 'prezzo_max': 8, 'target_vetrina': 30},
      {'query': 'giacca tuta adidas', 'prezzo_max': 8, 'target_vetrina': 28},
      {'query': 'giacca acetata', 'prezzo_max': 8, 'target_vetrina': 25},
  ]

  articoli_visti = set()

  while True:
    for item in ricerche:
      query = item['query']
      prezzo_max = item['prezzo_max']
      target_vetrina = item['target_vetrina']

      # Costruzione pulita dell'URL originale Vinted
      vinted_url = f'https://www.vinted.it/api/v2/catalog/items?search_text={quote(query)}&price_to={prezzo_max}&currency=EUR&order=newest_first&per_page=10'

      # Passaggio diretto a ScraperAPI tramite parametri dictionary (previene il doppio encoding)
      if SCRAPERAPI_KEY:
        payload = {'api_key': SCRAPERAPI_KEY.strip(), 'url': vinted_url}
        api_endpoint = 'http://api.scraperapi.com'
      else:
        payload = {}
        api_endpoint = vinted_url

      print(f"--> Avvio ricerca per: '{query}'...", flush=True)

      try:
        if SCRAPERAPI_KEY:
          res = requests.get(api_endpoint, params=payload, timeout=25)
        else:
          res = requests.get(api_endpoint, timeout=25)

        if res.status_code == 200:
          data = res.json()
          items = data.get('items', [])
          print(
              f"✅ Ricerca '{query}': Trovati {len(items)} articoli.",
              flush=True,
          )

          for articolo in items:
            item_id = articolo.get('id')
            if item_id in articoli_visti:
              continue

            articoli_visti.add(item_id)

            titolo = articolo.get('title', 'Senza titolo')

            raw_price = articolo.get('price')
            if isinstance(raw_price, dict):
              prezzo = float(raw_price.get('amount', 0.0))
            elif raw_price is not None:
              prezzo = float(raw_price)
            else:
              prezzo = 0.0

            like = articolo.get('favourite_count', 0)
            url_annuncio = articolo.get('url', '')

            risultato = analizza_con_gemini(
                titolo=titolo,
                prezzo=prezzo,
                target_vetrina=target_vetrina,
                like=like,
                spedizione=4.0,
                url_annuncio=url_annuncio,
            )

            if 'NO_NOTIFICA' not in risultato and risultato.strip():
              print(
                  f'🔥 Trovata occasione ({titolo}), invio su Telegram...',
                  flush=True,
              )
              manda_messaggio_telegram(risultato)

        else:
          print(
              f"❌ Errore HTTP {res.status_code} per la query '{query}'",
              flush=True,
          )

      except Exception as e:
        print(f"⚠️ Eccezione durante la ricerca '{query}': {e}", flush=True)

      time.sleep(15)

    print('=== CICLO COMPLETATO, PAUSA DI 60 SECONDI ===', flush=True)
    time.sleep(60)


bot_thread = threading.Thread(target=cerca_affari, daemon=True)
bot_thread.start()

if __name__ == '__main__':
  port = int(os.environ.get('PORT', 10000))
  app.run(host='0.0.0.0', port=port)
