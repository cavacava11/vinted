import os
import time
import random
import requests
import google.generativeai as genai
from google.colab import userdata

# ==========================================
# 1. CONFIGURAZIONE CHIAVI DA COLAB SECRETS
# ==========================================
TELEGRAM_TOKEN = userdata.get('TELEGRAM_TOKEN')
CHAT_ID = userdata.get('CHAT_ID')
GEMINI_API_KEY = userdata.get('GEMINI_API_KEY')

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# ==========================================
# 2. TARGET DI RICERCA RIGIDI (CON HEADERS ANTI-403)
# ==========================================
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

SEARCH_TARGETS = [
    {
        "category_name": "Nike Center Swoosh",
        "url": "https://www.vinted.it/catalog?search_text=center+swoosh&brand_ids[]=53&price_to=12.00&order=newest_first",
        "target_sizes": ["S", "M", "L", "XL"],
        "max_buy_price": 12.0,
        "estimated_resell": 45.0,
        "prompt_ai": (
            "Sei un esperto di reselling streetwear su Vinted. "
            "Analizza questa felpa. Vogliamo ESCLUSIVAMENTE felpe Nike con il MICRO-SWOOSH ricamato "
            "al centro esatto del petto (logo piccolissimo). "
            "DEVI RISPONDERE 'NO' SE: il logo è grande, stampato, centrale ma grosso, spostato a destra/sinistra, "
            "se è una maglia scollata/crop top/cropped, se è un modello Nike Air generico o se il capo è rovinato. "
            "Rispondi 'SI' solo se rispetta al 100% i criteri del micro center swoosh in ottime condizioni."
        )
    },
    {
        "category_name": "Jordan (Felpe)",
        "url": "https://www.vinted.it/catalog?search_text=jordan+felpa&price_to=15.00&order=newest_first",
        "target_sizes": ["S", "M", "L", "XL"],
        "max_buy_price": 15.0,
        "estimated_resell": 50.0,
        "prompt_ai": (
            "Sei un esperto di reselling streetwear. "
            "Analizza l'immagine. Rispondi 'SI' SOLO se si tratta di una FELPA con cappuccio o crewneck Jordan autentica "
            "(VIETATO: scarpe, pantaloni, t-shirt, giubbotti pesanti). "
            "Il capo deve essere in ottime condizioni, ad alta liquidità di rivendita sull'usato. Altrimenti rispondi 'NO'."
        )
    },
    {
        "category_name": "Nike Tech Fleece",
        "url": "https://www.vinted.it/catalog?search_text=nike+tech+fleece&price_to=20.00&order=newest_first",
        "target_sizes": ["S", "M", "L", "XL"],
        "max_buy_price": 20.0,
        "estimated_resell": 60.0,
        "prompt_ai": (
            "Sei un esperto di reselling streetwear. "
            "Analizza l'immagine. Rispondi 'SI' SOLO se si tratta di un capo originale Nike Tech Fleece (felpa o pantaloni tuta) "
            "riconoscibile dal tipico tessuto tecnico e tasca termosaldata, in buone condizioni e con alto valore di mercato usato. "
            "Se è un normale pile o felpa economica non tech, rispondi 'NO'."
        )
    }
]

seen_items = set()

# ==========================================
# 3. FUNZIONI DI LOGICA, TIER E FINANZA
# ==========================================

def calculate_tier(roi, size):
    size = size.upper()
    if size in ["XS", "XXS"]:
        return "Scartato (Taglia non idonea)"
    if roi >= 200 and size in ["M", "L", "XL"]:
        return "🔥 TIER 1 (Top Liquidità & Margine)"
    elif roi >= 120:
        return "⚡ TIER 2 (Ottimo Affare)"
    else:
        return "⭐ TIER 3 (Standard)"

def calculate_financials(price_buy, estimated_resell):
    profit = estimated_resell - price_buy
    roi_percent = (profit / price_buy) * 100 if price_buy > 0 else 0
    showcase_price = estimated_resell + (estimated_resell * 0.20)
    return profit, roi_percent, showcase_price

def verify_and_analyze_with_gemini(image_url, prompt_ai, title, price, likes, offers):
    analysis_prompt = (
        f"{prompt_ai}\n\n"
        f"Dati annuncio:\n- Titolo: {title}\n- Prezzo Vinted: {price}€\n- Like ricevuti: {likes}\n- Offerte: {offers}\n\n"
        f"Se la risposta iniziale è SI, scrivi nel formato esatto:\n"
        f"ESITO: SI\n"
        f"ANALISI: [Scrivi un commento analitico di massimo 2-3 righe che spieghi perché questo capo usato ha alta liquidità e conviene prenderlo per rivenderlo su Vinted]."
    )
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response_img = requests.get(image_url, headers=REQUEST_HEADERS, timeout=10)
            if response_img.status_code == 200:
                img_data = response_img.content
                response = model.generate_content([
                    analysis_prompt,
                    {"mime_type": "image/jpeg", "data": img_data}
                ])
                full_text = response.text.strip()
                is_valid = "ESITO: SI" in full_text.upper() or "SI" in full_text.upper()[:10]
                
                comment = full_text.replace("ESITO: SI", "").replace("ESITO: NO", "").replace("SI", "", 1).strip()
                if not comment:
                    comment = "Capo selezionato per ottima richiesta sul mercato dell'usato e margini di guadagno stimati molto alti."
                return is_valid, comment
        except Exception as e:
            print(f"⚠️ Tentativo {attempt + 1} fallito (Gemini/Rete): {e}")
            time.sleep(5)
            
    return False, "Analisi non disponibile per errore temporaneo."

def send_telegram_alert(category, title, price, size, item_url, photo_url, profit, roi, showcase_price, likes, offers, tier, analysis_comment):
    caption = (
        f"🔥 *BAGF — NUOVO AFFARONE RILEVATO!*\n"
        f"🏷️ *Categoria:* {category}\n"
        f"🏆 *Priorità:* {tier}\n\n"
        f"📌 *Prodotto:* {title}\n"
        f"💰 *Prezzo Vinted:* {price:.2f} €\n"
        f"📏 *Taglia:* {size}\n"
        f"❤️ *Like:* {likes} | 🤝 *Offerte:* {offers}\n\n"
        f"📈 *Profitto Stimato:* ~{profit:.2f} €\n"
        f"📊 *ROI Reale:* ~{roi:.0f}%\n"
        f"✨ *Prezzo Vetrina Consigliato (Y):* ~{showcase_price:.2f} €\n\n"
        f"💡 *Perché sceglierlo (Analisi IA):*\n{analysis_comment}\n\n"
        f"🔗 [APRI E COMPRA SUBITO SUL LINK]({item_url})"
    )
    
    telegram_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": photo_url,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(telegram_api, data=payload, timeout=10)
        if r.status_code == 200:
            print(f"✅ Notifica Telegram inviata per: {title}")
    except Exception as e:
        print(f"❌ Errore invio Telegram: {e}")

# ==========================================
# 4. CICLO CONTINUO SMART CON JITTER ANTI-403
# ==========================================

print("🚀 Bot BAGF avviato su Google Colab con monitoraggio e analisi Gemini attiva!")

while True:
    for target in SEARCH_TARGETS:
        try:
            print(f"🔍 Scansione in corso per: {target['category_name']}...")
            response = requests.get(target["url"], headers=REQUEST_HEADERS, timeout=15)
            
            if response.status_code == 403:
                print(f"⚠️ Rilevato blocco temporaneo (403) su {target['category_name']}. Applico pausa di sicurezza...")
                time.sleep(120)
                continue
            
            elif response.status_code == 200:
                print(f"✅ Catalogo {target['category_name']} raggiunto correttamente.")
            
            sleep_time = random.randint(90, 150)
            print(f"⏳ Pausa di {sleep_time} secondi prima del prossimo controllo...")
            time.sleep(sleep_time)
            
        except Exception as e:
            print(f"❌ Errore di rete durante la scansione: {e}")
            time.sleep(60)
