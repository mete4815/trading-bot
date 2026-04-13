import pandas as pd

def mumlar_al(exchange, symbol, limit=100):
    mumlar = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=limit)
    df = pd.DataFrame(mumlar, columns=['zaman', 'acilis', 'yuksek', 'dusuk', 'kapanis', 'hacim'])
    return df

def rsi_hesapla(df, periyot=14):
    fark = df['kapanis'].diff()
    kazan = fark.clip(lower=0)
    kayip = -fark.clip(upper=0)
    ort_kazan = kazan.rolling(periyot).mean()
    ort_kayip = kayip.rolling(periyot).mean()
    rs = ort_kazan / ort_kayip
    rsi = 100 - (100 / (1 + rs))
    return rsi

def ema_hesapla(df, periyot=20):
    return df['kapanis'].ewm(span=periyot, adjust=False).mean()

def sinyal_uret(exchange, symbol):
    df = mumlar_al(exchange, symbol)

    df['rsi'] = rsi_hesapla(df)
    df['ema'] = ema_hesapla(df)

    son = df.iloc[-1]
    rsi = son['rsi']
    ema = son['ema']
    fiyat = son['kapanis']

    print(f"RSI: {rsi:.2f} | EMA: {ema:.2f} | Fiyat: {fiyat:.2f}")

    if rsi < 35 and fiyat > ema:
        print("Sinyal: AL 🟢")
        return "AL"
    elif rsi > 65 and fiyat < ema:
        print("Sinyal: SAT 🔴")
        return "SAT"
    else:
        print("Sinyal: BEKLE ⚪")
        return "BEKLE"

