# scrape_and_notify.py
# Versión MVP: valida rango de fechas y envía mensaje de estado a Telegram.
import os
import requests
from datetime import datetime, date

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

# Rango permitido (ajusta año si hace falta)
RANGO_INICIO = date(2026, 2, 3)
RANGO_FIN = date(2026, 2, 15)

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
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    r = requests.post(url, data=payload)
    return r.ok, r.text

def main():
    # Lee fechas desde variables de entorno (workflow o secrets)
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

    # Aquí iría el scraping real. Por ahora enviamos mensaje de confirmación.
    texto = (
        f"✅ Fechas válidas para cotizar:\n"
        f"Inicio: {inicio.isoformat()}\n"
        f"Fin: {fin.isoformat()}\n"
        f"Próximo paso: ejecutar scraping y enviar oferta real."
    )
    ok, resp = send_telegram(texto)
    if not ok:
        print("Telegram error:", resp)

if __name__ == "__main__":
    main()
