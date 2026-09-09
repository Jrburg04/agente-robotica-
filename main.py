import os
import time
import json
import urllib.request
import threading
from datetime import datetime
from flask import Flask

# --- CONFIGURACIÓN ---
# Reemplaza esta URL por la URL de tu Webhook de Discord para el canal de Robótica
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/TU_WEBHOOK_ROBOTICA_AQUI"

TICKERS = ["NVDA", "ABB", "FANUY", "CGNX", "SYM"]
POSICIONES = {ticker: False for ticker in TICKERS}
HISTORIAL_PRECIOS = {ticker: [] for ticker in TICKERS}

app = Flask(__name__)

@app.route('/')
def home():
    return "Agente de Inversión en Robótica Operando OK - 24/7", 200

def enviar_discord(mensaje):
    if "TU_WEBHOOK_ROBOTICA_AQUI" in DISCORD_WEBHOOK_URL:
        print("⚠️ Pendiente configurar la URL del Webhook de Discord.")
        return
    try:
        data = json.dumps({"content": mensaje}).encode('utf-8')
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=data,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', 'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            print(f"📩 Alerta enviada a Discord ({response.getcode()}).")
    except Exception as e:
        print(f"❌ Error al enviar a Discord: {e}")

def obtener_precio_accion(symbol):
    # Consulta a la API de Stooq para evitar bloqueos HTTP 401/429
    url = f"https://stooq.com/q/l/?s={symbol}.us&f=sdgl1otc&e=json"
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    )
    with urllib.request.urlopen(req) as response:
        datos = json.loads(response.read().decode())
        precio = datos['symbols'][0]['close']
        if precio is not None and precio != 'N/A':
            return float(precio)
    raise ValueError("Precio no disponible")

def calcular_media_movil(ticker, periodo):
    precios = HISTORIAL_PRECIOS[ticker]
    if len(precios) < periodo:
        return 0.0
    return sum(precios[-periodo:]) / periodo

def analizar_ticker(ticker):
    global POSICIONES, HISTORIAL_PRECIOS
    try:
        precio_actual = obtener_precio_accion(ticker)
        HISTORIAL_PRECIOS[ticker].append(precio_actual)
        
        if len(HISTORIAL_PRECIOS[ticker]) > 30:
            HISTORIAL_PRECIOS[ticker].pop(0)

        ma_corta = calcular_media_movil(ticker, 3)
        ma_larga = calcular_media_movil(ticker, 10)

        hora_str = datetime.now().strftime("%H:%M:%S")
        print(f"[{hora_str}] 🤖 {ticker}: ${precio_actual:,.2f} | MA3: ${ma_corta:,.2f} | MA10: ${ma_larga:,.2f}")

        if ma_corta > 0 and ma_larga > 0:
            if ma_corta > ma_larga and not POSICIONES[ticker]:
                POSICIONES[ticker] = True
                msg = f"🚀 **[ROBÓTICA - SEÑAL DE COMPRA]**\n**Acción:** {ticker}\n**Precio:** ${precio_actual:,.2f} USD"
                enviar_discord(msg)

            elif ma_corta < ma_larga and POSICIONES[ticker]:
                POSICIONES[ticker] = False
                msg = f"⚠️ **[ROBÓTICA - SEÑAL DE VENTA]**\n**Acción:** {ticker}\n**Precio:** ${precio_actual:,.2f} USD"
                enviar_discord(msg)

    except Exception as e:
        print(f"❌ Error procesando {ticker}: {e}")

def bucle_agente():
    time.sleep(5)
    enviar_discord("🦾 **Agente de Inversión en Robótica Activo en Render.**")
    while True:
        for ticker in TICKERS:
            analizar_ticker(ticker)
            time.sleep(3)
        time.sleep(300)

t = threading.Thread(target=bucle_agente)
t.daemon = True
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
