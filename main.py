import os
import time
import json
import urllib.request
import threading
from datetime import datetime
from flask import Flask
import yfinance as yf

# --- CONFIGURACIÓN ---
# Reemplazarás esta URL por el Webhook del canal de Discord para Robótica
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/TU_WEBHOOK_ROBOTICA_AQUI"

TICKERS = ["NVDA", "ABB", "FANUY", "CGNX", "SYM"]
POSICIONES = {ticker: False for ticker in TICKERS}

app = Flask(__name__)

@app.route('/')
def home():
    return "Agente de Inversión en Robótica Operando OK - 24/7", 200

def enviar_discord(mensaje):
    if "TU_WEBHOOK_ROBOTICA_AQUI" in DISCORD_WEBHOOK_URL:
        print("⚠️ Configura el Webhook de Discord para Robótica.")
        return
    try:
        data = json.dumps({"content": mensaje}).encode('utf-8')
        req = urllib.request.Request(
            DISCORD_WEBHOOK_URL,
            data=data,
            headers={'User-Agent': 'Mozilla/5.0', 'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req) as response:
            print(f"📩 Alerta Robótica enviada a Discord ({response.getcode()}).")
    except Exception as e:
        print(f"❌ Error enviando a Discord: {e}")

def analizar_ticker(ticker):
    global POSICIONES
    try:
        data = yf.Ticker(ticker).history(period="1mo", interval="1d")
        if len(data) < 21:
            return

        ema9 = data['Close'].ewm(span=9, adjust=False).mean().iloc[-1]
        ema21 = data['Close'].ewm(span=21, adjust=False).mean().iloc[-1]
        precio_actual = data['Close'].iloc[-1]

        hora_str = datetime.now().strftime("%H:%M:%S")
        print(f"[{hora_str}] 🤖 {ticker}: ${precio_actual:,.2f} | EMA9: ${ema9:,.2f} | EMA21: ${ema21:,.2f}")

        if ema9 > ema21 and not POSICIONES[ticker]:
            POSICIONES[ticker] = True
            msg = f"🚀 **[ROBÓTICA - SEÑAL DE COMPRA]**\n**Acción:** {ticker}\n**Precio:** ${precio_actual:,.2f}\n**Tendencia:** EMA9 (${ema9:,.2f}) superó EMA21 (${ema21:,.2f})"
            enviar_discord(msg)

        elif ema9 < ema21 and POSICIONES[ticker]:
            POSICIONES[ticker] = False
            msg = f"⚠️ **[ROBÓTICA - SEÑAL DE VENTA / TOMA DE GANANCIA]**\n**Acción:** {ticker}\n**Precio:** ${precio_actual:,.2f}\n**Tendencia:** EMA9 por debajo de EMA21"
            enviar_discord(msg)

    except Exception as e:
        print(f"❌ Error analizando {ticker}: {e}")

def bucle_agente():
    time.sleep(5)
    enviar_discord("🦾 **Agente de Inversión en Robótica y Componentes Activo.**")
    while True:
        for ticker in TICKERS:
            analizar_ticker(ticker)
            time.sleep(2)
        time.sleep(300)

t = threading.Thread(target=bucle_agente)
t.daemon = True
t.start()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
