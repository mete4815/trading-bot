import requests
import time
import config
import json

TELEGRAM_TOKEN = None
CHAT_ID = None

def token_yukle():
    global TELEGRAM_TOKEN, CHAT_ID
    import telegram_bildirim
    TELEGRAM_TOKEN = telegram_bildirim.TELEGRAM_TOKEN
    CHAT_ID = telegram_bildirim.CHAT_ID

def mesaj_gonder(metin):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": metin})

def guncelleme_al(offset=None):
    url = "https://api.telegram.org/bot" + TELEGRAM_TOKEN + "/getUpdates"
    params = {"timeout": 10}
    if offset:
        params["offset"] = offset
    try:
        yanit = requests.get(url, params=params, timeout=15)
        return yanit.json()
    except:
        return {"result": []}

def komut_isle(metin, ex, acik_pozisyon_ref):
    if metin == "/bakiye":
        try:
            bakiye = ex.fetch_balance()
            usdt = round(bakiye['USDT']['free'], 2)
            btc = round(bakiye['BTC']['free'], 6)
            fiyat = ex.fetch_ticker(config.SYMBOL)['last']
            btc_deger = round(btc * fiyat, 2)
            toplam = round(usdt + btc_deger, 2)
            mesaj = "Bakiye\nUSDT: " + str(usdt) + "\nBTC: " + str(btc) + "\nToplam: " + str(toplam)
        except Exception as e:
            mesaj = "Hata: " + str(e)
        mesaj_gonder(mesaj)
    elif metin == "/durum":
        try:
            fiyat = ex.fetch_ticker(config.SYMBOL)['last']
            if acik_pozisyon_ref[0]:
                poz = acik_pozisyon_ref[0]
                kar = round(((fiyat - poz['giris']) / poz['giris']) * 100, 2)
                mesaj = "Pozisyon\nGiris: " + str(poz['giris']) + "\nGuncel: " + str(fiyat) + "\nKar: %" + str(kar) + "\nStop: " + str(poz['stop']) + "\nHedef: " + str(poz['hedef'])
            else:
                mesaj = "Acik pozisyon yok. BTC: " + str(fiyat)
        except Exception as e:
            mesaj = "Hata: " + str(e)
        mesaj_gonder(mesaj)
    elif metin == "/gecmis":
        try:
            with open("islemler.json", "r") as f:
                islemler = json.load(f)
            mesaj = "Son 5 Islem\n"
            for i in islemler[-5:]:
                mesaj += i['zaman'] + " " + i['islem'] + " $" + str(i['fiyat']) + "\n"
        except:
            mesaj = "Islem gecmisi yok."
        mesaj_gonder(mesaj)
    elif metin == "/yardim":
        mesaj = "/bakiye /durum /gecmis /yardim"
        mesaj_gonder(mesaj)

def komut_dinle(ex, acik_pozisyon_ref):
    token_yukle()
    offset = None
    while True:
        try:
            guncellemeler = guncelleme_al(offset)
            for g in guncellemeler.get("result", []):
                offset = g["update_id"] + 1
                metin = g.get("message", {}).get("text", "")
                if metin.startswith("/"):
                    komut_isle(metin, ex, acik_pozisyon_ref)
            time.sleep(1)
        except Exception as e:
            time.sleep(5)
