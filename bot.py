import os
import time
import requests
import ccxt
import pandas as pd

API_KEY = os.environ.get("API_KEY", "")
API_SECRET = os.environ.get("API_SECRET", "")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
TESTNET = os.environ.get("TESTNET", "True") == "True"
SYMBOL = "BTC/USDT"
RISK_PERCENT = 2
STOP_LOSS_PERCENT = 3
TAKE_PROFIT_PERCENT = 6
CHECK_INTERVAL = 60
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

def bildirim_gonder(mesaj):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": mesaj}, timeout=10)
    except Exception as e:
        print("Telegram hatasi: " + str(e))

def exchange_baglantisi_kur():
    exchange = ccxt.binance({"apiKey": API_KEY, "secret": API_SECRET})
    if TESTNET:
        exchange.set_sandbox_mode(True)
    return exchange

def fiyat_al(exchange):
    ticker = exchange.fetch_ticker(SYMBOL)
    fiyat = ticker["last"]
    print("Guncel fiyat: $" + str(fiyat))
    return fiyat

def bakiye_al(exchange):
    bakiye = exchange.fetch_balance()
    usdt = bakiye["USDT"]["free"]
    print("Bakiye: $" + str(usdt))
    return usdt

def mumlar_al(exchange):
    mumlar = exchange.fetch_ohlcv(SYMBOL, timeframe="1h", limit=100)
    df = pd.DataFrame(mumlar, columns=["zaman", "acilis", "yuksek", "dusuk", "kapanis", "hacim"])
    return df

def rsi_hesapla(df):
    fark = df["kapanis"].diff()
    kazan = fark.clip(lower=0)
    kayip = -fark.clip(upper=0)
    rs = kazan.rolling(14).mean() / kayip.rolling(14).mean()
    return 100 - (100 / (1 + rs))

def ema_hesapla(df):
    return df["kapanis"].ewm(span=20, adjust=False).mean()

def fear_greed_al():
    try:
        veri = requests.get("https://api.alternative.me/fng/?limit=1", timeout=10).json()
        deger = int(veri["data"][0]["value"])
        etiket = veri["data"][0]["value_classification"]
        print("Fear & Greed: " + str(deger) + " (" + etiket + ")")
        if deger <= 25:
            return "ASIRI_KORKU"
        elif deger <= 45:
            return "KORKU"
        elif deger <= 55:
            return "NOTR"
        elif deger <= 75:
            return "ACGOZLULUK"
        else:
            return "ASIRI_ACGOZLULUK"
    except Exception as e:
        print("Fear Greed hatasi: " + str(e))
        return "NOTR"

def funding_rate_al():
    try:
        veri = requests.get("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=1", timeout=10).json()
        rate = float(veri[0]["fundingRate"]) * 100
        print("Funding Rate: %" + str(round(rate, 4)))
        if rate > 0.05:
            return "ASIRI_LONG"
        elif rate < -0.05:
            return "ASIRI_SHORT"
        else:
            return "DENGELI"
    except Exception as e:
        print("Funding hatasi: " + str(e))
        return "DENGELI"

def claude_karar_al(fiyat, rsi, ema, fear_greed, funding, bakiye):
    prompt = "Sen bir kripto trading uzmanisın. Analiz et ve karar ver.\n"
    prompt += "BTC Fiyat: $" + str(fiyat) + "\n"
    prompt += "RSI: " + str(round(rsi, 2)) + "\n"
    prompt += "EMA: " + str(round(ema, 2)) + "\n"
    prompt += "Fear & Greed: " + fear_greed + "\n"
    prompt += "Funding: " + funding + "\n"
    prompt += "Bakiye: $" + str(bakiye) + "\n"
    prompt += "YANIT FORMATI: KARAR: AL veya SAT veya BEKLE, GEREKCE: kisa aciklama, GUVENILIRLIK: DUSUK veya ORTA veya YUKSEK"
    headers = {"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    veri = {"model": "claude-sonnet-4-6", "max_tokens": 150, "messages": [{"role": "user", "content": prompt}]}
    try:
        yanit = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=veri, timeout=15)
        metin = yanit.json()["content"][0]["text"]
        print("Claude: " + metin)
        if "KARAR: AL" in metin:
            return "AL", metin
        elif "KARAR: SAT" in metin:
            return "SAT", metin
        else:
            return "BEKLE", metin
    except Exception as e:
        print("Claude hatasi: " + str(e))
        return "BEKLE", "hata"

def al(exchange, fiyat, bakiye):
    btc = exchange.fetch_balance()["BTC"]["free"]
    if btc * fiyat > bakiye * 0.05:
        print("Yeterli BTC var.")
        return None
    miktar = round((bakiye * RISK_PERCENT / 100) / fiyat, 6)
    if miktar * fiyat < 10:
        print("Bakiye yetersiz.")
        return None
    print("ALIS: " + str(miktar) + " BTC @ $" + str(fiyat))
    emir = exchange.create_market_buy_order(SYMBOL, miktar)
    stop = round(fiyat * (1 - STOP_LOSS_PERCENT / 100), 2)
    hedef = round(fiyat * (1 + TAKE_PROFIT_PERCENT / 100), 2)
    return {"emir": emir, "stop": stop, "hedef": hedef, "giris": fiyat}

def sat(exchange, miktar, fiyat):
    print("SATIS: " + str(miktar) + " BTC @ $" + str(fiyat))
    return exchange.create_market_sell_order(SYMBOL, miktar)

def bot_calistir():
    bildirim_gonder("Bot basladi! " + SYMBOL)
    print("Bot basladi!")
    ex = exchange_baglantisi_kur()
    acik_pozisyon = [None]
    while True:
        try:
            print("--- Tarama ---")
            fiyat = fiyat_al(ex)
            bakiye = bakiye_al(ex)
            df = mumlar_al(ex)
            df["rsi"] = rsi_hesapla(df)
            df["ema"] = ema_hesapla(df)
            son = df.iloc[-1]
            rsi = son["rsi"]
            ema = son["ema"]
            print("RSI: " + str(round(rsi, 2)) + " EMA: " + str(round(ema, 2)))
            fg = fear_greed_al()
            funding = funding_rate_al()
            if acik_pozisyon[0]:
                if fiyat <= acik_pozisyon[0]["stop"]:
                    btc = ex.fetch_balance()["BTC"]["free"]
                    if btc > 0:
                        sat(ex, btc, fiyat)
                        bildirim_gonder("STOP-LOSS! $" + str(fiyat))
                    acik_pozisyon[0] = None
                elif fiyat >= acik_pozisyon[0]["hedef"]:
                    btc = ex.fetch_balance()["BTC"]["free"]
                    if btc > 0:
                        sat(ex, btc, fiyat)
                        bildirim_gonder("TAKE-PROFIT! $" + str(fiyat))
                    acik_pozisyon[0] = None
                else:
                    kar = round(((fiyat - acik_pozisyon[0]["giris"]) / acik_pozisyon[0]["giris"]) * 100, 2)
                    print("Pozisyon kar: %" + str(kar))
            else:
                karar, aciklama = claude_karar_al(fiyat, rsi, ema, fg, funding, bakiye)
                if karar == "AL":
                    sonuc = al(ex, fiyat, bakiye)
                    if sonuc:
                        acik_pozisyon[0] = sonuc
                        bildirim_gonder("ALIS! $" + str(fiyat) + " Stop: $" + str(sonuc["stop"]) + " Hedef: $" + str(sonuc["hedef"]))
                elif karar == "SAT":
                    btc = ex.fetch_balance()["BTC"]["free"]
                    if btc > 0:
                        sat(ex, btc, fiyat)
                        bildirim_gonder("SATIS! $" + str(fiyat))
            print("Sonraki tarama " + str(CHECK_INTERVAL) + " saniye sonra...")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            bildirim_gonder("Bot durduruldu.")
            break
        except Exception as e:
            print("Hata: " + str(e))
            bildirim_gonder("Hata: " + str(e))
            time.sleep(30)

if __name__ == "__main__":
    bot_calistir()
