import os
import time
import threading

API_KEY = os.environ.get('API_KEY', '')
API_SECRET = os.environ.get('API_SECRET', '')
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
TESTNET = os.environ.get('TESTNET', 'True') == 'True'
SYMBOL = "BTC/USDT"
RISK_PERCENT = 2
STOP_LOSS_PERCENT = 3
TAKE_PROFIT_PERCENT = 6
CHECK_INTERVAL = 60

import ccxt
import pandas as pd
import requests
import json

def exchange_baglantisi_kur():
    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': API_SECRET,
    })
    if TESTNET:
        exchange.set_sandbox_mode(True)
    return exchange

def fiyat_al(exchange):
    ticker = exchange.fetch_ticker(SYMBOL)
    fiyat = ticker['last']
    print(f"Güncel {SYMBOL} fiyatı: ${fiyat}")
    return fiyat

def bakiye_al(exchange):
    bakiye = exchange.fetch_balance()
    usdt = bakiye['USDT']['free']
    print(f"Kullanılabilir bakiye: ${usdt}")
    return usdt

def mumlar_al(exchange, limit=100):
    mumlar = exchange.fetch_ohlcv(SYMBOL, timeframe='1h', limit=limit)
    df = pd.DataFrame(mumlar, columns=['zaman', 'acilis', 'yuksek', 'dusuk', 'kapanis', 'hacim'])
    return df

def rsi_hesapla(df, periyot=14):
    fark = df['kapanis'].diff()
    kazan = fark.clip(lower=0)
    kayip = -fark.clip(upper=0)
    ort_kazan = kazan.rolling(periyot).mean()
    ort_kayip = kayip.rolling(periyot).mean()
    rs = ort_kazan / ort_kayip
    return 100 - (100 / (1 + rs))

def ema_hesapla(df, periyot=20):
    return df['kapanis'].ewm(span=periyot, adjust=False).mean()

def fear_greed_al():
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        yanit = requests.get(url, timeout=10)
        veri = yanit.json()
        deger = int(veri['data'][0]['value'])
        etiket = veri['data'][0]['value_classification']
        print(f"Fear & Greed: {deger} ({etiket})")
        if deger <= 25:
            return "ASIRI_KORKU", deger
        elif deger <= 45:
            return "KORKU",
cat > ~/trading-bot/bot.py << 'DOSYASONU'
import os
import time
import threading

API_KEY = os.environ.get('API_KEY', '')
API_SECRET = os.environ.get('API_SECRET', '')
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', '')
TESTNET = os.environ.get('TESTNET', 'True') == 'True'
SYMBOL = "BTC/USDT"
RISK_PERCENT = 2
STOP_LOSS_PERCENT = 3
TAKE_PROFIT_PERCENT = 6
CHECK_INTERVAL = 60

import ccxt
import pandas as pd
import requests
import json

def exchange_baglantisi_kur():
    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': API_SECRET,
    })
    if TESTNET:
        exchange.set_sandbox_mode(True)
    return exchange

def fiyat_al(exchange):
    ticker = exchange.fetch_ticker(SYMBOL)
    fiyat = ticker['last']
    print(f"Güncel {SYMBOL} fiyatı: ${fiyat}")
    return fiyat

def bakiye_al(exchange):
    bakiye = exchange.fetch_balance()
    usdt = bakiye['USDT']['free']
    print(f"Kullanılabilir bakiye: ${usdt}")
    return usdt

def mumlar_al(exchange, limit=100):
    mumlar = exchange.fetch_ohlcv(SYMBOL, timeframe='1h', limit=limit)
    df = pd.DataFrame(mumlar, columns=['zaman', 'acilis', 'yuksek', 'dusuk', 'kapanis', 'hacim'])
    return df

def rsi_hesapla(df, periyot=14):
    fark = df['kapanis'].diff()
    kazan = fark.clip(lower=0)
    kayip = -fark.clip(upper=0)
    ort_kazan = kazan.rolling(periyot).mean()
    ort_kayip = kayip.rolling(periyot).mean()
    rs = ort_kazan / ort_kayip
    return 100 - (100 / (1 + rs))

def ema_hesapla(df, periyot=20):
    return df['kapanis'].ewm(span=periyot, adjust=False).mean()

def fear_greed_al():
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        yanit = requests.get(url, timeout=10)
        veri = yanit.json()
        deger = int(veri['data'][0]['value'])
        etiket = veri['data'][0]['value_classification']
        print(f"Fear & Greed: {deger} ({etiket})")
        if deger <= 25:
            return "ASIRI_KORKU", deger
        elif deger <= 45:
            return "KORKU", deger
        elif deger <= 55:
            return "NOTR", deger
        elif deger <= 75:
            return "ACGOZLULUK", deger
        else:
            return "ASIRI_ACGOZLULUK", deger
    except Exception as e:
        print(f"Fear & Greed hatası: {e}")
        return "NOTR", 50

def funding_rate_al():
    try:
        url = "https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1"
        yanit = requests.get(url, timeout=10)
        veri = yanit.json()
        rate = float(veri[0]['fundingRate']) * 100
        print(f"Funding Rate: %{round(rate, 4)}")
        if rate > 0.05:
            return "ASIRI_LONG"
        elif rate < -0.05:
            return "ASIRI_SHORT"
        else:
            return "DENGELI"
    except Exception as e:
        print(f"Funding rate hatası: {e}")
        return "DENGELI"

def claude_karar_al(fiyat, rsi, ema, fear_greed, funding, bakiye):
    prompt = f"""Sen bir kripto trading uzmanısın. Aşağıdaki piyasa verilerini analiz et ve karar ver.

GÜNCEL VERİLER:
- BTC/USDT Fiyatı: ${fiyat}
- RSI (14): {rsi:.2f}
- EMA (20): {ema:.2f}
- Fear & Greed Index: {fear_greed}
- Funding Rate: {funding}
- Mevcut Bakiye: ${bakiye}

YANIT FORMATI:
KARAR: [AL/SAT/BEKLE]
GEREKÇE: [kısa açıklama]
GÜVENİLİRLİK: [DÜŞÜK/ORTA/YÜKSEK]"""

    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    veri = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 150,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        yanit = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=veri, timeout=15)
        metin = yanit.json()['content'][0]['text']
        print(f"\n🤖 Claude Analizi:\n{metin}")
        if "KARAR: AL" in metin:
            return "AL", metin
        elif "KARAR: SAT" in metin:
            return "SAT", metin
        else:
            return "BEKLE", metin
    except Exception as e:
        print(f"Claude API hatası: {e}")
        return "BEKLE", "API hatası"

def bildirim_gonder(mesaj):
    token = os.environ.get('TELEGRAM_TOKEN', '')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '')
    if not token or not chat_id:
        return
    try:
        url = "https://api.telegram.org/bot" + token + "/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": mesaj}, timeout=10)
    except Exception as e:
        print(f"Telegram hatası: {e}")

def kaydet(islem_tipi, fiyat, miktar, stop=None, hedef=None):
    print(f"[LOG] {islem_tipi} | ${fiyat} | {miktar} BTC")

def pozisyon_boyutu_hesapla(bakiye, fiyat):
    kullanilacak = bakiye * (RISK_PERCENT / 100)
    miktar = kullanilacak / fiyat
    return round(miktar, 6)

def al(exchange, fiyat, bakiye):
    btc_bakiye = exchange.fetch_balance()['BTC']['free']
    btc_deger = btc_bakiye * fiyat
    if btc_deger > bakiye * 0.05:
        print("Zaten yeterli BTC var, yeni alış yapılmadı.")
        return None
    miktar = pozisyon_boyutu_hesapla(bakiye, fiyat)
    if miktar * fiyat < 10:
        print("Bakiye yetersiz.")
        return None
    print(f"ALIŞ EMRİ: {miktar} BTC @ ${fiyat}")
    emir = exchange.create_market_buy_order(SYMBOL, miktar)
    stop = round(fiyat * (1 - STOP_LOSS_PERCENT / 100), 2)
    hedef = round(fiyat * (1 + TAKE_PROFIT_PERCENT / 100), 2)
    print(f"Stop-loss: ${stop} | Take-profit: ${hedef}")
    return {'emir': emir, 'stop': stop, 'hedef': hedef, 'giris': fiyat}

def sat(exchange, miktar, fiyat):
    print(f"SATIŞ EMRİ: {miktar} BTC @ ${fiyat}")
    emir = exchange.create_market_sell_order(SYMBOL, miktar)
    return emir

def bot_calistir():
    bildirim_gonder("🤖 AI Trading Bot Başlatıldı\nCoin: " + SYMBOL + "\nRisk: %" + str(RISK_PERCENT))
    print("=" * 50)
    print("   AI Trading Bot Başlatıldı")
    print("=" * 50)

    ex = exchange_baglantisi_kur()
    acik_pozisyon = [None]

    while True:
        try:
            print(f"\n{'='*50}")
            print("Tarama Başladı")
            print(f"{'='*50}")

            fiyat = fiyat_al(ex)
            bakiye = bakiye_al(ex)

            df = mumlar_al(ex)
            df['rsi'] = rsi_hesapla(df)
            df['ema'] = ema_hesapla(df)
            son = df.iloc[-1]
            rsi = son['rsi']
            ema = son['ema']
            print(f"RSI: {rsi:.2f} | EMA: {ema:.2f}")

            fg, fg_deger = fear_greed_al()
            funding = funding_rate_al()

            if acik_pozisyon[0]:
                if fiyat <= acik_pozisyon[0]['stop']:
                    print(f"🛑 STOP-LOSS tetiklendi! ${fiyat}")
                    btc_bakiye = ex.fetch_balance()['BTC']['free']
                    if btc_bakiye > 0:
                        sat(ex, btc_bakiye, fiyat)
                        kaydet("SAT (stop-loss)", fiyat, btc_bakiye)
                        bildirim_gonder("🛑 STOP-LOSS tetiklendi!\nFiyat: $" + str(fiyat))
                    acik_pozisyon[0] = None
                elif fiyat >= acik_pozisyon[0]['hedef']:
                    print(f"🎯 TAKE-PROFIT tetiklendi! ${fiyat}")
                    btc_bakiye = ex.fetch_balance()['BTC']['free']
                    if btc_bakiye > 0:
                        sat(ex, btc_bakiye, fiyat)
                        kaydet("SAT (take-profit)", fiyat, btc_bakiye)
                        bildirim_gonder("🎯 TAKE-PROFIT tetiklendi!\nFiyat: $" + str(fiyat))
                    acik_pozisyon[0] = None
                else:
                    kar = ((fiyat - acik_pozisyon[0]['giris']) / acik_pozisyon[0]['giris']) * 100
                    print(f"📊 Açık pozisyon: Giriş ${acik_pozisyon[0]['giris']} | Güncel %{round(kar,2)}")
            else:
                karar, aciklama = claude_karar_al(fiyat, rsi, ema, fg, funding, bakiye)
                if karar == "AL":
                    sonuc = al(ex, fiyat, bakiye)
                    if sonuc:
                        acik_pozisyon[0] = sonuc
                        kaydet("AL", fiyat, sonuc['emir']['amount'], sonuc['stop'], sonuc['hedef'])
                        bildirim_gonder("🟢 ALIŞ EMRİ\nFiyat: $" + str(fiyat) + "\nStop: $" + str(sonuc['stop']) + "\nHedef: $" + str(sonuc['hedef']))
                elif karar == "SAT":
                    btc_bakiye = ex.fetch_balance()['BTC']['free']
                    if btc_bakiye > 0:
                        sat(ex, btc_bakiye, fiyat)
                        kaydet("SAT", fiyat, btc_bakiye)
                        bildirim_gonder("🔴 SATIŞ EMRİ\nFiyat: $" + str(fiyat))

            print(f"Sonraki tarama {CHECK_INTERVAL} saniye sonra...")
            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\nBot durduruldu.")
            bildirim_gonder("🔴 Bot durduruldu.")
            break
        except Exception as e:
            print(f"Hata: {e}")
            bildirim_gonder("⚠️ Bot hatası:\n" + str(e))
            time.sleep(30)

if __name__ == "__main__":
    bot_calistir()
