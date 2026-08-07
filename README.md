# Cancun Cars Bot

Bot que envía 1 oferta diaria de renta de autos on-airport en Cancún.
Valida fechas entre 2026-02-03 y 2026-02-15.

## Archivos incluidos
- `scrape_and_notify.py` : script principal.
- `requirements.txt` : dependencias.
- `.github/workflows/daily-offer.yml` : workflow diario y manual.
- `.github/workflows/test-telegram.yml` : workflow de prueba.
- `offers.json` : archivo donde se guardan ofertas.

## Configuración rápida
1. Crear bot en Telegram con BotFather y enviar `/start` al bot.
2. Obtener `BOT_TOKEN` y `CHAT_ID` (usa @userinfobot).
3. En GitHub repo → Settings → Secrets and variables → Actions:
   - Añadir `BOT_TOKEN`
   - Añadir `CHAT_ID`
4. Subir estos archivos al repo (commit en `main`).
5. Ejecutar `Test Telegram` desde Actions para verificar conexión.
6. Ejecutar `Daily Car Offer (CUN)` manualmente o esperar el cron.

## Notas
- Ajusta los selectores en `scrape_and_notify.py` para cada rentadora.
- Si la web carga precios con JavaScript, considera usar Playwright.
- Siempre incluye el enlace al checkout en el mensaje para verificar el precio final.
