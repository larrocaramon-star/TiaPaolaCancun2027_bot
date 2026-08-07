# scrape_and_notify.py
# MVP: valida rango de fechas, hace scraping básico (placeholders),
# elige la mejor oferta on-airport y notifica por Telegram.
# Ajusta los selectores en parseadores según las páginas reales.

import os
import json
import requests
from datetime import datetime, date
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Rango permitido (exclusivo requisito)
RANGO_INICIO = date(2026, 2, 3)
RANGO_FIN = date(2026, 2, 15)

# Fuentes iniciales: reemplaza por URLs de búsqueda con pickup=CUN
SOURCES = [
    {"name": "Hertz", "url": "https://www.hertz.com/rentacar/reservation/?pickup=CUN"},
    {"name": "Sixt", "url": "https://www.sixt.com/car-rental/mexico/cancun-airport/"}
]

OFFERS_FILE = "offers.json"

def parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date()

def validar_rango_fechas(fecha_inicio_str, fecha_fin_str):
    try:
        inicio = parse_date(fecha_inicio_str)
        fin = parse_date(fecha_fin_str)
    except Exception:
        raise ValueError("Formato inválido. Usa YYYY-MM-DD.")
    if inicio < RANGO_INICIO or fin > RANGO_FIN:
        raise ValueError(f"Fechas fuera del rango permitido: {RANGO_INICIO} a {RANGO_FIN}.")
    if inicio > fin:
        raise ValueError("La fecha de inicio no puede ser posterior a la de fin.")
    return inicio, fin

def send_telegram(text):
    if not BOT_TOKEN or not CHAT_ID:
        print("Falta BOT_TOKEN o CHAT_ID en variables de entorno.")
        return False, "Missing token/chat"
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, data=payload, timeout=30)
        return r.ok, r.text
    except Exception as e:
        return False, str(e)

def fetch_page(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0; +https://github.com/)"
    }
    try:
        r = requests.get(url, headers=headers, timeout=30)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print("Error fetching", url, e)
        return None

# Parsers de ejemplo: ajusta selectores según cada web real
def parse_hertz(html):
    soup = BeautifulSoup(html, "html.parser")
    price = None
    insurance = "No especificado"
    office = "Desconocida"
    price_tag = soup.select_one("span.total-price") or soup.select_one(".price-total")
    if price_tag:
        price = price_tag.get_text(strip=True)
    ins_tag = soup.select_one(".insurance-summary") or soup.find(text=lambda t: t and "insurance" in t.lower())
    if ins_tag:
        insurance = ins_tag.get_text(strip=True) if hasattr(ins_tag, "get_text") else str(ins_tag).strip()
    office_tag = soup.select_one(".pickup-location") or soup.find(text=lambda t: t and ("CUN" in t.upper() or "CANCUN" in t.upper() or "AEROPUERTO" in t.upper() or "AIRPORT" in t.upper()))
    if office_tag:
        office = office_tag.get_text(strip=True) if hasattr(office_tag, "get_text") else str(office_tag).strip()
    return {"rentadora": "Hertz", "office": office, "price": price, "insurance": insurance}

def parse_sixt(html):
    soup = BeautifulSoup(html, "html.parser")
    price = None
    insurance = "No especificado"
    office = "Desconocida"
    price_tag = soup.select_one(".price") or soup.select_one(".total-price")
    if price_tag:
        price = price_tag.get_text(strip=True)
    ins_tag = soup.select_one(".insurance") or soup.find(text=lambda t: t and ("CDW" in t or "insurance" in t.lower()))
    if ins_tag:
        insurance = ins_tag.get_text(strip=True) if hasattr(ins_tag, "get_text") else str(ins_tag).strip()
    office_tag = soup.find(text=lambda t: t and ("CANCUN" in t.upper() or "AEROPUERTO" in t.upper() or "CUN" in t.upper()))
    if office_tag:
        office = office_tag.strip()
    return {"rentadora": "Sixt", "office": office, "price": price, "insurance": insurance}

def parse_generic(name, html):
    if "hertz" in name.lower():
        return parse_hertz(html)
    if "sixt" in name.lower():
        return parse_sixt(html)
    # fallback simple
    soup = BeautifulSoup(html, "html.parser")
    price_tag = soup.select_one("span.total-price") or soup.select_one(".price")
    price = price_tag.get_text(strip=True) if price_tag else None
    office = "Desconocida"
    ins = "No especificado"
    return {"rentadora": name, "office": office, "price": price, "insurance": ins}

def scrape_offers(start_date, end_date):
    offers = []
    for src in SOURCES:
        html = fetch_page(src["url"])
        if not html:
            continue
        data = parse_generic(src["name"], html)
        data["url"] = src["url"]
        data["scraped_at"] = datetime.utcnow().isoformat()
        office_upper = (data.get("office") or "").upper()
        if any(k in office_upper for k in ["CUN", "AEROPUERTO", "AIRPORT", "CANCUN"]):
            offers.append(data)
    return offers

def save_offers(offers):
    try:
        with open(OFFERS_FILE, "w", encoding="utf-8") as f:
            json.dump(offers, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving offers:", e)

def choose_best_offer(offers):
    def price_to_number(p):
        if not p:
            return float("inf")
        s = "".join(ch for ch in p if (ch.isdigit() or ch in ".,"))
        s = s.replace(",", "")
        try:
            return float(s)
        except:
            return float("inf")
    offers_sorted = sorted(offers, key=lambda o: price_to_number(o.get("price")))
    return offers_sorted[0] if offers_sorted else None

def format_message(offer, inicio, fin):
    if not offer:
        return "No se encontraron ofertas on-airport para las fechas seleccionadas."
    return (
        f"*Oferta del día — {offer['rentadora']}*\n"
        f"Oficina: {offer['office']}\n"
        f"Fechas: {inicio.isoformat()} → {fin.isoformat()}\n"
        f"*Precio total:* {offer.get('price','No disponible')}\n"
        f"*Seguros incluidos:* {offer.get('insurance','No especificado')}\n"
        f"Reservar: {offer.get('url')}\n"
        f"_Precio verificado en la página de la rentadora; confirma en checkout._"
    )

def main():
    fecha_inicio = os.environ.get("RENT_START", "")
    fecha_fin = os.environ.get("RENT_END", "")
    if not fecha_inicio or not fecha_fin:
        send_telegram("Error: no se definieron RENT_START y RENT_END en el workflow.")
        return

    try:
        inicio, fin = validar_rango_fechas(fecha_inicio, fecha_fin)
    except ValueError as e:
        send_telegram(f"Fechas inválidas: {e}")
        return

    offers = scrape_offers(inicio, fin)
    save_offers(offers)
    best = choose_best_offer(offers)
    msg = format_message(best, inicio, fin)
    ok, resp = send_telegram(msg)
    if not ok:
        print("Telegram error:", resp)

if __name__ == "__main__":
    main()
