import ccxt
import config

def exchange_baglantisi_kur():
    exchange = ccxt.binance({
        'apiKey': config.API_KEY,
        'secret': config.API_SECRET,
    })

    if config.TESTNET:
        exchange.set_sandbox_mode(True)

    return exchange

def fiyat_al(exchange):
    ticker = exchange.fetch_ticker(config.SYMBOL)
    fiyat = ticker['last']
    print(f"Güncel {config.SYMBOL} fiyatı: ${fiyat}")
    return fiyat

def bakiye_al(exchange):
    bakiye = exchange.fetch_balance()
    usdt = bakiye['USDT']['free']
    print(f"Kullanılabilir bakiye: ${usdt}")
    return usdt
