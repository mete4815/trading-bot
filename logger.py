import json
from datetime import datetime

LOG_DOSYASI = "islemler.json"

def kaydet(islem_tipi, fiyat, miktar, stop=None, hedef=None):
    kayit = {
        "zaman": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "islem": islem_tipi,
        "fiyat": fiyat,
        "miktar": miktar,
        "stop_loss": stop,
        "take_profit": hedef
    }

    try:
        with open(LOG_DOSYASI, 'r') as f:
            gecmis = json.load(f)
    except:
        gecmis = []

    gecmis.append(kayit)

    with open(LOG_DOSYASI, 'w') as f:
        json.dump(gecmis, f, indent=2, ensure_ascii=False)

    print(f"[LOG] {kayit['zaman']} | {islem_tipi} | ${fiyat} | {miktar} BTC")
