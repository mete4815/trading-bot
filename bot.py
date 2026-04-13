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
COINS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]
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


def telegram_komut_dinle(ex, acik_pozisyon):
    import threading
    offset = [None]
    
    def dinle():
        while True:
            try:
                url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/getUpdates"
                params = {"timeout": 10}
                if offset[0]:
                    params["offset"] = offset[0]
                yanit = requests.get(url, params=params, timeout=15)
                for g in yanit.json().get("result", []):
                    offset[0] = g["update_id"] + 1
                    metin = g.get("message", {}).get("text", "")
                    if metin == "/bakiye":
                        try:
                            b = ex.fetch_balance()
                            usdt = round(b["USDT"]["free"], 2)
                            btc = round(b["BTC"]["free"], 6)
                            fiyat = ex.fetch_ticker(SYMBOL)["last"]
                            toplam = round(usdt + btc * fiyat, 2)
                            bildirim_gonder("Bakiye\nUSDT: " + str(usdt) + "\nBTC: " + str(btc) + "\nToplam: $" + str(toplam))
                        except Exception as e:
                            bildirim_gonder("Hata: " + str(e))
                    elif metin == "/durum":
                        try:
                            fiyat = ex.fetch_ticker(SYMBOL)["last"]
                            if acik_pozisyon[0]:
                                poz = acik_pozisyon[0]
                                kar = round(((fiyat - poz["giris"]) / poz["giris"]) * 100, 2)
                                bildirim_gonder("Pozisyon\nGiris: $" + str(poz["giris"]) + "\nGuncel: $" + str(fiyat) + "\nKar: %" + str(kar))
                            else:
                                bildirim_gonder("Acik pozisyon yok. BTC: $" + str(fiyat))
                        except Exception as e:
                            bildirim_gonder("Hata: " + str(e))
                    elif metin == "/yardim":
                        bildirim_gonder("/bakiye /durum /yardim")
                import time
                time.sleep(1)
            except Exception as e:
                import time
                time.sleep(5)
    
    t = threading.Thread(target=dinle, daemon=True)
    t.start()

def bot_calistir():
    bildirim_gonder("Bot basladi! Tum coinler taranıyor.")
    print("Bot basladi!")
    ex = exchange_baglantisi_kur()
    acik_pozisyon = [None]
    telegram_komut_dinle(ex, acik_pozisyon)
    while True:
        try:
            print("--- Tarama ---")
            bakiye = bakiye_al(ex)
            fg = fear_greed_al()
            funding = funding_rate_al()
            en_iyi_coin = None
            en_iyi_skor = -999

            for coin in COINS:
                try:
                    ticker = ex.fetch_ticker(coin)
                    fiyat = ticker["last"]
                    mumlar = ex.fetch_ohlcv(coin, timeframe="1h", limit=100)
                    df = pd.DataFrame(mumlar, columns=["zaman", "acilis", "yuksek", "dusuk", "kapanis", "hacim"])
                    df["rsi"] = rsi_hesapla(df)
                    df["ema"] = ema_hesapla(df)
                    son = df.iloc[-1]
                    rsi = son["rsi"]
                    ema = son["ema"]
                    skor = 0
                    if rsi < 40:
                        skor += 3
                    elif rsi < 50:
                        skor += 1
                    elif rsi > 70:
                        skor -= 2
                    if fiyat > ema:
                        skor += 1
                    print(coin + " RSI: " + str(round(rsi, 2)) + " Skor: " + str(skor))
                    if skor > en_iyi_skor:
                        en_iyi_skor = skor
                        en_iyi_coin = {"coin": coin, "fiyat": fiyat, "rsi": rsi, "ema": ema}
                except Exception as e:
                    print(coin + " hata: " + str(e))

            if acik_pozisyon[0]:
                coin_data = acik_pozisyon[0]
                ticker = ex.fetch_ticker(coin_data["coin"])
                fiyat = ticker["last"]
                if fiyat <= coin_data["stop"]:
                    coin_symbol = coin_data["coin"].replace("/", "")
                    base = coin_data["coin"].split("/")[0]
                    coin_bakiye = ex.fetch_balance()[base]["free"]
                    if coin_bakiye > 0:
                        ex.create_market_sell_order(coin_data["coin"], coin_bakiye)
                        bildirim_gonder("STOP-LOSS! " + coin_data["coin"] + " $" + str(fiyat))
                    acik_pozisyon[0] = None
                elif fiyat >= coin_data["hedef"]:
                    base = coin_data["coin"].split("/")[0]
                    coin_bakiye = ex.fetch_balance()[base]["free"]
                    if coin_bakiye > 0:
                        ex.create_market_sell_order(coin_data["coin"], coin_bakiye)
                        bildirim_gonder("TAKE-PROFIT! " + coin_data["coin"] + " $" + str(fiyat))
                    acik_pozisyon[0] = None
                else:
                    kar = round(((fiyat - coin_data["giris"]) / coin_data["giris"]) * 100, 2)
                    print("Pozisyon kar: %" + str(kar))
            elif en_iyi_coin and en_iyi_skor >= 2:
                coin = en_iyi_coin["coin"]
                fiyat = en_iyi_coin["fiyat"]
                rsi = en_iyi_coin["rsi"]
                ema = en_iyi_coin["ema"]
                karar, aciklama = claude_karar_al(fiyat, rsi, ema, fg, funding, bakiye)
                if karar == "AL":
                    miktar = round((bakiye * RISK_PERCENT / 100) / fiyat, 6)
                    if miktar * fiyat >= 10:
                        emir = ex.create_market_buy_order(coin, miktar)
                        stop = round(fiyat * (1 - STOP_LOSS_PERCENT / 100), 4)
                        hedef = round(fiyat * (1 + TAKE_PROFIT_PERCENT / 100), 4)
                        acik_pozisyon[0] = {"coin": coin, "giris": fiyat, "stop": stop, "hedef": hedef, "miktar": miktar}
                        bildirim_gonder("ALIS! " + coin + " $" + str(fiyat) + " Stop: $" + str(stop) + " Hedef: $" + str(hedef))
                    else:
                        print("Bakiye yetersiz.")
            else:
                print("Uygun coin bulunamadi, bekleniyor.")
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

