import requests

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

def haber_skoru_al():
    try:
        url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&categories=BTC"
        yanit = requests.get(url, timeout=10)
        veri = yanit.json()
        haberler = veri.get('Data', [])[:10]

        pozitif_kelimeler = ['bull', 'surge', 'rally', 'gain', 'high', 'up', 'rise',
                             'growth', 'positive', 'buy', 'support', 'breakout', 'ath']
        negatif_kelimeler = ['bear', 'crash', 'drop', 'fall', 'low', 'down', 'sell',
                             'fear', 'risk', 'warning', 'hack', 'ban', 'regulation']

        pozitif = 0
        negatif = 0

        for haber in haberler:
            baslik = haber.get('title', '').lower()
            for k in pozitif_kelimeler:
                if k in baslik:
                    pozitif += 1
            for k in negatif_kelimeler:
                if k in baslik:
                    negatif += 1

        print(f"Haber analizi: +{pozitif} pozitif / -{negatif} negatif kelime")

        if pozitif > negatif + 2:
            return "POZITIF"
        elif negatif > pozitif + 2:
            return "NEGATIF"
        else:
            return "NOTR"

    except Exception as e:
        print(f"Haber hatası: {e}")
        return "NOTR"

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

def btc_dominance_al():
    try:
        url = "https://api.coingecko.com/api/v3/global"
        yanit = requests.get(url, timeout=10)
        veri = yanit.json()
        dominance = veri['data']['market_cap_percentage']['btc']
        print(f"BTC Dominance: %{round(dominance, 2)}")
        if dominance > 60:
            return "YUKSEK"
        elif dominance < 45:
            return "DUSUK"
        else:
            return "NORMAL"
    except Exception as e:
        print(f"BTC dominance hatası: {e}")
        return "NORMAL"

def piyasa_skoru_hesapla():
    print("\n--- Piyasa Analizi ---")
    fg, fg_deger = fear_greed_al()
    haber = haber_skoru_al()
    funding = funding_rate_al()
    dominance = btc_dominance_al()

    skor = 0

    if fg == "ASIRI_KORKU":
        skor += 3
    elif fg == "KORKU":
        skor += 1
    elif fg == "ASIRI_ACGOZLULUK":
        skor -= 2
    elif fg == "ACGOZLULUK":
        skor -= 1

    if haber == "POZITIF":
        skor += 2
    elif haber == "NEGATIF":
        skor -= 2

    if funding == "ASIRI_SHORT":
        skor += 2
    elif funding == "ASIRI_LONG":
        skor -= 2

    if dominance == "YUKSEK":
        skor += 1
    elif dominance == "DUSUK":
        skor -= 1

    print(f"Toplam piyasa skoru: {skor}")
    return skor
