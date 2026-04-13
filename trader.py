import config

def pozisyon_boyutu_hesapla(bakiye, fiyat):
    kullanilacak = bakiye * (config.RISK_PERCENT / 100)
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
    emir = exchange.create_market_buy_order(config.SYMBOL, miktar)
    stop = round(fiyat * (1 - config.STOP_LOSS_PERCENT / 100), 2)
    hedef = round(fiyat * (1 + config.TAKE_PROFIT_PERCENT / 100), 2)
    print(f"Stop-loss: ${stop} | Take-profit: ${hedef}")
    return {'emir': emir, 'stop': stop, 'hedef': hedef, 'giris': fiyat}

def sat(exchange, miktar, fiyat):
    print(f"SATIŞ EMRİ: {miktar} BTC @ ${fiyat}")
    emir = exchange.create_market_sell_order(config.SYMBOL, miktar)
    return emir
