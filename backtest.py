import ccxt
import pandas as pd
from datetime import datetime

def gecmis_veri_al(symbol="BTC/USDT", timeframe="1h", limit=1000):
    exchange = ccxt.binance()
    mumlar = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(mumlar, columns=['zaman', 'acilis', 'yuksek', 'dusuk', 'kapanis', 'hacim'])
    df['zaman'] = pd.to_datetime(df['zaman'], unit='ms')
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

def backtest_calistir(baslangic_bakiye=10000, risk=0.02, stop=0.03, hedef=0.06):
    print("Geçmiş veri çekiliyor...")
    df = gecmis_veri_al(limit=1000)
    df['rsi'] = rsi_hesapla(df)
    df['ema'] = ema_hesapla(df)
    df = df.dropna()

    bakiye = baslangic_bakiye
    acik_pozisyon = None
    islemler = []
    kazanan = 0
    kaybeden = 0

    print(f"Backtest başladı — {len(df)} mum analiz ediliyor...")
    print(f"Başlangıç bakiyesi: ${bakiye}\n")

    for i, satir in df.iterrows():
        fiyat = satir['kapanis']
        rsi = satir['rsi']
        ema = satir['ema']
        zaman = satir['zaman']

        if acik_pozisyon:
            if fiyat <= acik_pozisyon['stop']:
                kazanc = (fiyat - acik_pozisyon['giris']) * acik_pozisyon['miktar']
                bakiye += kazanc
                kaybeden += 1
                islemler.append({
                    'zaman': zaman,
                    'tip': 'SAT (stop)',
                    'fiyat': fiyat,
                    'kazanc': round(kazanc, 2),
                    'bakiye': round(bakiye, 2)
                })
                acik_pozisyon = None

            elif fiyat >= acik_pozisyon['hedef']:
                kazanc = (fiyat - acik_pozisyon['giris']) * acik_pozisyon['miktar']
                bakiye += kazanc
                kazanan += 1
                islemler.append({
                    'zaman': zaman,
                    'tip': 'SAT (hedef)',
                    'fiyat': fiyat,
                    'kazanc': round(kazanc, 2),
                    'bakiye': round(bakiye, 2)
                })
                acik_pozisyon = None

        else:
            if rsi < 40 and fiyat > ema:
                kullanilan = bakiye * risk
                miktar = kullanilan / fiyat
                acik_pozisyon = {
                    'giris': fiyat,
                    'miktar': miktar,
                    'stop': fiyat * (1 - stop),
                    'hedef': fiyat * (1 + hedef),
                    'zaman': zaman
                }
                islemler.append({
                    'zaman': zaman,
                    'tip': 'AL',
                    'fiyat': fiyat,
                    'kazanc': 0,
                    'bakiye': round(bakiye, 2)
                })

    toplam_islem = kazanan + kaybeden
    kar = round(bakiye - baslangic_bakiye, 2)
    kar_yuzde = round((kar / baslangic_bakiye) * 100, 2)
    basari = round((kazanan / toplam_islem * 100), 2) if toplam_islem > 0 else 0

    print("=" * 50)
    print("   BACKTEST SONUÇLARI")
    print("=" * 50)
    print(f"Başlangıç bakiyesi : ${baslangic_bakiye}")
    print(f"Son bakiye         : ${round(bakiye, 2)}")
    print(f"Toplam kâr/zarar   : ${kar} (%{kar_yuzde})")
    print(f"Toplam işlem       : {toplam_islem}")
    print(f"Kazanan işlem      : {kazanan}")
    print(f"Kaybeden işlem     : {kaybeden}")
    print(f"Başarı oranı       : %{basari}")
    print("=" * 50)

    if islemler:
        print("\nSon 5 işlem:")
        for i in islemler[-5:]:
            print(f"  {i['zaman']} | {i['tip']} | ${i['fiyat']:.2f} | Kâr: ${i['kazanc']} | Bakiye: ${i['bakiye']}")

if __name__ == "__main__":
    backtest_calistir()
